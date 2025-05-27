#!/bin/bash
# Local pipeline testing script

echo "Testing Build Stage"
docker build -t jenkins-llm:test .

echo "Testing Unit Tests"
docker run --rm -v $(pwd):/app -w /app jenkins-llm:test python -m pytest tests/unit/ -v

echo "Testing Security Scan"
docker run --rm -v $(pwd):/app -w /app jenkins-llm:test pip install safety bandit
docker run --rm -v $(pwd):/app -w /app jenkins-llm:test safety check || echo "Safety scan completed"
docker run --rm -v $(pwd):/app -w /app jenkins-llm:test bandit -r . -x "*/tests/*" || echo "Bandit scan completed"

echo "Testing App Deployment"
docker run -d --name test-app -p 5000:5000 jenkins-llm:test

echo "Waiting for app to start"
sleep 10

echo "Testing Health Check"
curl -f http://localhost:5000/health || echo "Health check failed"

echo "Testing Metrics"
curl -f http://localhost:5000/metrics || echo "Metrics endpoint failed"

echo "Cleanup"
docker stop test-app
docker rm test-app
docker rmi jenkins-llm:test

echo "Pipeline test completed!!!"
