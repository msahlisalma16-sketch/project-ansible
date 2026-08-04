import sys
sys.path.append('./utils')
import xml_migration as m

def main():
    v1_path = 'files/v2.xml'
    v5_path = 'files/v5.xml'

    try:
        placeholders, _ = m.extract_placeholders(v5_path)
        v1_tree = m.parse_v1(v1_path)

        print("Debug match results:")
        print(f"Placeholders: {placeholders}")
        print(f"v1 tree size: {len(v1_tree)}")
    except Exception as e:
        print("Debug match failed:", e)

if __name__ == "__main__":
    main()
