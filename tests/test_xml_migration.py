import os
import tempfile
import unittest
from pathlib import Path

from utils import xml_migration as m
from utils import config


class TestXmlMigration(unittest.TestCase):
    def test_extract_placeholders(self):
        template_xml_path = config.MASTER_TEMPLATE_PATH
        placeholders, tree = m.extract_placeholders(template_xml_path)

        self.assertIsInstance(placeholders, list)
        self.assertGreater(len(placeholders), 0)
        self.assertIsNotNone(tree)

    def test_parse_all_clients(self):
        clients = config.get_clients()
        for client in clients:
            source_xml_path = client["source_xml"]
            if not Path(source_xml_path).exists():
                self.skipTest(f"{source_xml_path} not found")
            values = m.parse_v1(source_xml_path)
            self.assertIsInstance(values, list)
            self.assertGreater(len(values), 0)

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

    def test_write_summary_report(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            summary_path = Path(temp_dir) / "summary.txt"
            m.write_summary_report(
                c_name="client1",
                source_xml=Path("files/client_sources/client1_source.xml"),
                master_template_path=Path("files/master_templates/master_config.xml"),
                placeholders=[{"placeholder": "system.hostname"}],
                mapping={"system.hostname": "example"},
                out_vars=Path("vars/vars_client1.yaml"),
                out_final=Path("final/client1_config.xml"),
                out_report=Path("reports/mappings/mapping_report_client1.txt"),
                summary_path=summary_path,
            )

            self.assertTrue(summary_path.exists())
            contents = summary_path.read_text(encoding="utf-8")
            self.assertIn("MANAGEMENT SUMMARY", contents)
            self.assertIn("Placeholders found: 1", contents)
            self.assertIn("Match rate: 100.0%", contents)

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
