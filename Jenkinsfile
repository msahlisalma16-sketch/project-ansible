pipeline {
    agent any
    
    options {
        skipDefaultCheckout()
    }

    parameters {
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

        stage('Setup Python deps') {
            steps {
                sh '''
                  rm -rf .venv
                  python3 -m venv .venv
                  . .venv/bin/activate
                  pip install --upgrade pip
                  pip install -r requirements.txt
                '''
            }
        }

        stage('Generate Configs') {
            steps {
                withCredentials([file(credentialsId: params.VAULT_CREDENTIAL_ID, variable: 'VAULT_PASSWORD_FILE')]) {
                    sh '''
                      set -e
                      . .venv/bin/activate
                      "$ANSIBLE_CMD" --vault-password-file "$VAULT_PASSWORD_FILE" -i "$INVENTORY" playbooks/playbook.yaml
                    '''
                }
            }
        }

        stage('Run Tests') {
            steps {
                sh '''
                  set -e
                  . .venv/bin/activate
                  export PYTHONPATH=$PYTHONPATH:/var/lib/jenkins/workspace/ansible-pipeline

                  python -m unittest tests/test_xml_migration.py
                  python -m unittest tests/test_unmapped_placeholders.py

                  python tests/score_probe.py
                  python utils/debug_match.py
                  python utils/debug_parser.py
                '''
            }
        }

        stage('Secure Artifacts') {
            steps {
                sh '''
                  chmod 600 vars/*.yaml || true
                '''
            }
        }
    }

    post {
        success {
            archiveArtifacts artifacts: 'final/**, reports/**, vars/**, debug/**', fingerprint: true
        }
        failure {
            echo 'Pipeline failed — configs not deployed.'
        }
        always {
            sh 'rm -f "$VAULT_PASSWORD_FILE"'
            archiveArtifacts artifacts: 'reports/**', fingerprint: true
        }
    }
}

