import sys
sys.path.append('./utils')
import xml_migration as m
import config

def main():
    v1_path = config.V1_PATH
    v5_path = config.V5_PATH

    try:
        # Parse both XMLs
        v1_tree = m.parse_v1(v1_path)
        placeholders, _ = m.extract_placeholders(v5_path)

        print("Debug parser results:")
        print(f"v1.xml parsed with {len(v1_tree)} elements")
        print(f"v5.xml contains {len(placeholders)} placeholders")
        # Optionally print the first few placeholders
        for ph in placeholders[:5]:
            print(f" - {ph['placeholder']}")
    except Exception as e:
        print("Debug parser failed:", e)

if __name__ == "__main__":
    main()
