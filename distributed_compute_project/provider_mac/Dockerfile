FROM python:3.9-slim

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY provider_client_mac.py .

# Set environment variable to bypass OS check
ENV DOCKER_ENV=true

ENV PYTHONUNBUFFERED=1

# Run the provider
CMD ["python", "provider_client_mac.py"] 