# Project Workflow Summary

This project is an automated XML migration pipeline built with Jenkins and Ansible. The Jenkins job checks out the repository, creates a Python virtual environment, installs dependencies, and runs the main Ansible playbook.

## End-to-End Flow

1. The playbook first prepares the local workspace on the control node by creating the required folders: `files/`, `files/master_templates/`, `templates/`, `final/`, and `debug/`.
2. It then fetches the master template XML from the Windows hosts into `files/master_templates/master_config.xml`.
3. The client source XML files stay on the control node in `files/client_sources/`.
4. For each client source XML, the migration script `utils/xml_migration.py` runs locally on the control node.
5. The migration script reads the client source XML and the fetched master template, maps values to placeholders, and generates the output artifacts.
6. The migration script also writes a short management summary report for each client, showing totals such as placeholders found, matched, unmapped, and the match rate.
7. The pipeline runs validation and debug scripts to confirm the migration logic is working correctly.
8. The final XML files from `final/` are copied back to the Windows target under `C:\Users\vboxuser\Desktop\project\...`.

## Files Involved

- `Jenkinsfile` - starts the pipeline and runs Ansible.
- `playbooks/playbook.yaml` - coordinates directory setup, fetch, migration, testing, and copy-back.
- `files/master_templates/master_config.xml` - fetched master XML template with placeholders.
- `files/client_sources/` - local client XML source files used as input values.
- `utils/xml_migration.py` - core migration script that creates vars, reports, and final XML output.
- `vars/` - generated client-specific YAML variable files.
- `reports/mappings/` - generated mapping reports.
- `reports/ai_reviews/` - generated AI review reports.
- `reports/summary/` - management summary reports for supervisors and quick review.
- `final/` - generated final XML files.
- `debug/` - logs and debug output from validation scripts.

## Important Conditions

- The Windows user path must stay consistent for fetch and copy-back operations.
- The master template is fetched from Windows; the client XML sources remain local on the control node.
- The migration step runs per client source XML, not for a single hard-coded file.
- The pipeline should be able to handle multiple Windows hosts if the inventory contains more than one.
- Tests and debug scripts are part of the workflow so the generated artifacts can be verified before copying them back to Windows.

