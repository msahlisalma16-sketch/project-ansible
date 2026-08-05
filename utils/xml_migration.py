#!/usr/bin/env python3
import os, re
from lxml import etree
try:
    import yaml
except ImportError:
    yaml = None

try:
    from sentence_transformers import SentenceTransformer, util
except ImportError:
    SentenceTransformer = None
    util = None

_ai_model = None

# --- Helpers ---
def strip_namespace(tag):
    if not isinstance(tag, str):
        return ""
    if '}' in tag:
        return tag.split('}', 1)[1]
    return tag

def parse_xml(path: str):
    parser = etree.XMLParser(ns_clean=True, recover=True, resolve_entities=True)
    return etree.parse(path, parser)

def normalize_term(value: str) -> str:
    if not value:
        return ""
    s = value.replace("_", " ").replace("-", " ")
    s = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", s)
    s = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", s)
    s = re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()
    return s

def tokenize_term(value: str):
    if not value:
        return []
    s = normalize_term(value)
    return [tok for tok in re.split(r"[^a-z0-9]+", s) if tok]

# --- AI similarity ---
def get_ai_model():
    global _ai_model
    if SentenceTransformer is None or util is None:
        return None
    if _ai_model is None:
        _ai_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _ai_model


def ai_similarity(a, b):
    if not a or not b:
        return 0.0
    model = get_ai_model()
    if model is None:
        return 0.0
    emb_a = model.encode(a, convert_to_tensor=True)
    emb_b = model.encode(b, convert_to_tensor=True)
    return float(util.cos_sim(emb_a, emb_b))


def ai_enabled():
    return SentenceTransformer is not None and util is not None

# --- Scoring ---
def score_candidate(ph, v):
    score = 0
    reason_parts = []

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
    if tag and tag == v_tag:
        score += 75
        reason_parts.append("Tag match.")
    if leaf and (leaf == v_attr or leaf == v_tag or leaf in v_path):
        score += 70
        reason_parts.append("Leaf match.")

    if not reason_parts:
        reason_parts.append("No strong matches.")

    return score, "; ".join(reason_parts)

def find_best_match(ph, v1_values):
    candidates = []
    for v in v1_values:
        score, reason = score_candidate(ph, v)
        if score > 0:
            candidates.append((score, reason, v))
    if not candidates:
        return None, "no candidates"
    candidates.sort(key=lambda item: (-item[0], item[2]["path"]))
    best_score, best_reason, best_value = candidates[0]
    if best_score < 75:
        return None, "Rejected: score below threshold"
    return best_value, best_reason

# --- XML parsing ---
def extract_placeholders(v5_path):
    tree = parse_xml(v5_path)
    root = tree.getroot()
    placeholders = []

    def recurse(element, component=None, path=""):
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
                    "signature": {"component": component, "tag": tag, "path": current_path, "leaf": ph.split(".")[-1]},
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
                        "signature": {"component": component, "tag": tag, "path": current_path, "leaf": ph.split(".")[-1]},
                    })

        for child in element:
            recurse(child, component, current_path)

    recurse(root)
    return placeholders, tree

def convert_to_jinja2(tree, out_path):
    xml_str = etree.tostring(tree.getroot(), encoding="unicode")
    jinja_str = re.sub(r"#\{([^}]+)\}", r"{{ \1 }}", xml_str)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(jinja_str)

def parse_v1(v1_path):
    tree = parse_xml(v1_path)
    root = tree.getroot()

    def parse_element(element, parent_path=""):
        results = []
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

# --- Matching ---
def match_placeholders(placeholders, v1_values):
    mapping = {}
    report_lines = []
    for ph in placeholders:
        match, reason = find_best_match(ph, v1_values)
        if match:
            report_lines.append(f"{ph['placeholder']} -> {ph['location']} => {match['text']} ({reason})")
            mapping[ph["placeholder"]] = match["text"]
        else:
            report_lines.append(f"{ph['placeholder']} -> {ph['location']} => UNMAPPED ({reason})")
    return mapping, report_lines

# --- Writers ---
def write_vars_yaml(mapping, yaml_path):
    nested = {}
    for ph, val in mapping.items():
        parts = ph.split(".")
        d = nested
        for p in parts[:-1]:
            d = d.setdefault(p, {})
        d[parts[-1]] = val
    with open(yaml_path, "w", encoding="utf-8") as f:
        if yaml is not None:
            yaml.dump(nested, f, default_flow_style=False, sort_keys=False)
        else:
            for k, v in nested.items():
                f.write(f"{k}: {v}\n")

def write_report(report_lines, report_path):
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("REPORT LEGEND:\n")
        f.write("- Exact match, token overlap, component/tag/leaf match.\n\n")
        for line in report_lines:
            f.write(line + "\n")


def generate_ai_review(placeholders, v1_values, top_n=3):
    lines = []
    if not ai_enabled():
        lines.append("AI review unavailable: sentence_transformers is not installed.")
        return lines

    for ph in placeholders:
        candidates = []
        for v in v1_values:
            sim = ai_similarity(ph["placeholder"], v.get("text", ""))
            candidates.append((sim, v))
        candidates.sort(key=lambda item: item[0], reverse=True)

        lines.append(f"Placeholder: {ph['placeholder']} ({ph['location']})")
        for sim, v in candidates[:top_n]:
            lines.append(
                f"  candidate: {v.get('path')} => {v.get('text')} (similarity={sim:.3f})"
            )
        lines.append("")
    return lines


def write_ai_review(review_lines, review_path):
    with open(review_path, "w", encoding="utf-8") as f:
        f.write("AI Review Suggestions:\n")
        f.write("- These suggestions do not affect vars or final output.\n\n")
        for line in review_lines:
            f.write(line + "\n")

# --- Main ---
def main():
    import argparse
    parser = argparse.ArgumentParser(description="Robust XML migration with namespace/CDATA support.")
    parser.add_argument("v1_path", nargs="?", default="v1.xml")
    parser.add_argument("v5_path", nargs="?", default="v5.xml")
    parser.add_argument("--out-template", default="templates/config_target.j2")
    parser.add_argument("--out-vars", default="/home/vboxuser/ansible-project/vars.yaml")
    parser.add_argument("--out-report", default="mapping_report.txt")
    parser.add_argument("--ai-review", default="mapping_ai_review.txt",
                        help="Write a separate AI review report for candidate suggestions.")
    args = parser.parse_args()

    # Debug line to confirm where vars.yaml will be written
    print(f"Writing vars.yaml to {args.out_vars}")

    placeholders, v5_tree = extract_placeholders(args.v5_path)
    convert_to_jinja2(v5_tree, args.out_template)

    v1_values = parse_v1(args.v1_path)
    mapping, report_lines = match_placeholders(placeholders, v1_values)

    write_vars_yaml(mapping, args.out_vars)
    write_report(report_lines, args.out_report)

    review_lines = generate_ai_review(placeholders, v1_values)
    write_ai_review(review_lines, args.ai_review)

    print(f"Generated {args.out_template}, {args.out_vars}, {args.out_report}, {args.ai_review}")


if __name__ == "__main__":
    main()

