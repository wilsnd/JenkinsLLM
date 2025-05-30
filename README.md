# JenkinsLLM - DevOps Pipeline Project

## Project Overview 
This is a LLM project that uses data from CommonCrawl to train a PyTorch GPT model that can generate results from prompts. I used Flask for the inference, and it has a basic GPT-like interface which enables the user to converse with the AI. The model took 9 hours to train and was able to complete sentences form basic prompts.

1. **Name**: JenkinsLLM 
2. **Tech Stack**: Python, PyTorch, Jenkins, Docker, SonarQube, Prometheus
3. **Stages**: 7 (Build, Test, Quality, Security, Deploy, Release, Monitoring)

## Features 
- Large Language Model that can complete sentences from basic prompt
- 7-stage DevOps pipeline that is automatic
- Security scanning with Bandit and Safety
- SonarQube for Code Quality analysis
- Production monitoring with Prometheus

## Technology Stack 

| Category | Technologies | Use |
|----------|--------------|-----|
| CI/CD | Jenkins | Pipeline |
| Containerization | Docker | Package application |
| Code Quality | SonarQube | Static analysis & coverage |
| Security | Safety, Bandit | Scan dependencies & vulnerabilities |
| Monitoring | Prometheus | Collect metrics and data |
| Application | Python, PyTorch, Flask | Training & inference |
| Testing | Unittest | Test code |

## Pipeline Implementation 

### 1. Build Stage 
Packages the entire project into a docker image with health checks and version tagging.

### 2. Test Stage 
Conducts python class test with unittest and coverage test.

### 3. Code Quality Stage 
Uses SonarQube to check static codes and look for any issues or basic vulnerabilities.

### 4. Security Stage 
Uses Safety and Bandit to conduct security test on the code. Checks vulnerabilities with dependencies and common security issues.

### 5. Deployment Stage 
Uses docker to deploy the test website on `localhost:5001` with health checks and logging.

### 6. Release Stage 
Releases the production version on `localhost:5000`. Creates release notes and sends email notifications. Uses simplified Blue-Green deployment strategy.

### 7. Monitoring Stage 
Provides 3 endpoints to monitor and check website status:
- `/health`: Application health
- `/metrics`: Prometheus metrics  
- `/status`: System resource

## Technical Features 

### LLM Architecture 
- **Model Size**: 9M parameters
- **Architecture**: 3 layers, 4 attention heads, 512 hidden dimensions 
- **Training Data**: 10GB of CommonCrawl Data cleaned to 1GB training data 
- **Inference**: Flask API

### LLM Pipeline 
Data processing pipeline with 5 stages: Data Cleaning → Preparation → Model Creation → Training → Inference

### CommonCrawl Data Cleaning 
3 main steps during data cleaning process:
1. Length Filter, Language Detection, Encoding Validation 
2. Line diversity, Word diversity, Sentence, Content ratio 
3. Similar duplicates, Very similar duplicates, Cross document 

This reduces the data by 90%. From 10GB of raw data to 1GB cleaned data.

### Model Configuration
```python
# Model size  
self.vocab_size = 10000  
self.d_model = 512  
self.n_heads = 4  
self.n_layers = 3  
self.d_ff = int(self.d_model * 2.7)  # SwiGLU activation
self.max_seq_len = 32  

# Training  
self.dropout = 0.005  
self.learning_rate = 0.0004  
self.batch_size = 128  
```

## Installation & Usage

### Prerequisites
- Docker
- Jenkins
- SonarQube Server

### Quick Start
```bash
# Clone repository
git clone https://github.com/wilsnd/JenkinsLLM

# Build and run with Docker
docker-compose up -d

# Access application
# Test environment: http://localhost:5001
# Production: http://localhost:5000
```

### Jenkins Pipeline
The Jenkins pipeline automatically triggers on code changes and runs through all 7 stages with email notifications.

## Future Improvements
- Fix the SonarQube quality issues 
- Try Kubernetes 
- Optimize the code, mainly the preparation step to make it more efficient
- Train with more data 
- Improve the model 
- Package only the necessary files
