import unittest
import xml_migration   # your migration module

class TestUnmappedPlaceholders(unittest.TestCase):

    def test_unmapped_threshold(self):
        # Load placeholders from v5 template
        placeholders, _ = xml_migration.extract_placeholders(
            "files/master_templates/master_config.xml"
        )
        # Parse v1 source XML
        v1_values = xml_migration.parse_v1(
            "files/client_sources/client1_source.xml"
        )
        # Run matching
        mapping, _ = xml_migration.match_placeholders(placeholders, v1_values)

        # Collect unmapped placeholders
        unmapped = [ph for ph, val in mapping.items()
                    if val.strip() == "" or val.startswith("UNMAPPED")]

        # Debug visibility: log them
        print("\n--- Unmapped placeholders ---")
        for ph in unmapped:
            print(f"UNMAPPED: {ph}")
        print(f"Total unmapped: {len(unmapped)}")

        # Threshold alert: fail if too many
        self.assertLessEqual(
            len(unmapped), 5,
            f"Too many unmapped placeholders ({len(unmapped)}): {unmapped}"
        )

if __name__ == "__main__":
    unittest.main()
