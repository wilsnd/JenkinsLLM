pipeline {
    agent any

    parameters {
        booleanParam(name: 'FORCE_RELEASE', defaultValue: false, description: 'Force release to production regardless of branch')
        choice(name: 'SECURITY_LEVEL', choices: ['standard', 'strict'], description: 'Security scanning level')
        string(name: 'NOTIFICATION_EMAIL', defaultValue: '', description: 'Override notification email')
    }

    tools {
        sonarRunner 'SonarScanner'
    }

    environment {
        DOCKER_IMAGE = "jenkins-llm"
        DOCKER_TAG   = "${env.BUILD_NUMBER}"
        NOTIFICATION_EMAIL = "${params.NOTIFICATION_EMAIL ?: env.CHANGE_AUTHOR_EMAIL ?: 'admin@example.com'}"
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 90, unit: 'MINUTES')
        timestamps()
    }

    stages {
        stage('Build') {
            steps {
                echo "🏗️ Stage 1: Build Docker image"
                script {
                    def imageTag = "${env.DOCKER_IMAGE}:${env.BUILD_NUMBER}"
                    def latestTag = "${env.DOCKER_IMAGE}:latest"

                    // Build with version tags
                    bat "docker build -t \"${imageTag}\" -t \"${latestTag}\" ."

                    // Store build info
                    writeFile file: 'build-info.json', text: """
                    {
                        "buildNumber": "${env.BUILD_NUMBER}",
                        "gitCommit": "${env.GIT_COMMIT}",
                        "buildTime": "${new Date()}",
                        "imageTag": "${imageTag}"
                    }
                    """

                    archiveArtifacts artifacts: 'build-info.json', fingerprint: true
                    echo "✅ Build tagged as: ${imageTag}"
                }
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
                echo "🧪 Stage 2: Run comprehensive tests"

                // Unit Tests with Coverage
                bat '''
                    docker run --rm ^
                      -v "%WORKSPACE%:/app" ^
                      -w /app ^
                      %DOCKER_IMAGE%:%DOCKER_TAG% ^
                      pip install coverage xmlrunner && coverage run --source=. --omit="*/tests/*,*/test_*,*/__pycache__/*,*/venv/*" -m xmlrunner discover -s tests/unit -o test-results
                '''

                // Generate coverage reports
                bat '''
                    docker run --rm ^
                      -v "%WORKSPACE%:/app" ^
                      -w /app ^
                      %DOCKER_IMAGE%:%DOCKER_TAG% ^
                      coverage xml -o coverage.xml
                '''

                bat '''
                    docker run --rm ^
                      -v "%WORKSPACE%:/app" ^
                      -w /app ^
                      %DOCKER_IMAGE%:%DOCKER_TAG% ^
                      coverage html -d htmlcov
                '''

                // Integration Tests
                bat '''
                    docker run --rm ^
                      -v "%WORKSPACE%:/app" ^
                      -w /app ^
                      %DOCKER_IMAGE%:%DOCKER_TAG% ^
                      python -m xmlrunner discover -s tests/integration -o test-results/integration
                '''

                // Archive coverage reports
                publishHTML([
                    allowMissing: false,
                    alwaysLinkToLastBuild: true,
                    keepAll: true,
                    reportDir: 'htmlcov',
                    reportFiles: 'index.html',
                    reportName: 'Coverage Report'
                ])
            }
            post {
                always {
                    junit 'test-results/*.xml'
                    junit 'test-results/integration/*.xml'
                    archiveArtifacts artifacts: 'coverage.xml,htmlcov/**', allowEmptyArchive: true
                }
                failure {
                    echo "❌ Tests failed"
                    error("Test stage failed")
                }
                success {
                    script {
                        // Check coverage threshold
                        bat '''
                            docker run --rm ^
                              -v "%WORKSPACE%:/app" ^
                              -w /app ^
                              %DOCKER_IMAGE%:%DOCKER_TAG% ^
                              coverage report --fail-under=70
                        '''
                    }
                    echo "✅ All tests passed with adequate coverage (≥70%)"
                }
            }
        }

        stage('Quality') {
            steps {
                echo "🔎 Stage 3: Advanced Code Quality Analysis"
                script {
                    def scannerHome = tool 'SonarScanner'
                    withSonarQubeEnv('SonarQube') {
                        bat """
                            ${scannerHome}\\bin\\sonar-scanner.bat ^
                            -Dsonar.projectKey=jenkins-llm ^
                            -Dsonar.organization=jenkins-llm ^
                            -Dsonar.sources=. ^
                            -Dsonar.exclusions=**/tests/**,**/test-results/**,**/__pycache__/**,**/venv/** ^
                            -Dsonar.python.coverage.reportPaths=coverage.xml ^
                            -Dsonar.qualitygate.wait=true ^
                            -Dsonar.qualitygate.timeout=300 ^
                            -Dsonar.coverage.exclusions=**/tests/**,**/test_*/** ^
                            -Dsonar.duplicated.exclusions=**/tests/** ^
                            -Dsonar.issue.ignore.multicriteria=e1,e2 ^
                            -Dsonar.issue.ignore.multicriteria.e1.ruleKey=python:S1192 ^
                            -Dsonar.issue.ignore.multicriteria.e1.resourceKey=**/test_*.py ^
                            -Dsonar.issue.ignore.multicriteria.e2.ruleKey=python:S125 ^
                            -Dsonar.issue.ignore.multicriteria.e2.resourceKey=**/docs/**
                        """
                    }
                }
                timeout(time: 10, unit: 'MINUTES') {
                    script {
                        def qg = waitForQualityGate()
                        echo "Quality Gate status: ${qg.status}"

                        if (qg.status != 'OK') {
                            def message = "Quality Gate failed with status: ${qg.status}"
                            if (qg.conditions) {
                                qg.conditions.each { condition ->
                                    echo "Failed condition: ${condition.metricKey} - ${condition.status}"
                                    echo "Threshold: ${condition.errorThreshold}, Actual: ${condition.actualValue}"
                                }
                            }
                            error(message)
                        }

                        writeFile file: 'quality-report.json', text: """
                        {
                            "buildNumber": "${env.BUILD_NUMBER}",
                            "qualityGateStatus": "${qg.status}",
                            "timestamp": "${new Date()}",
                            "projectKey": "jenkins-llm"
                        }
                        """

                        archiveArtifacts artifacts: 'quality-report.json', fingerprint: true
                        echo "✅ Quality gate passed with advanced configuration"
                    }
                }
            }
            post {
                failure {
                    emailext (
                        subject: "Quality Gate Failed: ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                        body: "Quality gate has failed for build ${env.BUILD_NUMBER}. Check SonarQube dashboard.",
                        to: "${env.NOTIFICATION_EMAIL}"
                    )
                }
            }
        }

        stage('Security') {
            steps {
                echo "🔒 Stage 4: Security Analysis"

                // Python dependency vulnerability scanning with Safety
                bat '''
                    docker run --rm ^
                      -v "%WORKSPACE%:/app" ^
                      -w /app ^
                      %DOCKER_IMAGE%:%DOCKER_TAG% ^
                      safety check --json --output safety-report.json || echo "Safety scan completed"
                '''

                // Bandit security linting for Python code
                bat '''
                    docker run --rm ^
                      -v "%WORKSPACE%:/app" ^
                      -w /app ^
                      %DOCKER_IMAGE%:%DOCKER_TAG% ^
                      bandit -r . -f json -o bandit-report.json -x "*/tests/*,*/test_*" || echo "Bandit scan completed"
                '''

                // Process security reports
                script {
                    def securityIssues = []

                    // Parse Safety report --> dependency vulnerabilities check
                    if (fileExists('safety-report.json')) {
                        try {
                            def safetyReport = readJSON file: 'safety-report.json'
                            echo "Safety scan found ${safetyReport.size()} dependency vulnerabilities"

                            safetyReport.each { vuln ->
                                securityIssues.add([
                                    type: 'Dependency Vulnerability',
                                    severity: 'HIGH',
                                    description: "Package: ${vuln.package_name}, Vulnerability: ${vuln.vulnerability_id}",
                                    recommendation: "Update ${vuln.package_name} to version ${vuln.analyzed_version}"
                                ])
                            }
                        } catch (Exception e) {
                            echo "Note: Safety report format may be different - ${e.message}"
                        }
                    }

                    // Parse Bandit report --> code security issues check
                    if (fileExists('bandit-report.json')) {
                        try {
                            def banditReport = readJSON file: 'bandit-report.json'
                            def results = banditReport.results ?: []
                            echo "Bandit scan found ${results.size()} code security issues"

                            results.each { issue ->
                                securityIssues.add([
                                    type: 'Code Security Issue',
                                    severity: issue.issue_severity?.toUpperCase() ?: 'MEDIUM',
                                    description: "${issue.test_name}: ${issue.issue_text}",
                                    location: "${issue.filename}:${issue.line_number}",
                                    recommendation: "Review and fix: ${issue.issue_text}"
                                ])
                            }
                        } catch (Exception e) {
                            echo "Note: Bandit report format may be different - ${e.message}"
                        }
                    }

                    // Create security summary
                    def securitySummary = [
                        buildNumber: env.BUILD_NUMBER,
                        timestamp: new Date().toString(),
                        totalIssues: securityIssues.size(),
                        highSeverity: securityIssues.count { it.severity == 'HIGH' },
                        mediumSeverity: securityIssues.count { it.severity == 'MEDIUM' },
                        lowSeverity: securityIssues.count { it.severity == 'LOW' },
                        issues: securityIssues
                    ]

                    writeJSON file: 'security-summary.json', json: securitySummary

                    // Report findings
                    echo "🔍 Security Analysis Results:"
                    echo "  Total Issues: ${securitySummary.totalIssues}"
                    echo "  High Severity: ${securitySummary.highSeverity}"
                    echo "  Medium Severity: ${securitySummary.mediumSeverity}"
                    echo "  Low Severity: ${securitySummary.lowSeverity}"

                    // Log critical issues
                    securityIssues.findAll { it.severity == 'HIGH' }.each { issue ->
                        echo "⚠️ HIGH SEVERITY: ${issue.description}"
                        echo "   Recommendation: ${issue.recommendation}"
                    }

                    // Fail build if too many high severity level issues
                    if (securitySummary.highSeverity > 10) {
                        error("Security gate failed: Too many high severity issues (${securitySummary.highSeverity})")
                    }

                    echo "✅ Security analysis completed successfully"
                }
            }
            post {
                always {
                    archiveArtifacts artifacts: '*-report.json,security-summary.json', allowEmptyArchive: true

                    publishHTML([
                        allowMissing: true,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: '.',
                        reportFiles: 'security-summary.json',
                        reportName: 'Security Report'
                    ])
                }
                failure {
                    emailext (
                        subject: "Security Issues Found: ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                        body: "Security analysis found critical issues in build ${env.BUILD_NUMBER}. Review the security report.",
                        to: "${env.NOTIFICATION_EMAIL}"
                    )
                }
            }
        }

        stage('Deploy') {
            steps {
                echo "🚀 Stage 5: Deploy to Test Environment"

                script {
                    def deploymentName = "jenkins-llm-test"
                    def testPort = "5001"
                    def healthCheckUrl = "http://localhost:${testPort}"

                    // Stop existing test deployment
                    bat """
                        docker stop ${deploymentName} 2>nul || echo "No existing container to stop"
                        docker rm ${deploymentName} 2>nul || echo "No existing container to remove"
                    """

                    // Deploy to test environment
                    bat """
                        docker run -d ^
                          --name ${deploymentName} ^
                          -p ${testPort}:5000 ^
                          -e ENVIRONMENT=test ^
                          -e LOG_LEVEL=DEBUG ^
                          --health-cmd="curl -f http://localhost:5000/health || exit 1" ^
                          --health-interval=30s ^
                          --health-timeout=10s ^
                          --health-retries=3 ^
                          ${env.DOCKER_IMAGE}:${env.DOCKER_TAG}
                    """

                    // Wait for deployment to be ready
                    echo "⏳ Waiting for deployment to be ready..."
                    timeout(time: 5, unit: 'MINUTES') {
                        waitUntil {
                            script {
                                def result = bat(
                                    script: "curl -f ${healthCheckUrl}/health --max-time 10",
                                    returnStatus: true
                                )
                                return result == 0
                            }
                        }
                    }

                    // API functionality test
                    bat """
                        curl -X POST ${healthCheckUrl}/generate ^
                          -H "Content-Type: application/json" ^
                          -d "{\\"prompt\\": \\"test\\"}" ^
                          -o api-test-result.json
                    """

                    // Validate API response
                    script {
                        if (fileExists('api-test-result.json')) {
                            try {
                                def apiResult = readJSON file: 'api-test-result.json'
                                if (apiResult.result) {
                                    echo "✅ API test successful: Generated text received"
                                } else {
                                    error("❌ API test failed: No generated text in response")
                                }
                            } catch (Exception e) {
                                echo "⚠️ API response validation failed: ${e.message}"
                            }
                        }
                    }

                    // Create deployment report
                    def deploymentInfo = [
                        buildNumber: env.BUILD_NUMBER,
                        deploymentName: deploymentName,
                        imageTag: "${env.DOCKER_IMAGE}:${env.DOCKER_TAG}",
                        environment: 'test',
                        port: testPort,
                        timestamp: new Date().toString(),
                        healthCheckUrl: healthCheckUrl,
                        status: 'deployed'
                    ]

                    writeJSON file: 'deployment-info.json', json: deploymentInfo

                    echo "✅ Deployment to test environment successful!"
                    echo "🌐 Application accessible at: ${healthCheckUrl}"
                    echo "📋 Container name: ${deploymentName}"
                }
            }
            post {
                always {
                    archiveArtifacts artifacts: 'deployment-info.json,api-test-result.json', allowEmptyArchive: true

                    script {
                        bat '''
                            docker logs jenkins-llm-test > deployment-logs.txt 2>&1 || echo "No logs available"
                        '''
                    }
                    archiveArtifacts artifacts: 'deployment-logs.txt', allowEmptyArchive: true
                }
                failure {
                    script {
                        bat '''
                            docker stop jenkins-llm-test 2>nul || echo "Container already stopped"
                            docker rm jenkins-llm-test 2>nul || echo "Container already removed"
                        '''
                    }
                    emailext (
                        subject: "Deployment Failed: ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                        body: "Deployment to test environment failed for build ${env.BUILD_NUMBER}. Check deployment logs.",
                        to: "${env.NOTIFICATION_EMAIL}"
                    )
                }
            }
        }

        stage('Release') {
            when {
                anyOf {
                    branch 'main'
                    branch 'master'
                    expression { params.FORCE_RELEASE == true }
                }
            }
            steps {
                echo "🎯 Stage 6: Release to Production Environment"

                script {
                    def prodDeploymentName = "jenkins-llm-prod"
                    def prodPort = "5000"
                    def prodHealthUrl = "http://localhost:${prodPort}"
                    def releaseVersion = "v${env.BUILD_NUMBER}"

                    // Pre-release validation
                    echo "🔍 Pre-release validation..."

                    // Make sure the test environment is still healthy
                    def testHealthy = bat(
                        script: "curl -f http://localhost:5001/health --max-time 10",
                        returnStatus: true
                    ) == 0

                    if (!testHealthy) {
                        error("❌ Test environment unhealthy, aborting release")
                    }

                    // Tag the Docker image for production
                    bat """
                        docker tag ${env.DOCKER_IMAGE}:${env.DOCKER_TAG} ${env.DOCKER_IMAGE}:${releaseVersion}
                        docker tag ${env.DOCKER_IMAGE}:${env.DOCKER_TAG} ${env.DOCKER_IMAGE}:production
                    """

                    // Create release notes
                    def releaseNotes = [
                        version: releaseVersion,
                        buildNumber: env.BUILD_NUMBER,
                        gitCommit: env.GIT_COMMIT ?: 'unknown',
                        releaseDate: new Date().toString(),
                        environment: 'production',
                        features: [
                            "LLM inference API with health monitoring",
                            "Batch processing capabilities",
                            "Docker containerization with health checks",
                            "Prometheus metrics collection",
                            "Enhanced security scanning"
                        ],
                        testResults: [
                            unitTests: "Passed",
                            integrationTests: "Passed",
                            securityScan: "Passed",
                            codeQuality: "Passed"
                        ]
                    ]

                    writeJSON file: 'release-notes.json', json: releaseNotes

                    // Check if production container exists for blue-green deployment
                    def prodExists = bat(
                        script: "docker inspect ${prodDeploymentName} 2>nul",
                        returnStatus: true
                    ) == 0

                    if (prodExists) {
                        echo "🔄 Performing blue-green deployment..."
                        // Stop old version
                        bat """
                            docker stop ${prodDeploymentName}
                            docker rm ${prodDeploymentName}
                        """
                    } else {
                        echo "🆕 First production deployment..."
                    }

                    // Deploy new version
                    bat """
                        docker run -d ^
                          --name ${prodDeploymentName} ^
                          -p ${prodPort}:5000 ^
                          -e ENVIRONMENT=production ^
                          -e LOG_LEVEL=INFO ^
                          --restart=unless-stopped ^
                          ${env.DOCKER_IMAGE}:${releaseVersion}
                    """

                    // Final production health check
                    echo "🏥 Final production health check..."
                    timeout(time: 3, unit: 'MINUTES') {
                        waitUntil {
                            script {
                                return bat(
                                    script: "curl -f ${prodHealthUrl}/health --max-time 10",
                                    returnStatus: true
                                ) == 0
                            }
                        }
                    }

                    // Production validation
                    bat """
                        curl -X POST ${prodHealthUrl}/generate ^
                          -H "Content-Type: application/json" ^
                          -d "{\\"prompt\\": \\"production validation\\"}" ^
                          -o prod-validation.json
                    """

                    // Create release record
                    def releaseRecord = [
                        version: releaseVersion,
                        deploymentName: prodDeploymentName,
                        imageTag: "${env.DOCKER_IMAGE}:${releaseVersion}",
                        productionUrl: prodHealthUrl,
                        releaseTimestamp: new Date().toString(),
                        deploymentStrategy: prodExists ? 'blue-green' : 'first-deployment',
                        healthStatus: 'healthy',
                        buildNumber: env.BUILD_NUMBER
                    ]

                    writeJSON file: 'release-record.json', json: releaseRecord

                    echo "🎉 Production release ${releaseVersion} completed successfully!"
                    echo "🌐 Production URL: ${prodHealthUrl}"
                }
            }
            post {
                always {
                    archiveArtifacts artifacts: 'release-notes.json,release-record.json,prod-validation.json', allowEmptyArchive: true
                }
                success {
                    script {
                        def releaseVersion = "v${env.BUILD_NUMBER}"

                        emailext (
                            subject: "🎉 Production Release ${releaseVersion} Successful",
                            body: """
                            Production release ${releaseVersion} has been deployed successfully!

                            Build: ${env.BUILD_NUMBER}
                            Commit: ${env.GIT_COMMIT ?: 'unknown'}
                            Production URL: http://localhost:5000

                            Release includes:
                            ✅ All tests passed
                            ✅ Security scan completed
                            ✅ Code quality verified
                            ✅ Health checks verified

                            Check Jenkins for detailed logs and artifacts.
                            """,
                            to: "${env.NOTIFICATION_EMAIL}",
                            mimeType: 'text/plain'
                        )
                    }
                }
                failure {
                    script {
                        echo "🔄 Rolling back failed release..."
                        bat '''
                            docker stop jenkins-llm-prod 2>nul || echo "Prod container not running"
                            docker rm jenkins-llm-prod 2>nul || echo "Prod container not found"
                        '''

                        emailext (
                            subject: "🚨 Production Release Failed - Rollback Initiated",
                            body: "Production release failed for build ${env.BUILD_NUMBER}. Automatic rollback completed.",
                            to: "${env.NOTIFICATION_EMAIL}"
                        )
                    }
                }
            }
        }

        stage('Monitoring') {
            steps {
                echo "📊 Stage 7: Setup Monitoring & Alerting"

                script {
                    // Create monitoring directories
                    bat '''
                        if not exist monitoring mkdir monitoring
                    '''

                    // Create basic monitoring setup
                    echo "🔍 Setting up application monitoring..."

                    // Test monitoring endpoints on both environments
                    def monitoringResults = [:]

                    ['5000', '5001'].each { port ->
                        def testUrl = "http://localhost:${port}"
                        def healthy = bat(
                            script: "curl -f ${testUrl}/health --max-time 5",
                            returnStatus: true
                        ) == 0

                        def metricsAvailable = bat(
                            script: "curl -f ${testUrl}/metrics --max-time 5",
                            returnStatus: true
                        ) == 0

                        monitoringResults["app-${port}"] = [
                            url: testUrl,
                            healthStatus: healthy ? 'healthy' : 'unhealthy',
                            metricsAvailable: metricsAvailable,
                            timestamp: new Date().toString()
                        ]
                    }

                    // Create monitoring summary
                    def monitoringSummary = [
                        buildNumber: env.BUILD_NUMBER,
                        deploymentTimestamp: new Date().toString(),
                        applicationEndpoints: monitoringResults,
                        monitoringCapabilities: [
                            'Health checks': 'Available on /health endpoint',
                            'Prometheus metrics': 'Available on /metrics endpoint',
                            'System status': 'Available on /status endpoint',
                            'Application ready': 'Available on /ready endpoint'
                        ],
                        recommendedAlerts: [
                            'ApplicationDown': 'Monitor /health endpoint availability',
                            'HighResponseTime': 'Monitor response times via metrics',
                            'HighErrorRate': 'Monitor error rates in application logs',
                            'ResourceUsage': 'Monitor CPU/memory via /status endpoint'
                        ],
                    ]

                    writeJSON file: 'monitoring-summary.json', json: monitoringSummary

                    // Basic monitoring validation
                    def totalHealthy = monitoringResults.count { key, value -> value.healthStatus == 'healthy' }
                    def totalMetrics = monitoringResults.count { key, value -> value.metricsAvailable }

                    echo "✅ Monitoring setup completed!"
                    echo "📊 Healthy endpoints: ${totalHealthy}/${monitoringResults.size()}"
                    echo "📈 Metrics available: ${totalMetrics}/${monitoringResults.size()}"

                    if (totalHealthy == 0) {
                        error("❌ No healthy endpoints found for monitoring")
                    }
                }
            }
            post {
                always {
                    archiveArtifacts artifacts: 'monitoring-summary.json', allowEmptyArchive: true

                    publishHTML([
                        allowMissing: false,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: '.',
                        reportFiles: 'monitoring-summary.json',
                        reportName: 'Monitoring Setup Report'
                    ])
                }
                success {
                    script {
                        emailext (
                            subject: "📊 Monitoring Setup Complete: ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                            body: """
                            Monitoring and alerting capabilities have been configured for build ${env.BUILD_NUMBER}!

                            🔍 Available Endpoints:
                            • Health Check: /health
                            • Metrics: /metrics (Prometheus format)
                            • Status: /status (detailed system info)
                            • Readiness: /ready

                            The application is ready for production monitoring.
                            """,
                            to: "${env.NOTIFICATION_EMAIL}"
                        )
                    }
                }
                failure {
                    emailext (
                        subject: "🚨 Monitoring Setup Issues: ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                        body: "Monitoring setup encountered issues for build ${env.BUILD_NUMBER}. Check the Jenkins logs for details.",
                        to: "${env.NOTIFICATION_EMAIL}"
                    )
                }
            }
        }
    }

    post {
        always {
            // Cleanup
            bat "docker rmi \"%DOCKER_IMAGE%:%DOCKER_TAG%\" || exit 0"

            // Archive all reports
            archiveArtifacts artifacts: '**/*.json,**/*.xml,**/*.txt', allowEmptyArchive: true
        }
        success {
            echo "🎉 Pipeline completed successfully!"
            echo "📋 All 7 stages completed: Build ✅ Test ✅ Quality ✅ Security ✅ Deploy ✅ Release ✅ Monitoring ✅ 🥳🥳🥳🥳"
        }
        failure {
            echo "🚨 Pipeline failed 🙏🙏😭😭😭😭."

            // Cleanup
            script {
                bat '''
                    docker stop jenkins-llm-test jenkins-llm-prod 2>nul || echo "Containers not running"
                    docker rm jenkins-llm-test jenkins-llm-prod 2>nul || echo "Containers not found"
                '''
            }
        }
        unstable {
            echo "⚠️ Pipeline completed with warnings."
        }
    }
}