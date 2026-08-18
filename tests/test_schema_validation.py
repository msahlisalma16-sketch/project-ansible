import sys
from lxml import etree
import glob

SCHEMA_FILE = "schemas/schema.xsd"
XML_DIR = "final/*.xml"

def validate_xmls():
    # Load schema
    with open(SCHEMA_FILE, "rb") as f:
        schema_root = etree.XML(f.read())
        schema = etree.XMLSchema(schema_root)

    # Validate each XML
    errors = []
    for xml_file in glob.glob(XML_DIR):
        with open(xml_file, "rb") as f:
            xml_doc = etree.XML(f.read())
        if not schema.validate(xml_doc):
            print(f" Invalid XML: {xml_file}")
            for error in schema.error_log:
                print(f"   - {error.message}")
            errors.append(xml_file)
        else:
            print(f" Valid XML: {xml_file}")

    if errors:
        print(f"\nERROR: {len(errors)} invalid XML files.")
        sys.exit(1)
    else:
        print("\nAll XML files are valid.")
        sys.exit(0)

if __name__ == "__main__":
    validate_xmls()
