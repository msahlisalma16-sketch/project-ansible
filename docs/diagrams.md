# Architecture and Sequence Diagrams (Mermaid)

## System architecture

```mermaid
flowchart LR
  A[Jenkins CI] --> B[Jenkins Agent / Ansible Control Node]
  B --> C[Windows Target]
  B --> D[Repository Files & Scripts]
  D -->|run| E[utils/xml_migration.py]
  E --> F[templates/config.xml.j2]
  E --> G[vars.yaml]
  B -->|render using vars.yaml| H[final_config.xml]
  B --> C[copy final_config.xml]
```

## Sequence diagram

```mermaid
sequenceDiagram
  participant Dev as Developer
  participant GH as GitHub
  participant Jenkins as Jenkins
  participant Agent as Jenkins Agent (Ansible)
  participant Win as Windows Target

  Dev->>GH: push changes (Jenkinsfile, playbook, utils)
  GH->>Jenkins: webhook triggers job
  Jenkins->>Agent: checkout repo
  Jenkins->>Agent: withCredentials(VAULT_FILE)
  Agent->>Agent: run ansible-playbook --vault-password-file
  Agent->>Win: fetch v5.xml
  Agent->>Agent: run utils/xml_migration.py
  Agent->>Agent: write vars.yaml and template
  Agent->>Agent: render final_config.xml
  Agent->>Win: copy final_config.xml
  Agent->>Agent: run tests and save reports
  Jenkins->>GH: post build status
```


## How to view locally
- In Markdown viewers that support Mermaid (VS Code with Mermaid preview, GitHub after rendering), these diagrams will render automatically.
