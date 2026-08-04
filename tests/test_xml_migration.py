import sys
import unittest

sys.path.append('./utils')   # add utils folder to Python path
import xml_migration as m

class TestXmlMigration(unittest.TestCase):
    def test_extract_placeholders(self):
        v5_path = 'files/v5.xml'
        placeholders, _ = m.extract_placeholders(v5_path)
        # Correct expectation: list of dicts, not a single dict
        self.assertIsInstance(placeholders, list)
        self.assertGreater(len(placeholders), 0)

    def test_parse_v1(self):
        v1_path = 'files/v2.xml'
        v1_tree = m.parse_v1(v1_path)
        self.assertIsNotNone(v1_tree)

if __name__ == '__main__':
    unittest.main()
