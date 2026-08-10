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
                sh 'ansible-playbook playbook.yaml'
            }
        }
    }
}
