FROM python:3.9-slim

# Install system deps
RUN apt-get update && apt-get install -y \
    bash \
    build-essential \
    curl \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Requirements
COPY requirements.txt .

# Install Python deps
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project code
COPY . .

# WSGI entry point
RUN echo 'from inference.flask_web import create_app\napp = create_app()\nif __name__ == "__main__":\n    app.run(host="0.0.0.0", port=5000)' > wsgi.py

# Create directories
RUN mkdir -p /app/models/all_models \
             /app/processed_data \
             /app/monitoring \
             /app/logs \
             /app/test-results

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
CMD ["sh", "-c", "if [ \"$ENVIRONMENT\" = \"production\" ]; then gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 60 wsgi:app; else python inference/flask_web.py; fi"]