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

        stage('Test') {
            steps {
                script {
                    // use the freshly built image
                    docker.image("jenkins-llm:${env.BUILD_NUMBER}").inside {
                        // run your pytest suite
                        sh '''
                            cd /app
                            python -m pytest tests/unit/ -v --junitxml=test-results.xml
                        '''
                    }
                }
            }
            post {
                always {
                    // publish the JUnit report
                    publishTestResults testResultsPattern: 'test-results.xml'
                }
            }
        }
    }
}
