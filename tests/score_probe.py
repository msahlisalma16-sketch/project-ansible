import sys
sys.path.append('./utils')   # add utils folder to Python path
import xml_migration as m

def main():
    v1_path = 'files/v2.xml'
    v5_path = 'files/v5.xml'

    try:
        placeholders, _ = m.extract_placeholders(v5_path)
        v1_tree = m.parse_v1(v1_path)

        print("Score probe successful.")
        print(f"Found {len(placeholders)} placeholders in v5.xml")
        print(f"Parsed v1.xml with {len(v1_tree)} elements")
    except Exception as e:
        print("Score probe failed:", e)

if __name__ == "__main__":
    main()
