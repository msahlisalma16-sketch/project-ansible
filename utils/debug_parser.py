from utils import xml_migration as m
from utils import config

def main():
    source_xml_path = config.SOURCE_XML_PATH
    template_xml_path = config.MASTER_TEMPLATE_PATH

    try:
        # Parse both XMLs
        source_tree = m.parse_v1(source_xml_path)
        placeholders, _ = m.extract_placeholders(template_xml_path)

        print("Debug parser results:")
        print(f"Source XML parsed with {len(source_tree)} elements")
        print(f"Template XML contains {len(placeholders)} placeholders")
        # Optionally print the first few placeholders
        for ph in placeholders[:5]:
            print(f" - {ph['placeholder']}")
    except Exception as e:
        print("Debug parser failed:", e)

if __name__ == "__main__":
    main()
