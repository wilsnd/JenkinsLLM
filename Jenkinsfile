pipeline {
    agent any

    environment {
        DOCKER_IMAGE = "jenkins-llm"
        DOCKER_TAG   = "${env.BUILD_NUMBER}"
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 60, unit: 'MINUTES')
        timestamps()
    }

    stages {
        stage('Build') {
            steps {
                script {
                    echo "🏗️ Building Docker image"
                    docker.build("${DOCKER_IMAGE}:${DOCKER_TAG}")
                    sh "docker tag ${DOCKER_IMAGE}:${DOCKER_TAG} ${DOCKER_IMAGE}:latest"
                    echo "✅ Build completed successfully"
                }
            }
            post {
                failure {
                    echo "❌ Build stage failed - stopping pipeline"
                    error("Build failed")
                }
            }
        }

        stage('Test') {
            parallel {
                stage('Unit Tests') {
                    steps {
                        script {
                            echo "🧪 Running Unit Tests"
                            docker.image("${DOCKER_IMAGE}:${DOCKER_TAG}").inside {
                                sh '''
                                    cd /app
                                    python -m pytest tests/unit/ -v \
                                        --junitxml=test-results/unit-tests.xml
                                '''
                            }
                        }
                    }
                    post {
                        always {
                            publishTestResults testResultsPattern: 'test-results/unit-tests.xml'
                        }
                        failure {
                            echo "❌ Unit tests failed - failing pipeline"
                            error("Unit tests failed")
                        }
                    }
                }

                stage('Integration Tests') {
                    steps {
                        script {
                            echo "🔧 Running Integration Tests"
                            docker.image("${DOCKER_IMAGE}:${DOCKER_TAG}").inside {
                                sh '''
                                    cd /app
                                    python run_integration_tests.py
                                '''
                            }
                        }
                    }
                    post {
                        failure {
                            echo "❌ Integration tests failed - failing pipeline"
                            error("Integration tests failed")
                        }
                    }
                }
            }
            post {
                always {
                    archiveArtifacts artifacts: 'test-results/**/*', allowEmptyArchive: true
                }
                success {
                    echo "✅ All tests passed"
                }
                failure {
                    script {
                        echo "❌ Tests failed - pipeline stopped"
                        currentBuild.result = 'FAILURE'
                    }
                }
            }
        }
    }

    post {
        always {
            script {
                echo "🧹 Cleaning up Docker images"
                sh '''
                    docker rmi ${DOCKER_IMAGE}:${DOCKER_TAG} || true
                    docker system prune -f || true
                '''
            }
        }
        success {
            echo "🎉 Pipeline completed successfully!"
        }
        failure {
            echo "❌ Pipeline failed at stage: ${env.STAGE_NAME}"
        }
    }
}
