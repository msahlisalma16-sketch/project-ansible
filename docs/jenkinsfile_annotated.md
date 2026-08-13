# Annotated `Jenkinsfile`

This appendix explains the typical `Jenkinsfile` used in the project and where secrets/steps occur.

> Note: Jenkinsfiles can vary — this is a generalized annotation matching the pipeline behavior used in this repo.

## Header / Agent
- `pipeline { agent { label 'ansible' } }` — the agent label selects a Jenkins node with required tooling (python, ansible, git).

## Parameters
- `parameters { string(name: 'BRANCH', defaultValue: 'master') }` — optional user parameters to run pipeline against a different branch.

## Stages

1. Checkout
   - `checkout scm` or `git url` — obtains the repository from GitHub. If using `checkout scm`, Jenkins automatically resolves repo and ref.
   - Credential: Jenkins uses SSH credential (configured in Jenkins) to access the private repository; ensure the credentialID is registered.

2. Prep (optional)
   - Create a virtualenv and install Python dependencies: `python -m venv .venv && .venv/bin/pip install -r requirements.txt`.
   - Purpose: ensure `lxml`, `PyYAML` are available, and optionally `sentence-transformers`.

3. Run Ansible (important)
   - `withCredentials([file(credentialsId: 'VAULT_PASS_FILE_ID', variable: 'VAULT_PASSWORD')])`
     - Jenkins writes the secret file to the agent temporarily and exposes an environment variable referencing the path.
     - The pipeline must remove temporary files afterward (`rm -f $VAULT_PASSWORD`).
   - The pipeline runs:
     ```sh
     ansible-playbook --vault-password-file $VAULT_PASSWORD playbook.yaml
     ```
   - The Ansible playbook performs the migration and rendering steps and may produce `vars.yaml`, `templates/config.xml.j2`, and `final_config.xml`.

4. Post / Cleanup
   - Remove any temporary files, e.g., `rm -f vault_pass.txt` or `rm -f /tmp/tmp.*` used by the job.

## Security annotations
- Avoid echoing the vault password. Use `withCredentials` and `file(...)` to provide the vault password file path securely.
- Prefer `sshagent` or credential-binding for Git operations instead of embedding keys in workspace.
- Use `skipDefaultCheckout()` only when you explicitly perform one `checkout` step — this avoids duplicate checkouts.

## Troubleshooting tips
- If a build fails at `git fetch`, verify the SSH credential is valid and the agent's `known_hosts` includes GitHub.
- If `ansible-playbook` errors about missing Python packages, ensure the `Prep` stage installs `requirements.txt` or the agent already has dependencies.

If you want, I can produce a commented `Jenkinsfile` file tailored to the exact content in the repo (I can fetch the current `Jenkinsfile` and annotate it line-by-line).