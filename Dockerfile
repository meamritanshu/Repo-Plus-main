# Use official Python image
FROM python:3.11-slim

WORKDIR /app

# Install git (needed for GitPython to clone repos)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ .

# Create required directories
RUN mkdir -p data/temp_repos app/static/generated_graphs

# Expose Flask port
EXPOSE 5000

ENV FLASK_DEBUG=false

CMD ["python", "run.py"]
