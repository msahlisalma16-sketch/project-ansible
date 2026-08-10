pipeline {
    agent any
    options {
        skipDefaultCheckout()
    }
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        stage('Run Ansible') {
            steps {
                withCredentials([string(credentialsId: 'VAULT_PASS_ID', variable: 'VAULT_PASSWORD')]) {
                    sh '''
                      set -e
                      vault_file=$(mktemp)
                      echo "$VAULT_PASSWORD" > "$vault_file"
                      ansible-playbook --vault-password-file "$vault_file" playbook.yaml
                      rm -f "$vault_file"
                    '''
                }
            }
        }
    }
    post {
        always {
            sh 'rm -f vault_pass.txt || true'
        }
    }
}