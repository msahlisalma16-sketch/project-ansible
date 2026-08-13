#!/usr/bin/env python3
from html import parser
import os
import re
import xml.etree.ElementTree as ET
try:
    import yaml
except ImportError:
    yaml = None

GENERIC_TAGS = {
    "enterpriseconfig",
    "enterpriseconfiguration",
    "root",
    "config",
    "parameters",
    "folders",
    "folder",
    "dictionary",
    "entry",
    "add",
    "gateway",
    "storage",
    "connection",
    "queues",
    "queue",
    "topics",
    "topic",
    "logging",
    "resource",
    "template",
    "templates",
    "api",
    "file",
    "files",
    "path",
    "url",
    "health",
    "ssl",
    "cert",
    "key",
    "retry",
    "auth",
    "remote",
    "archive",
    "temp",
    "ftp",
    "broker",
    "user",
    "password",
    "host",
    "port",
    "level",
    "value",
    "policy",
    "pattern",
    "name",
    "id",
    "main",
    "event",
    "audit",
    "base",
    "scripts",
    "logs",
    "reports",
    "cache",
    "local",
    "connectionstring",
}


def is_structural_tag(tag):
    normalized = normalize_term(tag)
    if not normalized:
        return True
    if normalized in GENERIC_TAGS:
        return True
    tokens = tokenize_term(tag)
    if len(tokens) <= 1 and normalized not in {
        "messaging",
        "logging",
        "resource",
        "template",
        "api",
        "filestorage",
        "connectionstrings",
        "apigateway",
        "messagingservice",
        "loggingservice",
        "resourcefolders",
        "templates",
        "filestorage",
    }:
        return True
    return False


def infer_component(ancestors):
    for tag in reversed(ancestors):
        if is_structural_tag(tag):
            continue
        return tag
    return None

def extract_placeholders(v5_path):
    tree = ET.parse(v5_path)
    root = tree.getroot()
    placeholders = []

    def recurse(element, component=None, path=""):
        tag = element.tag
        if tag == "component" and "name" in element.attrib:
            component = element.attrib["name"]

        current_path = f"{path}/{tag}" if path else tag
        text = element.text.strip() if element.text else ""

        if "#{" in text:
            for ph in re.findall(r"#\{([^}]+)\}", text):
                signature = {
                    "component": component,
                    "tag": tag,
                    "name": element.attrib.get("name"),
                    "key": element.attrib.get("key"),
                    "path": current_path,
                    "leaf": ph.split(".")[-1],
                }
                placeholders.append({
                    "placeholder": ph,
                    "component": component,
                    "tag": tag,
                    "attribute": None,
                    "location": f"{current_path}/text",
                    "signature": signature,
                    "tokens": normalize_placeholder_tokens(ph, signature),
                })

        for attr, val in element.attrib.items():
            if val and "#{" in val:
                for ph in re.findall(r"#\{([^}]+)\}", val):
                    signature = {
                        "component": component,
                        "tag": tag,
                        "name": element.attrib.get("name"),
                        "key": element.attrib.get("key"),
                        "path": current_path,
                        "leaf": ph.split(".")[-1],
                    }
                    placeholders.append({
                        "placeholder": ph,
                        "component": component,
                        "tag": tag,
                        "attribute": attr,
                        "location": f"{current_path}/@{attr}",
                        "signature": signature,
                        "tokens": normalize_placeholder_tokens(ph, signature),
                    })

        for child in element:
            recurse(child, component, current_path)

    recurse(root)
    return placeholders, tree

def convert_to_jinja2(tree, out_path):
    xml_str = ET.tostring(tree.getroot(), encoding="unicode")
    jinja_str = re.sub(r"#\{([^}]+)\}", r"{{ \1 }}", xml_str)
    out_dir = os.path.dirname(out_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(jinja_str)

def parse_connection_string(name, conn_str):
    values = []
    for part in conn_str.split(";"):
        if "=" in part:
            k, v = part.split("=", 1)
            values.append({
                "component": "connectionStrings",
                "tag": "add",
                "signature_name": name,
                "signature_key": None,
                "attribute": k.strip().lower(),
                "text": v.strip(),
                "path": f"connectionStrings/add[@name={name}]/@{k.strip().lower()}",
            })
    return values


def parse_v1(v1_path):
    tree = ET.parse(v1_path)
    root = tree.getroot()
    values = []
    element_contexts = {}

    def find_component(ancestors):
        return infer_component(ancestors)

    def recurse(element, ancestors):
        tag = element.tag
        component = find_component(ancestors + [tag]) or find_component(ancestors) or tag
        path = "/".join(ancestors + [tag])
        text = element.text.strip() if element.text and element.text.strip() else None

        signature_name = element.attrib.get("name") or element.attrib.get("id")
        signature_key = element.attrib.get("key")

        element_contexts.setdefault(path, {
            "attrs": {},
            "text": None,
            "tag": tag,
            "component": component,
            "signature_name": signature_name,
            "signature_key": signature_key,
            "path": path,
        })

        if text is not None:
            element_contexts[path]["text"] = text
            values.append({
                "component": component,
                "tag": tag,
                "signature_name": signature_name,
                "signature_key": signature_key,
                "attribute": None,
                "text": text,
                "path": f"{path}/text",
            })

        for attr, val in element.attrib.items():
            element_contexts[path]["attrs"][attr] = val
            values.append({
                "component": component,
                "tag": tag,
                "signature_name": signature_name,
                "signature_key": signature_key,
                "attribute": attr,
                "text": val,
                "path": f"{path}/@{attr}",
            })

        if tag == "add" and "connectionString" in element.attrib:
            values.extend(parse_connection_string(signature_name, element.attrib["connectionString"]))

        for child in element:
            recurse(child, ancestors + [tag])

    recurse(root, [])

    for value in values:
        element_path = value["path"].rsplit("/", 1)[0]
        parent_context = element_contexts.get(element_path, {})
        value["parent_attrs"] = parent_context.get("attrs", {})
        value["tokens"] = build_candidate_tokens(value)

    return values

def normalize_term(value: str) -> str:
    if not value:
        return ""
    s = value.replace("_", " ").replace("-", " ")
    s = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", s)
    s = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", s)
    s = re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()
    return s


def tokenize_term(value: str) -> list[str]:
    if not value:
        return []
    s = normalize_term(value)
    return [tok for tok in re.split(r"[^a-z0-9]+", s) if tok]


def build_candidate_tokens(value):
    tokens = []
    for source in (value.get("component"), value.get("tag"), value.get("attribute"), value.get("signature_name"), value.get("signature_key"), value.get("path"), value.get("text")):
        if source:
            tokens.extend(tokenize_term(source))
    for attr_value in value.get("parent_attrs", {}).values():
        tokens.extend(tokenize_term(attr_value))
    return set(tokens)


def normalize_placeholder_tokens(placeholder, signature):
    tokens = tokenize_term(placeholder)
    for field in (signature.get("component"), signature.get("tag"), signature.get("name"), signature.get("key"), signature.get("path")):
        if field:
            tokens.extend(tokenize_term(field))
    return set(tokens)


def same_component_group(a, b):
    a_norm = normalize_term(a)
    b_norm = normalize_term(b)
    if not a_norm or not b_norm:
        return False
    if a_norm == b_norm:
        return True

    a_tokens = tokenize_term(a_norm)
    b_tokens = tokenize_term(b_norm)
    if not a_tokens or not b_tokens:
        return False

    if set(a_tokens) & set(b_tokens):
        return True

    for a_tok in a_tokens:
        for b_tok in b_tokens:
            if a_tok.startswith(b_tok) or b_tok.startswith(a_tok):
                return True
    return False


def score_candidate(ph, v):
    score = 0
    sig = ph["signature"]
    leaf = normalize_term(sig.get("leaf", ""))
    tag = normalize_term(sig.get("tag", ""))
    comp = normalize_term(sig.get("component", ""))
    v_comp = normalize_term(v.get("component", ""))
    v_tag = normalize_term(v.get("tag", ""))
    v_attr = normalize_term(v.get("attribute", ""))
    v_path = normalize_term(v.get("path", ""))

    if sig["name"] and v.get("signature_name") == sig["name"]:
        score += 120
    if sig["key"] and v.get("signature_key") == sig["key"]:
        score += 120
    if ph["attribute"] and v["attribute"] == ph["attribute"]:
        score += 90
    if ph["attribute"] and leaf and v.get("attribute") and normalize_term(v["attribute"]) == leaf:
        score += 180

    ph_tokens = ph.get("tokens", set())
    v_tokens = v.get("tokens", set())
    token_overlap = ph_tokens & v_tokens
    if token_overlap:
        score += len(token_overlap) * 18

    component_match = False
    if not sig["component"]:
        component_match = True
    elif v_comp == comp:
        component_match = True
    elif same_component_group(comp, v_comp):
        component_match = True
    elif ph_tokens and v_tokens and ph_tokens & v_tokens:
        component_match = True

    if not component_match:
        return 0

    if v_comp and same_component_group(comp, v_comp):
        score += 80
    elif comp:
        score += 70

    if sig["tag"] and (v["tag"] == sig["tag"] or v_tag == tag):
        score += 75
    if leaf and v_attr == leaf:
        score += 70
    if leaf and v_tag == leaf:
        score += 60
    if leaf and leaf in v_attr and v_attr:
        score += 35
    if leaf and leaf in v_tag and v_tag:
        score += 30
    if leaf and leaf in v_path:
        score += 25
    if leaf and leaf in ph_tokens and leaf in v_tokens:
        score += 25
    if leaf and v.get("text") is not None and leaf in normalize_term(v["text"]):
        score += 40

    if ph["attribute"] is None and v["attribute"] is None and v.get("parent_attrs"):
        parent_tokens = set()
        for attr_value in v["parent_attrs"].values():
            parent_tokens.update(tokenize_term(attr_value))
        if parent_tokens and ph_tokens & parent_tokens:
            score += 120

    if ph["attribute"] is None and v["text"] is not None:
        if leaf and (leaf == v_attr or leaf == v_tag or leaf in v_path):
            score += 55
        elif tag and tag == v_tag:
            score += 45
        elif tag and tag in v_path:
            score += 30
        elif ph_tokens and v_tokens and ph_tokens & v_tokens:
            score += 25

    return score


def find_best_match(ph, v1_values):
    exact_matches = []
    candidates = []
    for v in v1_values:
        score = score_candidate(ph, v)
        if score <= 0:
            continue

        exact_name = bool(ph["signature"].get("name") and v.get("signature_name") == ph["signature"]["name"])
        exact_key = bool(ph["signature"].get("key") and v.get("signature_key") == ph["signature"]["key"])
        exact_attr = bool(ph["attribute"] and v.get("attribute") == ph["attribute"])
        exact_tag = bool(ph["signature"].get("tag") and v.get("tag") == ph["signature"]["tag"])
        exact_component = bool(ph["signature"].get("component") and normalize_term(ph["signature"]["component"]) == normalize_term(v.get("component", "")))

        if exact_name or exact_key or exact_attr or exact_tag or exact_component:
            exact_matches.append((score, exact_name, exact_key, exact_attr, exact_tag, exact_component, v))
        else:
            candidates.append((score, v))

    if exact_matches:
        exact_matches.sort(key=lambda item: (-item[0], -int(item[1]), -int(item[2]), -int(item[3]), -int(item[4]), -int(item[5]), item[6]["path"]))
        return exact_matches[0][6]

    if not candidates:
        return None
    candidates.sort(key=lambda item: (-item[0], item[1]["path"]))
    return candidates[0][1]


def sig_leaf(ph):
    return ph["signature"].get("leaf", "").lower()


def match_placeholders(placeholders, v1_values):
    mapping = {}
    report_lines = []
    for ph in placeholders:
        matched = find_best_match(ph, v1_values)

        if matched:
            value = matched["text"]
            report_lines.append(
                f"{ph['placeholder']} -> {ph['location']} => {value} (matched {matched['path']})"
            )
        else:
            value = f"UNMAPPED({ph['placeholder']})"
            report_lines.append(f"{ph['placeholder']} -> {ph['location']} => {value}")
        mapping[ph["placeholder"]] = value
    return mapping, report_lines

def _format_yaml_value(value):
    if value is None:
        return "null"
    s = str(value)
    if s == "":
        return "''"
    if any(ch in s for ch in ':#{}[],&*?`\'"<>|%@\n'):
        return repr(s)
    return s


def _dump_yaml(data, indent=0):
    lines = []
    for key, value in data.items():
        prefix = ' ' * indent
        if isinstance(value, dict):
            lines.append(f"{prefix}{key}:")
            lines.extend(_dump_yaml(value, indent + 2))
        else:
            lines.append(f"{prefix}{key}: {_format_yaml_value(value)}")
    return lines


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
            f.write("\n".join(_dump_yaml(nested)))


def write_report(report_lines, report_path):
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

def main():
    import argparse
    try:
        import config
    except ImportError:
        from utils import config

    parser = argparse.ArgumentParser(description="Migrate v5 XML placeholders to Jinja2 and vars YAML.")
    parser.add_argument("v1_path", nargs="?", default=str(config.V1_PATH), help="Path to the source v1 XML file")
    parser.add_argument("v5_path", nargs="?", default=str(config.V5_PATH), help="Path to the target v5 XML file")
    parser.add_argument("--out-template", default=str(config.OUT_TEMPLATE), help="Output Jinja2 template path")
    parser.add_argument("--out-vars", default=str(config.OUT_VARS), help="Output YAML vars path")
    parser.add_argument("--out-report", default=str(config.OUT_REPORT), help="Output mapping report path")
    args = parser.parse_args()

    placeholders, v5_tree = extract_placeholders(args.v5_path)
    convert_to_jinja2(v5_tree, args.out_template)

    v1_values = parse_v1(args.v1_path)
    mapping, report_lines = match_placeholders(placeholders, v1_values)

    write_vars_yaml(mapping, args.out_vars)
    write_report(report_lines, args.out_report)

    print(f"Generated {args.out_template}, {args.out_vars}, {args.out_report}")

if __name__ == "__main__":
    main()
