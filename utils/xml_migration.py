#!/usr/bin/env python3
"""XML migration utilities for converting v5 XML into Jinja2 template and variables."""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

try:
    import config
except ImportError:
    from utils import config

from lxml import etree

try:
    import yaml
except ImportError:
    yaml = None

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

try:
    from sentence_transformers import SentenceTransformer, util
except ImportError:
    SentenceTransformer = None  # type: ignore[assignment]
    util = None

_ai_model: Optional["SentenceTransformer"] = None


def strip_namespace(tag: Any) -> str:
    """Remove XML namespace prefix from a tag name."""
    if not isinstance(tag, str):
        return ""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def parse_xml(path: Path) -> etree._ElementTree:
    """Parse XML from disk with lenient namespace handling."""
    parser = etree.XMLParser(ns_clean=True, recover=True, resolve_entities=True)
    return etree.parse(str(path), parser)


def normalize_term(value: str) -> str:
    """Normalize a string for matching by lowercasing and separating tokens."""
    if not value:
        return ""

    s = value.replace("_", " ").replace("-", " ")
    s = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", s)
    s = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", s)
    s = re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()
    return s


def tokenize_term(value: str) -> List[str]:
    """Split a normalized string into lowercase tokens."""
    if not value:
        return []
    s = normalize_term(value)
    return [tok for tok in re.split(r"[^a-z0-9]+", s) if tok]


def get_ai_model() -> Optional[SentenceTransformer]:
    """Lazily load the sentence-transformers model if available."""
    global _ai_model
    if SentenceTransformer is None or util is None:
        return None
    if _ai_model is None:
        _ai_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _ai_model


def ai_similarity(a: str, b: str) -> float:
    """Compute similarity score between two strings using an AI model."""
    if not a or not b:
        return 0.0

    model = get_ai_model()
    if model is None:
        return 0.0

    emb_a = model.encode(a, convert_to_tensor=True)
    emb_b = model.encode(b, convert_to_tensor=True)
    return float(util.cos_sim(emb_a, emb_b))


def ai_enabled() -> bool:
    """Return True if the optional AI similarity feature is available."""
    return SentenceTransformer is not None and util is not None


def score_candidate(ph: Dict[str, Any], v: Dict[str, Any]) -> Tuple[int, str]:
    """Score a candidate match for a placeholder."""
    score = 0
    reason_parts: List[str] = []

    sig = ph["signature"]
    leaf = normalize_term(sig.get("leaf", ""))
    tag = normalize_term(sig.get("tag", ""))
    comp = normalize_term(sig.get("component", ""))
    v_comp = normalize_term(v.get("component", ""))
    v_tag = normalize_term(v.get("tag", ""))
    v_attr = normalize_term(v.get("attribute", ""))
    v_path = normalize_term(v.get("path", ""))

    if sig.get("name") and v.get("signature_name") == sig["name"]:
        score += 120
        reason_parts.append("Exact name match.")
    if sig.get("key") and v.get("signature_key") == sig["key"]:
        score += 120
        reason_parts.append("Exact key match.")
    if ph["attribute"] and v["attribute"] == ph["attribute"]:
        score += 90
        reason_parts.append("Attribute match.")

    ph_tokens = set(tokenize_term(ph["placeholder"]))
    v_tokens = set(tokenize_term(v.get("text", "")))
    token_overlap = ph_tokens & v_tokens
    if token_overlap:
        score += len(token_overlap) * 18
        reason_parts.append(f"Token overlap: {token_overlap}")

    if comp and comp == v_comp:
        score += 80
        reason_parts.append("Component match.")
    if comp and comp in v_path:
        score += 80
        reason_parts.append("Component path match.")
    if tag and tag == v_tag:
        score += 75
        reason_parts.append("Tag match.")
    if leaf and (leaf == v_attr or leaf == v_tag or leaf in v_path):
        score += 70
        reason_parts.append("Leaf match.")

    if not reason_parts:
        reason_parts.append("No strong matches.")

    return score, "; ".join(reason_parts)


def find_best_match(ph: Dict[str, Any], v1_values: List[Dict[str, Any]]) -> Tuple[Optional[Dict[str, Any]], str]:
    """Find the best matching v1 value for a placeholder."""
    candidates: List[Tuple[int, str, Dict[str, Any]]] = []
    for v in v1_values:
        score, reason = score_candidate(ph, v)
        if score > 0:
            candidates.append((score, reason, v))

    if not candidates:
        return None, "no candidates"

    candidates.sort(key=lambda item: (-item[0], item[2].get("path", "")))
    best_score, best_reason, best_value = candidates[0]
    if best_score < 75:
        return None, "Rejected: score below threshold"
    return best_value, best_reason


def extract_placeholders(v5_path: Path) -> Tuple[List[Dict[str, Any]], etree._ElementTree]:
    """Extract placeholder metadata from a v5 XML document."""
    tree = parse_xml(v5_path)
    root = tree.getroot()
    placeholders: List[Dict[str, Any]] = []

    def recurse(element: etree._Element, component: Optional[str] = None, path: str = "") -> None:
        tag = strip_namespace(element.tag)
        if tag == "component" and "name" in element.attrib:
            component = element.attrib["name"]

        current_path = f"{path}/{tag}" if path else tag
        text = element.text.strip() if element.text else ""

        if "#{" in text:
            for ph in re.findall(r"#\{([^}]+)\}", text):
                placeholders.append({
                    "placeholder": ph,
                    "component": component,
                    "tag": tag,
                    "attribute": None,
                    "location": f"{current_path}/text",
                    "signature": {
                        "component": component,
                        "tag": tag,
                        "path": current_path,
                        "leaf": ph.split(".")[-1],
                    },
                })

        for attr, val in element.attrib.items():
            if val and "#{" in val:
                for ph in re.findall(r"#\{([^}]+)\}", val):
                    placeholders.append({
                        "placeholder": ph,
                        "component": component,
                        "tag": tag,
                        "attribute": attr,
                        "location": f"{current_path}/@{attr}",
                        "signature": {
                            "component": component,
                            "tag": tag,
                            "path": current_path,
                            "leaf": ph.split(".")[-1],
                        },
                    })

        for child in element:
            recurse(child, component, current_path)

    recurse(root)
    return placeholders, tree


def convert_to_jinja2(tree: etree._ElementTree, out_path: Path) -> None:
    """Convert an XML tree to a Jinja2-compatible template."""
    xml_str = etree.tostring(tree.getroot(), encoding="unicode")
    jinja_str = re.sub(r"#\{([^}]+)\}", r"{{ \1 }}", xml_str)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(jinja_str, encoding="utf-8")


def parse_v1(v1_path: Path) -> List[Dict[str, Any]]:
    """Parse v1 XML into a flat list of searchable value dictionaries."""
    tree = parse_xml(v1_path)
    root = tree.getroot()

    def parse_element(element: etree._Element, parent_path: str = "") -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        tag = strip_namespace(element.tag)
        current_path = f"{parent_path}/{tag}" if parent_path else tag

        signature_name = element.attrib.get("name") or element.attrib.get("id")
        signature_key = element.attrib.get("key")

        for attr, val in element.attrib.items():
            results.append({
                "component": tag,
                "tag": tag,
                "signature_name": signature_name,
                "signature_key": signature_key,
                "attribute": attr,
                "text": val,
                "path": f"{current_path}/@{attr}",
            })

        if element.text and element.text.strip():
            results.append({
                "component": tag,
                "tag": tag,
                "signature_name": signature_name,
                "signature_key": signature_key,
                "attribute": None,
                "text": element.text.strip(),
                "path": f"{current_path}/text",
            })

        for child in element:
            results.extend(parse_element(child, current_path))

        return results

    return parse_element(root)


def match_placeholders(placeholders: List[Dict[str, Any]], v1_values: List[Dict[str, Any]]) -> Tuple[Dict[str, str], List[str]]:
    """Match placeholders against v1 values and return a mapping and report lines."""
    mapping: Dict[str, str] = {}
    report_lines: List[str] = []

    for ph in placeholders:
        match, reason = find_best_match(ph, v1_values)
        if match:
            report_lines.append(f"{ph['placeholder']} -> {ph['location']} => {match['text']} ({reason})")
            mapping[ph["placeholder"]] = match["text"]
        else:
            report_lines.append(f"{ph['placeholder']} -> {ph['location']} => UNMAPPED ({reason})")

    return mapping, report_lines


def write_vars_yaml(mapping: Dict[str, Any], yaml_path: Path) -> None:
    """Write a nested YAML file from placeholder mappings."""
    yaml_path.parent.mkdir(parents=True, exist_ok=True)
    nested: Dict[str, Any] = {}
    for ph, val in mapping.items():
        parts = ph.split(".")
        d = nested
        for p in parts[:-1]:
            d = d.setdefault(p, {})
        d[parts[-1]] = val

    with yaml_path.open("w", encoding="utf-8") as f:
        if yaml is not None:
            yaml.dump(nested, f, default_flow_style=False, sort_keys=False)
        else:
            for key, value in nested.items():
                f.write(f"{key}: {value}\n")


def write_report(report_lines: List[str], report_path: Path) -> None:
    """Write a simple match report to disk."""
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8") as f:
        f.write("REPORT LEGEND:\n")
        f.write("- Exact match, token overlap, component/tag/leaf match.\n\n")
        for line in report_lines:
            f.write(line + "\n")


def generate_ai_review(placeholders: List[Dict[str, Any]], v1_values: List[Dict[str, Any]], top_n: int = 3) -> List[str]:
    """Generate an optional AI similarity review for placeholder mappings."""
    lines: List[str] = []
    if not ai_enabled():
        lines.append("AI review unavailable: sentence_transformers is not installed.")
        return lines

    for ph in placeholders:
        candidates: List[Tuple[float, Dict[str, Any]]] = []
        for v in v1_values:
            sim = ai_similarity(ph["placeholder"], v.get("text", ""))
            candidates.append((sim, v))
        candidates.sort(key=lambda item: item[0], reverse=True)

        lines.append(f"Placeholder: {ph['placeholder']} ({ph['location']})")
        for sim, v in candidates[:top_n]:
            lines.append(f"  candidate: {v.get('path')} => {v.get('text')} (similarity={sim:.3f})")
        lines.append("")

    return lines


def write_ai_review(review_lines: List[str], review_path: Path) -> None:
    """Write the AI review report to disk."""
    review_path.parent.mkdir(parents=True, exist_ok=True)
    with review_path.open("w", encoding="utf-8") as f:
        f.write("AI Review Suggestions:\n")
        f.write("- These suggestions do not affect vars or final output.\n\n")
        for line in review_lines:
            f.write(line + "\n")


def render_final_config(template_path: Path, mapping: Dict[str, Any], out_final_path: Path) -> None:
    """Render the Jinja2 template with mapped variables to produce the final XML file with filled placeholders."""
    if not template_path.exists():
        return
    out_final_path.parent.mkdir(parents=True, exist_ok=True)
    template_str = template_path.read_text(encoding="utf-8")

    nested: Dict[str, Any] = {}
    for ph, val in mapping.items():
        parts = ph.split(".")
        d = nested
        for p in parts[:-1]:
            d = d.setdefault(p, {})
        d[parts[-1]] = val

    try:
        import jinja2
        template = jinja2.Template(template_str)
        rendered = template.render(**nested)
    except Exception:
        rendered = template_str
        for ph, val in mapping.items():
            rendered = rendered.replace(f"{{{{ {ph} }}}}", str(val))

    out_final_path.write_text(rendered, encoding="utf-8")


def process_client(client: Dict[str, Any], placeholders: List[Dict[str, Any]], template_path: Path) -> None:
    """Process migration for a single client against the extracted placeholders and master template."""
    c_name = client["name"]
    source_xml = Path(client.get("source_xml", client["v1_path"]))
    out_vars = Path(client["out_vars"])
    out_final = Path(client["out_final"])
    out_report = Path(client["out_report"])
    ai_review = Path(client["ai_review"])

    print(f"--- Processing Client: {c_name} (Source: {source_xml}) ---")
    source_values = parse_v1(source_xml)
    mapping, report_lines = match_placeholders(placeholders, source_values)

    write_vars_yaml(mapping, out_vars)
    write_report(report_lines, out_report)
    render_final_config(template_path, mapping, out_final)

    review_lines = generate_ai_review(placeholders, source_values)
    write_ai_review(review_lines, ai_review)

    print(f"[{c_name}] Generated: {out_vars}, {out_final}, {out_report}, {ai_review}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Robust XML migration with namespace/CDATA support.")
    parser.add_argument("source_xml", nargs="?", default=None, help="Path to client source XML file")
    parser.add_argument("master_template_path", nargs="?", default=None, help="Path to master template XML file")
    parser.add_argument("--out-template", default=str(config.OUT_TEMPLATE))
    parser.add_argument("--out-vars", default=None)
    parser.add_argument("--out-final", default=None, help="Path to rendered final output XML with filled placeholders")
    parser.add_argument("--out-report", default=None)
    parser.add_argument(
        "--ai-review",
        default=None,
        help="Write a separate AI review report for candidate suggestions.",
    )
    args = parser.parse_args()

    # Master template path
    master_template_path = Path(args.master_template_path) if args.master_template_path else config.MASTER_TEMPLATE_PATH
    out_template = Path(args.out_template)

    print(f"Extracting master placeholders from {master_template_path}...")
    placeholders, master_tree = extract_placeholders(master_template_path)
    convert_to_jinja2(master_tree, out_template)
    print(f"Master template created at {out_template}")

    # If explicit CLI positional args were passed for a single file migration
    if args.source_xml or args.out_vars or args.out_final:
        single_client = {
            "name": "custom",
            "source_xml": Path(args.source_xml) if args.source_xml else config.SOURCE_XML_PATH,
            "v1_path": Path(args.source_xml) if args.source_xml else config.SOURCE_XML_PATH,
            "out_vars": Path(args.out_vars) if args.out_vars else config.OUT_VARS,
            "out_final": Path(args.out_final) if args.out_final else config.OUT_FINAL,
            "out_report": Path(args.out_report) if args.out_report else config.OUT_REPORT,
            "ai_review": Path(args.ai_review) if args.ai_review else config.AI_REVIEW,
        }
        process_client(single_client, placeholders, out_template)
    else:
        # Multi-client processing mode
        clients = config.get_clients()
        print(f"Processing {len(clients)} client(s) defined in config...")
        for client in clients:
            process_client(client, placeholders, out_template)


if __name__ == "__main__":
    main()

