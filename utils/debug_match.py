import sys
sys.path.append('./utils')
import xml_migration as m
import config

def main():
    v1_path = config.V1_PATH
    v5_path = config.V5_PATH

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
