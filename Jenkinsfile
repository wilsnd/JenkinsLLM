pipeline {
    agent any

    environment {
        // Docker settings
        DOCKER_IMAGE = "jenkins-llm"
        DOCKER_TAG = "${env.BUILD_NUMBER}"

        // Quality gate thresholds
        MIN_COVERAGE = "70"
        MAX_CRITICAL_ISSUES = "0"
        MAX_MAJOR_ISSUES = "5"
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

                    // Build Docker image
                    def image = docker.build("${DOCKER_IMAGE}:${DOCKER_TAG}")

                    // Tag as latest
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
                            // Publish test results
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
                            echo "❌ Integration tests failed - failing pipeline"
                            error("Integration tests failed")
                        }
                    }
                }
            }
            post {
                always {
                    // Archive test artifacts
                    archiveArtifacts artifacts: 'test-results/**/*', allowEmptyArchive: true

                    // Publish coverage report
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
                    echo "✅ All tests passed - proceeding to quality analysis"
                }
                failure {
                    echo "❌ Tests failed - pipeline stopped"
                    currentBuild.result = 'FAILURE'
                }
            }
        }

        stage('Code Quality') {
            parallel {
                stage('SonarQube Analysis') {
                    steps {
                        script {
                            echo "📊 Running SonarQube Analysis"

                            withSonarQubeEnv('SonarQube') {
                                sh '''
                                    sonar-scanner \
                                        -Dsonar.projectKey=llm-pipeline \
                                        -Dsonar.sources=. \
                                        -Dsonar.exclusions=**/tests/**,**/data/**,**/__pycache__/** \
                                        -Dsonar.python.coverage.reportPaths=coverage.xml \
                                        -Dsonar.python.xunit.reportPath=test-results/unit-tests.xml
                                '''
                            }
                        }
                    }
                }

                stage('Code Linting') {
                    steps {
                        script {
                            echo "📝 Running Code Linting"

                            docker.image("${DOCKER_IMAGE}:${DOCKER_TAG}").inside() {
                                sh '''
                                    cd /app

                                    # Run flake8
                                    flake8 . \
                                        --exclude=data,processed_data,models,tests \
                                        --max-line-length=100 \
                                        --output-file=flake8-report.txt || true

                                    # Run pylint
                                    pylint **/*.py \
                                        --ignore=data,processed_data,models,tests \
                                        --output-format=json > pylint-report.json || true
                                '''
                            }
                        }
                    }
                    post {
                        always {
                            archiveArtifacts artifacts: '*-report.*', allowEmptyArchive: true
                        }
                    }
                }
            }
            post {
                always {
                    script {
                        // Wait for SonarQube quality gate
                        timeout(time: 10, unit: 'MINUTES') {
                            def qg = waitForQualityGate()

                            if (qg.status != 'OK') {
                                echo "❌ Quality Gate failed: ${qg.status}"

                                // Check specific metrics
                                if (qg.status == 'ERROR') {
                                    error("Quality gate failed with ERROR status")
                                } else {
                                    echo "⚠️ Quality gate failed with WARNING - continuing"
                                    currentBuild.result = 'UNSTABLE'
                                }
                            } else {
                                echo "✅ Quality gate passed"
                            }
                        }
                    }
                }
                failure {
                    echo "❌ Code quality stage failed - pipeline stopped"
                    currentBuild.result = 'FAILURE'
                }
                unstable {
                    echo "⚠️ Code quality issues detected - marked as unstable"
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
            echo "🎉 Pipeline stages 1-3 completed successfully!"
            emailext(
                subject: "✅ Pipeline Success: ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                body: "Build, Test, and Code Quality stages completed successfully!",
                to: "${env.CHANGE_AUTHOR_EMAIL ?: 'team@company.com'}"
            )
        }

        failure {
            echo "❌ Pipeline failed"
            emailext(
                subject: "❌ Pipeline Failed: ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                body: "Pipeline failed at stage: ${env.STAGE_NAME}. Check logs for details.",
                to: "${env.CHANGE_AUTHOR_EMAIL ?: 'team@company.com'}"
            )
        }

        unstable {
            echo "⚠️ Pipeline completed with warnings"
            emailext(
                subject: "⚠️ Pipeline Unstable: ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                body: "Pipeline completed but has quality issues. Review the reports.",
                to: "${env.CHANGE_AUTHOR_EMAIL ?: 'team@company.com'}"
            )
        }
    }
}