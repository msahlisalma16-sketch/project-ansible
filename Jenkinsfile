pipeline {
    agent any
    options {
        skipDefaultCheckout()
    }
    parameters {
        string(name: 'PLAYBOOK_NAME', defaultValue: 'playbooks/playbook.yaml', description: 'Ansible playbook to run')
        string(name: 'INVENTORY', defaultValue: 'inventory.ini', description: 'Ansible inventory file')
        string(name: 'VAULT_CREDENTIAL_ID', defaultValue: 'VAULT_PASS_FILE', description: 'Jenkins credential ID for the Ansible vault password file')
        string(name: 'ANSIBLE_CMD', defaultValue: 'ansible-playbook', description: 'Ansible command to execute')
    }
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        stage('Prep') {
            steps {
                sh '''
                  set -e
                  $ANSIBLE_CMD --version
                  python3 --version
                '''
            }
        }
        stage('Run Ansible') {
            steps {
                withCredentials([file(credentialsId: params.VAULT_CREDENTIAL_ID, variable: 'VAULT_PASSWORD_FILE')]) {
                    sh '''
                      set -e
                      "$ANSIBLE_CMD" --vault-password-file "$VAULT_PASSWORD_FILE" -i "$INVENTORY" "$PLAYBOOK_NAME"
                    '''
                }
            }
        }
    }
}
