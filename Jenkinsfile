pipeline {
    agent any

    stages {
        stage('Build') {
            steps {
                script {
                    docker.build("jenkins-llm:${env.BUILD_NUMBER}")
                }
            }
        }
    }
}