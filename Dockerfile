FROM python:3.9-slim

# Install system deps
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python deps
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project code
COPY . .

# Create dir
RUN mkdir -p /app/monitoring /app/logs /app/test-results

# Set the environment variables
ENV PYTHONPATH=/app
ENV FLASK_APP=inference/flask_web.py
ENV ENVIRONMENT=production

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# For flask
EXPOSE 5000

# Default command
CMD ["python", "inference/flask_web.py"]