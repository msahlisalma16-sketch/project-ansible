"""Centralized configuration management for XML migration and debug tools."""

import os
from pathlib import Path
from typing import Any, Dict, List

ROOT_DIR = Path(__file__).resolve().parents[1]
CONFIG_FILE = ROOT_DIR / "config.yaml"

DEFAULT_CONFIG: Dict[str, str] = {
    "master_template_path": "files/master_templates/master_config.xml",
    "v5_path": "files/master_templates/master_config.xml",
    "source_xml": "files/client_sources/client1_source.xml",
    "v1_path": "files/client_sources/client1_source.xml",
    "out_template": "templates/config_target.j2",
    "out_vars": "vars/vars.yaml",
    "out_final": "final/final_config.xml",
    "out_report": "reports/mappings/mapping_report.txt",
    "ai_review": "reports/ai_reviews/mapping_ai_review.txt",
    "summary_report": "reports/summary/management_summary.txt",
}


def load_config() -> Dict[str, Any]:
    """Load configuration from config.yaml and environment variables."""
    cfg: Dict[str, Any] = DEFAULT_CONFIG.copy()

    if CONFIG_FILE.exists():
        try:
            import yaml
            with CONFIG_FILE.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if isinstance(data, dict):
                    for k, v in data.items():
                        if v:
                            cfg[k] = v
        except Exception:
            pass

    # Environment variables take precedence if present
    env_mapping = {
        "XML_SOURCE_PATH": "source_xml",
        "XML_V1_PATH": "source_xml",
        "XML_MASTER_TEMPLATE": "master_template_path",
        "XML_V5_PATH": "master_template_path",
        "OUT_TEMPLATE": "out_template",
        "OUT_VARS": "out_vars",
        "OUT_FINAL": "out_final",
        "OUT_REPORT": "out_report",
        "AI_REVIEW": "ai_review",
        "SUMMARY_REPORT": "summary_report",
    }
    for env_var, cfg_key in env_mapping.items():
        if env_var in os.environ:
            cfg[cfg_key] = os.environ[env_var]

    return cfg


_config = load_config()

MASTER_TEMPLATE_PATH = Path(_config.get("master_template_path", _config.get("v5_path", DEFAULT_CONFIG["master_template_path"])))
V5_PATH = MASTER_TEMPLATE_PATH

SOURCE_XML_PATH = Path(_config.get("source_xml", _config.get("v1_path", DEFAULT_CONFIG["source_xml"])))
V1_PATH = SOURCE_XML_PATH

OUT_TEMPLATE = Path(_config.get("out_template", DEFAULT_CONFIG["out_template"]))
OUT_VARS = Path(_config.get("out_vars", DEFAULT_CONFIG["out_vars"]))
OUT_FINAL = Path(_config.get("out_final", DEFAULT_CONFIG["out_final"]))
OUT_REPORT = Path(_config.get("out_report", DEFAULT_CONFIG["out_report"]))
AI_REVIEW = Path(_config.get("ai_review", DEFAULT_CONFIG["ai_review"]))
SUMMARY_REPORT = Path(_config.get("summary_report", DEFAULT_CONFIG["summary_report"]))


def get_clients() -> List[Dict[str, Any]]:
    """Return list of client configurations."""
    raw_clients = _config.get("clients")
    if isinstance(raw_clients, list) and raw_clients:
        clients = []
        for idx, item in enumerate(raw_clients):
            if isinstance(item, dict):
                c_name = str(item.get("name", f"client_{idx+1}"))
                src_xml = item.get("source_xml", item.get("v1_path", SOURCE_XML_PATH))
                clients.append({
                    "name": c_name,
                    "source_xml": Path(src_xml),
                    "v1_path": Path(src_xml),
                    "out_vars": Path(item.get("out_vars", f"vars/vars_{c_name}.yaml")),
                    "out_final": Path(item.get("out_final", f"final/{c_name}_config.xml")),
                    "out_report": Path(item.get("out_report", f"reports/mappings/mapping_report_{c_name}.txt")),
                    "ai_review": Path(item.get("ai_review", f"reports/ai_reviews/mapping_ai_review_{c_name}.txt")),
                    "summary_report": Path(item.get("summary_report", f"reports/summary/management_summary_{c_name}.txt")),
                })
        if clients:
            return clients

    return [{
        "name": "default",
        "source_xml": SOURCE_XML_PATH,
        "v1_path": V1_PATH,
        "out_vars": OUT_VARS,
        "out_final": OUT_FINAL,
        "out_report": OUT_REPORT,
        "ai_review": AI_REVIEW,
        "summary_report": SUMMARY_REPORT,
    }]


def reload_config() -> Dict[str, Any]:
    """Reload configuration dynamically."""
    global _config, MASTER_TEMPLATE_PATH, V5_PATH, SOURCE_XML_PATH, V1_PATH, OUT_TEMPLATE, OUT_VARS, OUT_FINAL, OUT_REPORT, AI_REVIEW, SUMMARY_REPORT
    _config = load_config()
    MASTER_TEMPLATE_PATH = Path(_config.get("master_template_path", _config.get("v5_path", DEFAULT_CONFIG["master_template_path"])))
    V5_PATH = MASTER_TEMPLATE_PATH
    SOURCE_XML_PATH = Path(_config.get("source_xml", _config.get("v1_path", DEFAULT_CONFIG["source_xml"])))
    V1_PATH = SOURCE_XML_PATH
    OUT_TEMPLATE = Path(_config.get("out_template", DEFAULT_CONFIG["out_template"]))
    OUT_VARS = Path(_config.get("out_vars", DEFAULT_CONFIG["out_vars"]))
    OUT_FINAL = Path(_config.get("out_final", DEFAULT_CONFIG["out_final"]))
    OUT_REPORT = Path(_config.get("out_report", DEFAULT_CONFIG["out_report"]))
    AI_REVIEW = Path(_config.get("ai_review", DEFAULT_CONFIG["ai_review"]))
    SUMMARY_REPORT = Path(_config.get("summary_report", DEFAULT_CONFIG["summary_report"]))
    return _config
