# Security Checklist and Best Practices

This checklist covers concrete controls, CI agent hardening, secrets lifecycle, and artifact handling appropriate for this project.

1. Jenkins credentials and access
   - Create an SSH key pair for Jenkins to access GitHub; restrict its repo access to this project.
   - Use Jenkins credentials (SSH key) and bind them via `sshagent` or `checkout scm`.
   - Use role-based access control (RBAC) in Jenkins: restrict who can create / edit jobs and who can read build logs.

2. Vault / Secrets handling
   - Store Ansible Vault passphrase as a Jenkins `secret file` credential.
   - Use `withCredentials([file(credentialsId: 'VAULT_ID', variable: 'VAULT_PASSWORD')])` so the agent receives a file path only.
   - Ensure temporary vault files are `rm -f`'d in `post` steps.
   - Rotate vault credentials periodically and audit access to the secrets.

3. Generated artifacts and sensitive files
   - Treat `vars.yaml` as sensitive if it contains credentials; do not commit generated `vars.yaml` to the Git repo.
   - Add `templates/`, `final/`, `vars.yaml`, and `mapping_*.txt` to `.gitignore` if they must not be tracked.
   - Limit artifact retention in Jenkins; enable artifact cleanup policies.

4. Agent hardening
   - Use dedicated Jenkins agents for sensitive pipelines; ideally ephemeral agents (container-based) that are destroyed after use.
   - Ensure agents have minimal access to network resources except what is required (e.g., inventory hosts).
   - Configure the agent OS to have least-privilege service accounts.

5. File permissions
   - Generated files created by the pipeline should have restrictive permissions while in workspace: e.g., `chmod 600 vars.yaml` if it contains secrets.
   - When copying to Windows hosts, use secure transport and delete temporary local copies after transfer.

6. Logging and audit
   - Mask secrets in Jenkins build logs (Jenkins built-in masking for credentials bindings).
   - Keep a secure audit trail for who triggered runs and viewed logs containing sensitive outputs.

7. Dependency and supply-chain
   - Pin versions in `requirements.txt` where feasible to avoid unexpected breaking changes (e.g., `lxml==6.1.1`).
   - Run periodic `pip-audit` or dependency scanning to detect vulnerable packages.

8. CI best practices
   - Avoid storing long-lived credentials in jobs; use short-lived tokens where possible.
   - Use branch protection rules on GitHub and require PR reviews for changes to `Jenkinsfile` or `playbook.yaml`.

9. Recovery and incident response
   - If a secret leaks, rotate the secret immediately and invalidate related credentials.
   - Keep a documented rollback plan for production changes that includes restoring the previous `final_config.xml`.


## Quick checklist (copyable)
- [ ] Jenkins: SSH key configured and limited to repo
- [ ] Jenkins: Vault pass stored as secret-file credential
- [ ] Workspace: `vars.yaml` not committed; added to `.gitignore` if needed
- [ ] Agents: ephemeral or isolated with minimal access
- [ ] Dependencies: pin versions and run vulnerability scans
- [ ] Cleanup: temporary files removed in `post` stage
