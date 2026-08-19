from utils import config
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from utils import xml_migration as m

def main():
    source_xml_path = config.SOURCE_XML_PATH
    template_xml_path = config.MASTER_TEMPLATE_PATH

    try:
        placeholders, _ = m.extract_placeholders(template_xml_path)
        source_tree = m.parse_v1(source_xml_path)

        print("Score probe successful.")
        print(f"Template XML contains {len(placeholders)} placeholders")
        print(f"Source XML parsed with {len(source_tree)} elements")
    except Exception as e:
        print("Score probe failed:", e)

if __name__ == "__main__":
    main()
