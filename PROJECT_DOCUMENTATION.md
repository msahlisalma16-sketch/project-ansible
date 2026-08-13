# Project Ansible — Full Documentation

## **Overview**
- **Purpose**: This repository automates migrating and rendering XML configuration from an older format (v1) into a newer template format (v5 → Jinja2) and then deploys or copies the generated final XML to a target Windows host using Ansible.
- **Primary outputs**: a Jinja2 template (templates/config_target.j2), a `vars.yaml` file with the mapped values, and a rendered `final_config.xml`.

## **High-level Architecture**
- Source repository (this project), contains:
  - `Jenkinsfile` — CI pipeline that checks out code and runs Ansible on a Jenkins agent.
  - `config.yaml` — centralized configuration file for input/output XML paths and generated files.
  - `playbook.yaml` — top-level Ansible playbook orchestrating the migration and rendering flow.
  - `files/` — contains subfolders: `files/client_sources/` for client source XML files (e.g. `client1_source.xml`, `client2_source.xml`) and `files/master_templates/` for master placeholder template XML files (`master_config.xml`).
  - `templates/` — Jinja2 templates created by the migration for rendering.
  - `utils/` — helper scripts and `config.py` for centralized path settings. `xml_migration.py` processes XML using centralized or CLI paths.
  - `tests/` — unit tests for `xml_migration.py` and helper tools.

- Runtime actors and interactions:
  1. Jenkins (CI): checks out repo, provides Ansible Vault password securely to the job, and runs `ansible-playbook` on an agent.
  2. Ansible control node (Jenkins agent): executes the playbook which runs steps locally and can fetch files from remote Windows targets.
  3. Windows target(s): one or more endpoints where original `v5.xml` might exist and final `final_config.xml` is deployed.
  4. Optional: local developer machine — you can run the playbook locally for testing.


## **Component Details**

  **Architecture diagram**

  ```mermaid
  flowchart LR
    Jenkins[Jenkins CI]
    Agent[Jenkins Agent / Ansible Control Node]
    Repo[GitHub Repository]
    Win[Windows Target]
    Dev[Developer Machine]

    Jenkins -->|triggers job| Agent
    Agent -->|checks out| Repo
    Agent -->|runs| "utils/xml_migration.py"
    "utils/xml_migration.py" -->|writes| Repo
    Agent -->|fetches| Win
    Agent -->|copies final_config.xml| Win
    Dev -->|push code| Repo
  ```

**Centralized Configuration (`config.yaml` / `utils/config.py`)**
- Allows defining master template (`master_template_path`) and multiple client environments (`clients:`).
- Each client entry specifies its own source values (`source_xml`), variable mapping output (`out_vars`), and rendered final XML (`out_final`).
- `utils/xml_migration.py` iterates over all clients defined in `config.yaml`, creating client-specific `vars` files and filled final XML configurations from the single master template.

**`utils/xml_migration.py`**
- Role: parse `v5.xml` for `#{...}` placeholders, parse `v1` XML to find candidate values, score and match placeholders to values, write `vars.yaml`, convert `v5` to a Jinja2 template, and optionally produce an AI review report.
- Key behaviors:
  - `extract_placeholders(v5_path)` — returns extracted placeholders and the parsed XML tree.
  - `parse_v1(v1_path)` — flattens v1 XML elements/attributes into searchable `path`/`text` items.
  - `match_placeholders(placeholders, v1_values)` — heuristic scoring to pick the best candidate for each placeholder.
  - `convert_to_jinja2(tree, out_path)` — write a `.j2` template by replacing `#{...}` → `{{ ... }}`.
  - `write_vars_yaml(mapping, yaml_path)` — write nested YAML mapping; uses `PyYAML` if available.
  - `generate_ai_review(...)` — optional suggestions using `sentence_transformers` (diagnostic only; does not change outputs).
- Why AI is optional: AI suggestions are only for manual review; core mapping is structure/heuristic-based to keep deterministic output.

**`playbook.yaml` (Ansible)**
- Orchestrates tasks such as:
  - Ensure local directories exist.
  - Fetch `v5.xml` from the Windows host via `win_copy`/`win_get` or similar.
  - Run the migration script locally to generate `templates/config.xml.j2` and `vars.yaml`.
  - Render the Jinja2 template with the generated `vars.yaml` to produce `final_config.xml`.
  - Copy `final_config.xml` back to the Windows host and run optional tests.
- Vault handling: the Jenkins job provides the vault password using a secure secret-file credential (no plaintext in the pipeline).



**Templates and Files**
- `templates/` — destination for generated Jinja2 templates. The render step uses `vars.yaml` to produce `final_config.xml`.
- `files/` — structured XML folder containing `files/client_sources/` (legacy/client XML sources) and `files/master_templates/` (master placeholder XML templates).

**Tests**
- `tests/test_xml_migration.py` — unit tests ensure `extract_placeholders`, `parse_v1`, and `write_vars_yaml` behave as expected.
- Run tests locally with:

```bash
python -m unittest discover -s tests -p 'test_*.py'
```


## **Data Flow / Interaction Walkthrough (step-by-step)**
1. Jenkins checks out the repo and runs the pipeline on a configured agent.
2. The pipeline prepares secrets (Vault password) and invokes `ansible-playbook`.
3. Ansible playbook:
   - Ensures local folders (files, templates, final, debug).
   - Fetches `v5.xml` from the Windows host and places it under `files/`.
   - Calls the `xml_migration.py` script:
     - Script scans the `v5.xml` for placeholders `#{...}`.
     - Script scans a chosen `v1` source for possible values.
     - Script runs scoring to match placeholders to values and writes `vars.yaml`.
     - Script converts the original `v5.xml` into a Jinja2 template at `templates/config.xml.j2`.
   - Ansible loads `vars.yaml` and renders the Jinja2 template to produce `final_config.xml`.
   - Ansible copies `final_config.xml` to the Windows target.
4. Ansible runs tests or debug scripts to validate output (e.g., `score_probe.py`, `test_xml_migration.py`).


## **Setup & Run (developer machine)**
1. Clone the repo and switch to a Python environment (recommended):

```bash
git clone git@github.com:msahlisalma16-sketch/project-ansible.git
cd project-ansible
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# or cmd
.\.venv\Scripts\activate.bat

python -m pip install -r requirements.txt
```

2. Run the unit tests:

```bash
python -m unittest discover -s tests -p 'test_*.py'
```

3. Run the Ansible playbook locally (needs Ansible; on Windows use WSL or a Linux runner):

```bash
ansible-playbook --vault-password-file /path/to/vault_pass playbook.yaml
```

Notes:
- If you don't want AI review, you can skip installing `sentence-transformers` — script still works.
- `PyYAML` is optional but recommended.


## **CI / Deployment Notes (Jenkins)**
- Jenkins must have an SSH key configured for the GitHub repo and a secret-file credential containing the Ansible Vault password.
- The `Jenkinsfile` uses `withCredentials([file(credentialsId: 'VAULT_PASS_FILE_ID', variable: 'VAULT_PASSWORD')])` so the pipeline gets a secure file path to pass to `ansible-playbook --vault-password-file`.
- Ensure the Jenkins agent has Python 3.8+ and `pip` available (or use a virtualenv step inside the pipeline to `pip install -r requirements.txt`).


## **Troubleshooting**
- If `ModuleNotFoundError: No module named 'lxml'` appears:
  - Ensure you installed dependencies with `python -m pip install -r requirements.txt` in the interpreter used by Jenkins or the agent.
- If Ansible can't reach the Windows target:
  - Check WinRM settings on the Windows host, firewall rules, and the inventory host address.
- If `vars.yaml` is not generated:
  - Check the migration script output in the Ansible task. The script prints `Writing vars.yaml to ...`






Project Layout

project-ansible/
├── ansible.cfg                   # Ansible configuration
├── config.yaml                   # Central project configuration
├── inventory.ini                 # Ansible inventory
├── Jenkinsfile                   # CI/CD pipeline
├── PROJECT_DOCUMENTATION.md      # Main documentation
├── requirements.txt              # Python dependencies
│
├── artifacts/                    # Packages, IDE configs, & build outputs
│   ├── jenkins_2.568.2_all.deb
│   ├── git_status.txt
│   └── projects
│
├── docs/                         # Markdown documentation & diagrams
│   ├── diagrams.md
│   ├── file_inventory.md
│   ├── index.md
│   └── security_checklist.md
│
├── files/                        # XML Input Files
│   ├── master_templates/         # Master template XMLs (containing #{...} placeholders)
│   │   └── master_config.xml
│   └── client_sources/           # Client source XMLs (containing canonical values)
│       ├── client1_source.xml
│       └── client2_source.xml
│
├── final/                        # Generated Final Output XMLs
│   ├── client1_config.xml
│   └── client2_config.xml
│
├── playbooks/                    # Ansible Playbooks
│   ├── playbook.yaml
│   └── ping.yaml
│
├── reports/                      # Generated Mapping & AI Review Reports
│   ├── mappings/
│   │   ├── mapping_report_client1.txt
│   │   └── mapping_report_client2.txt
│   └── ai_reviews/
│       ├── mapping_ai_review_client1.txt
│       └── mapping_ai_review_client2.txt
│
├── templates/                    # Generated Jinja2 Templates
│   └── config_target.j2
│
├── tests/                        # Unit Tests & Probes
│   ├── test_xml_migration.py
│   └── score_probe.py
│
├── utils/                        # Python Scripts & Config Loader
│   ├── config.py
│   ├── xml_migration.py
│   ├── debug_parser.py
│   └── debug_match.py
│
└── vars/                         # Generated Client Variable YAML Files
    ├── vars_client1.yaml
    └── vars_client2.yaml






































































































































  on success.


## **Security Considerations**
- Never store vault passwords in plaintext in the repo.
- Use Jenkins secret-file credentials (or HashiCorp Vault / other secrets manager) to provide secrets to the pipeline.
- Generated `vars.yaml` can contain secrets found in `v1` XML; treat it as sensitive in downstream pipelines and clean up temporary files after use.


## **How to Extend / Contribute**
- To add a new mapping heuristic, update `utils/xml_migration.py` in `score_candidate()` and add unit tests under `tests/`.
- To add a new Jenkins stage, modify the `Jenkinsfile` and test on a branch before merging.
- For better output control, add CLI flags to `xml_migration.py` (e.g., `--template-name`, `--strict-matching`).


## **Glossary**
- `v1.xml` — legacy XML structure containing canonical values.
- `v5.xml` — target XML with `#{...}` placeholders to be converted into Jinja2.
- `vars.yaml` — produced YAML mapping consumed by Ansible to render templates.
- `Jinja2` — templating engine used by Ansible for rendering templates.
- `Ansible Vault` — tool to encrypt secrets used in Ansible playbooks.


## **Files of Interest**
- `Jenkinsfile` — CI pipeline.
- `playbook.yaml` — Ansible orchestration.
- `utils/xml_migration.py` — core migration script.
- `requirements.txt` — Python dependencies.
- `tests/test_xml_migration.py` — unit tests.

