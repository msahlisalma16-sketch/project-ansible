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
     pipeline {
    agent any

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
                  python3 -m pip install --upgrade pip
                  python3 -m pip install sentence-transformers torch --index-url https://download.pytorch.org/whl/cpu
                '''
            }
        }

        stage('Generate Configs') {
            steps {
                sh '''
                  ansible-playbook --vault-password-file $VAULT_PASSWORD_FILE -i inventory.ini playbooks/playbook.yaml
                '''
            }
        }

        stage('Run Tests') {
            steps {
                sh '''
                  python3 -m unittest tests/test_xml_migration.py
                  python3 -m unittest tests/test_unmapped_placeholders.py
                '''
            }
        }
    }
}
  
        stage('Generate Configs') {
            steps {
                withCredentials([file(credentialsId: params.VAULT_CREDENTIAL_ID, variable: 'VAULT_PASSWORD_FILE')]) {
                    sh '''
                      set -e
                      "$ANSIBLE_CMD" --vault-password-file "$VAULT_PASSWORD_FILE" -i "$INVENTORY" playbooks/playbook.yaml
                    '''
                }
            }
        }
        stage('Run Tests') {
            steps {
                sh '''
                  set -e
                  export PYTHONPATH=$PYTHONPATH:/var/lib/jenkins/workspace/ansible-pipeline
                  
                  python3 -m unittest tests/test_xml_migration.py
                  python3 -m unittest tests/test_unmapped_placeholders.py

                  python3 tests/score_probe.py
                  python3 utils/debug_match.py
                  python3 utils/debug_parser.py
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
    }
}

