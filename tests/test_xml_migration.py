import os
import tempfile
import unittest
from pathlib import Path

from utils import xml_migration as m
from utils import config


class TestXmlMigration(unittest.TestCase):
    def test_extract_placeholders(self):
        master_template_path = Path("files/master_templates/master_config.xml")
        placeholders, tree = m.extract_placeholders(master_template_path)

        self.assertIsInstance(placeholders, list)
        self.assertGreater(len(placeholders), 0)
        self.assertIsNotNone(tree)

        placeholder = placeholders[0]
        self.assertIn("placeholder", placeholder)
        self.assertIn("location", placeholder)
        self.assertIn("signature", placeholder)
        self.assertIn("leaf", placeholder["signature"])

    def test_parse_source_xml(self):
        source_xml_path = Path("files/client_sources/client2_source.xml")
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
        self.assertIsNotNone(config.SOURCE_XML_PATH)
        self.assertIsNotNone(config.MASTER_TEMPLATE_PATH)

        os.environ["XML_SOURCE_PATH"] = "files/custom_source.xml"
        config.reload_config()
        self.assertEqual(config.SOURCE_XML_PATH, Path("files/custom_source.xml"))

        del os.environ["XML_SOURCE_PATH"]
        config.reload_config()


if __name__ == "__main__":
    unittest.main()
