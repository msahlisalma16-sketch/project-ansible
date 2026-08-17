import sys
sys.path.append('./utils')   # add utils folder to Python path
from utils import xml_migration as m
import config

def main():
    v1_path = config.V1_PATH
    v5_path = config.V5_PATH

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
