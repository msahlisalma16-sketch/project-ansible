from utils import xml_migration as m
from utils import config

def main():
    source_xml_path = config.SOURCE_XML_PATH
    template_xml_path = config.MASTER_TEMPLATE_PATH

    try:
        placeholders, _ = m.extract_placeholders(template_xml_path)
        source_tree = m.parse_v1(source_xml_path)

        print("Debug match results:")
        print(f"Template placeholders count: {len(placeholders)}")
        print(f"Source XML element count: {len(source_tree)}")
        for ph in placeholders[:5]:
            print(f" - {ph['placeholder']}")
    except Exception as e:
        print("Debug match failed:", e)

if __name__ == "__main__":
    main()
