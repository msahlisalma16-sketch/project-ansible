pipeline {
    agent any
    stages {
        stage('Checkout') {
            steps {
                git 'https://github.com/msahlisalma16-sketch/project-ansible.git'
            }
        }
        stage('Run Ansible') {
            steps {
                withCredentials([string(credentialsId: 'VAULT_PASS_ID', variable: 'VAULT_PASSWORD')]) {
                    sh '''
                      echo "$VAULT_PASSWORD" > vault_pass.txt
                      ansible-playbook --vault-password-file vault_pass.txt playbook.yaml
                      rm -f vault_pass.txt
                    '''
                }
            }
        }
    }
}