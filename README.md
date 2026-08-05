             # Ansible XML Migration Project

## Overview
This project automates XML migration and rendering using Ansible and a Python-based XML migration engine. The workflow:

1. Create local directories.
2. Fetch `v5.xml` from a Windows host if available.
3. Run the XML migration engine locally.
4. Generate a Jinja2 XML template and YAML values file.
5. Render the final XML.
6. Optionally copy the completed XML back to Windows.
7. Run tests and save debug logs.

## Repository Structure

- `playbook.yaml`
  - Main Ansible playbook orchestrating the whole process.
  - Handles local setup, migration execution, template rendering, Windows file transfer, and tests/debug.

- `inventory.ini`
  - Defines the `windows` host group and WinRM connection settings.

- `ping.yaml`
  - Simple Ansible playbook for testing Windows WinRM connectivity.

- `files/`
  - Holds source XML data.
  - Expected files include `v1.xml`, `v2.xml`, and `v5.xml`.

- `templates/`
  - Stores generated Jinja2 XML templates.
  - `templates/config.xml.j2` is the migrated template used for rendering.

- `final/`
  - Contains final rendered output.
  - `final/final_config.xml` is the completed XML produced by the playbook.

- `debug/`
  - Saves debug logs from test and diagnostics steps.

- `tests/`
  - Contains automated tests for the migration utilities.
  - `test_xml_migration.py` verifies placeholder extraction and V1 XML parsing.

- `utils/`
  - Python helper scripts for XML migration and debugging.
  - `xml_migration.py` is the core migration engine.
  - `xml_migration_v0.py` is an older variant.
  - `debug_match.py` and `debug_parser.py` are small diagnostic helpers.

## Core Workflow in `playbook.yaml`

### Prepare local directories
Ensures `files`, `templates`, `final`, and `debug` exist on the controller.

### Fetch `v5.xml` from Windows
Uses `ansible.builtin.fetch` to copy `v5.xml` from the Windows inventory host to `files/v5.xml`.
If the `windows` host group is missing, this step is skipped.

### Run migration locally
Executes `utils/xml_migration.py` on localhost.
The script receives:
- `v1.xml` input file
- `v5.xml` target file with placeholders
- `--out-template` path for generated Jinja2 template
- `--out-vars` path for generated YAML variable file
- `--out-report` path for migration report

It then validates that `vars.yaml` is generated successfully.

### Render final filled XML
Loads `vars.yaml` with Ansible `include_vars` and renders `templates/config.xml.j2` to `final/final_config.xml`.

### Copy final XML to Windows
If the Windows host exists, the final XML is copied back using `ansible.windows.win_copy`.

### Run tests and debug scripts
Runs the following scripts locally and saves their outputs to `debug/`:
- `tests/score_probe.py`
- `tests/test_xml_migration.py`
- `utils/debug_match.py`
- `utils/debug_parser.py`

## `utils/xml_migration.py` — Core migration engine

### What it does
- Parses source XML files with `lxml`.
- Extracts placeholder expressions from `v5.xml` like `#{foo.bar}`.
- Converts `v5.xml` to a Jinja2 template by replacing placeholders with `{{ foo.bar }}`.
- Parses `v1.xml` to extract candidate text and attribute values.
- Matches placeholders to source values using a combined scoring model.
- Writes the results to `vars.yaml` and a human-readable `mapping_report.txt`.

### Key parts
- `extract_placeholders(v5_path)`
  - Walks `v5.xml` recursively.
  - Finds placeholder patterns in text and attributes.
  - Records placeholder metadata including component, tag, attribute, and path.

- `convert_to_jinja2(tree, out_path)`
  - Converts `#{...}` placeholders to Jinja2 `{{ ... }}` syntax.

- `parse_v1(v1_path)`
  - Walks `v1.xml` recursively.
  - Extracts candidate values from XML text and attributes.
  - Captures element metadata such as name, key, component, tag, and path.

- `match_placeholders(placeholders, v1_values)`
  - Uses `find_best_match(...)` to score candidate values.
  - Builds a mapping of placeholder → chosen value.

- `write_vars_yaml(mapping, yaml_path)`
  - Writes the final values map to YAML.

## How AI is integrated

### AI model used
- `sentence_transformers.SentenceTransformer('all-MiniLM-L6-v2')`

### AI’s role
- AI is now only used for diagnostic purposes.
- It generates a separate review report with candidate suggestions and similarity scores.
- It does not affect the actual `vars.yaml` values or the final rendered XML.

### Why AI is included
- It can help summarize differences between `v1`/`v5` placeholders and source values.
- It can suggest candidate fields for manual review when the structural match is unclear.
- It can provide human-readable mapping explanations without changing output.

### Why AI is not used for matching
- The project now prioritizes structure-based matching first.
- AI is not part of the core score used to choose placeholder values.
- This makes the migration more predictable when the XML structure is the reliable signal.

## Important notes

- `utils/xml_migration.py` requires Python packages:
  - `lxml`
  - `sentence_transformers`
  - optionally `PyYAML` for richer YAML output
- The script’s CLI defaults are configured for this repo, but Ansible passes explicit paths.
- If `windows` inventory is unavailable, the Windows fetch/copy steps are skipped.

## Run the project

1. Ensure the repository root contains `inventory.ini` and `playbook.yaml`.
2. Make sure a Python environment has dependencies installed.
3. Run:
   ```bash
   ansible-playbook -i inventory.ini playbook.yaml
   ```

## Summary

This project is a hybrid Ansible + Python XML migration pipeline. The core Python script converts target XML placeholders into a Jinja2 template, uses AI-assisted matching to fill variable values from source XML, and outputs a renderable YAML-backed template. `playbook.yaml` coordinates the full flow from file fetch to final XML creation and validation.
