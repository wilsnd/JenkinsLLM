FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

# Install deps
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project code
COPY . .

# For Flask
EXPOSE 5000