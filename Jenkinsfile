pipeline {
    agent any

    tools {
        sonarScanner 'SonarScanner'
    }

    environment {
        DOCKER_IMAGE = "jenkins-llm"
        DOCKER_TAG   = "${env.BUILD_NUMBER}"
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 20, unit: 'MINUTES')
        timestamps()
    }

    stages {
        stage('Build') {
            steps {
                echo "🏗️ Stage 1: Build Docker image"
                bat """
                    docker build -t "%DOCKER_IMAGE%:%DOCKER_TAG%" .
                """
            }
            post {
                failure {
                    echo "❌ Build failed"
                    error("Stopping pipeline")
                }
            }
        }

        stage('Test') {
            steps {
                echo "🧪 Stage 2: Run tests"
                bat """
                  docker run --rm ^
                    -v "%WORKSPACE%:/app" ^
                    -w /app ^
                    %DOCKER_IMAGE%:%DOCKER_TAG% ^
                    python -m xmlrunner discover -s tests/unit -o test-results
                """
            }
            post {
                always {
                    echo "🔍 Publishing results"
                    junit 'test-results/*.xml'
                }
                failure {
                    echo "❌ Tests failed"
                    error("Test stage failed")
                }
            }
        }
        stage('Quality Check') {
            steps {
                echo "🔎  Stage 3: Code Quality with SonarQube"
                withSonarQubeEnv('SonarQube') {
                    bat 'sonar-scanner'
                }
            }
            post {
                failure {
                    echo "❌  Sonar analysis failed"
                    error("Quality check failed")
                }
            }
        }
    }

    }

    post {
        always {
            echo "🧹 Cleanup"
            bat """
                docker rmi "%DOCKER_IMAGE%:%DOCKER_TAG%" || exit 0
            """
        }
        success {
            echo "🎉 Pipeline completed!"
        }
        failure {
            echo "🚨 Pipeline failed."
        }
    }
}
