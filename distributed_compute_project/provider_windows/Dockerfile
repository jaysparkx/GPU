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

COPY provider_client_windows.py .

ENV DOCKER_ENV=true
ENV PYTHONUNBUFFERED=1

CMD ["python", "provider_client_windows.py"] 