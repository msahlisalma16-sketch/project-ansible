import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "utils"))

import xml_migration as m
import config


class TestXmlMigration(unittest.TestCase):
    def test_extract_placeholders(self):
        master_template_path = ROOT / "files" / "master_templates" / "master_config.xml"
        placeholders, tree = m.extract_placeholders(master_template_path)

        self.assertIsInstance(placeholders, list)
        self.assertGreater(len(placeholders), 0)
        self.assertIsNotNone(tree)

        placeholder = placeholders[0]
        self.assertIn("placeholder", placeholder)
        self.assertIn("location", placeholder)
        self.assertIn("signature", placeholder)
        self.assertIn("leaf", placeholder["signature"])

    def test_parse_v1(self):
        source_xml_path = ROOT / "files" / "client_sources" / "client2_source.xml"
        values = m.parse_v1(source_xml_path)

        self.assertIsInstance(values, list)
        self.assertGreater(len(values), 0)
        self.assertIn("text", values[0])
        self.assertIn("path", values[0])

    def test_write_vars_yaml(self):
        mapping = {
            "system.hostname": "example",
            "system.port": "443",
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            yaml_path = Path(temp_dir) / "vars.yaml"
            m.write_vars_yaml(mapping, yaml_path)

            self.assertTrue(yaml_path.exists())
            contents = yaml_path.read_text(encoding="utf-8")
            self.assertIn("system:", contents)
            self.assertIn("hostname", contents)
            self.assertIn("port", contents)

    def test_config_defaults_and_env_override(self):
        self.assertIsNotNone(config.V1_PATH)
        self.assertIsNotNone(config.V5_PATH)

        os.environ["XML_V1_PATH"] = "files/custom_v1.xml"
        config.reload_config()
        self.assertEqual(config.V1_PATH, Path("files/custom_v1.xml"))

        del os.environ["XML_V1_PATH"]
        config.reload_config()


if __name__ == "__main__":
    unittest.main()
