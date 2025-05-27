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
                    docker.image("${DOCKER_IMAGE}:${DOCKER_TAG}").inside() {
                        sh '''
                            cd /app
                            python -m pytest tests/unit/ -v \
                                --junitxml=test-results/unit-tests.xml \
                                --cov=. \
                                --cov-report=xml \
                                --cov-report=html \
                                --cov-fail-under=${MIN_COVERAGE}
                        '''
                    }
                }
            }
            post {
                always {
                    publishTestResults testResultsPattern: 'test-results/unit-tests.xml'
                }
                failure {
                    echo "Unit tests failed"
                    error("Unit tests failed")
                }
            }
            stage('Integration Tests') {
                    steps {
                        script {
                            docker.image("${DOCKER_IMAGE}:${DOCKER_TAG}").inside() {
                                sh '''
                                    cd /app
                                    python run_integration_tests.py
                                '''
                            }
                        }
                    }
                    post {
                        failure {
                            error("Integration tests failed")
                        }
                    }
                }
            post {
                always {
                    // Archive test artifacts
                    archiveArtifacts artifacts: 'test-results/**/*', allowEmptyArchive: true

                    // Post the coverage report
                    publishHTML([
                        allowMissing: false,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'htmlcov',
                        reportFiles: 'index.html',
                        reportName: 'Coverage Report'
                    ])
                }
                success {
                    echo "All tests passed"
                }
                failure {
                    echo "Tests failed"
                    currentBuild.result = 'FAILURE'
                }
            }
        }
    }
}