FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    python3-dev \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install packages with specific versions to ensure compatibility
RUN pip install --no-cache-dir werkzeug==2.0.2 && \
    pip install --no-cache-dir flask==2.0.1 && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY head_node.py .

# Expose ports
EXPOSE 5000
EXPOSE 8265
EXPOSE 6379

# Environment variables that can be overridden
ENV REDIS_HOST=redis
ENV REDIS_PORT=6379
ENV RAY_REDIS_PASSWORD=5241590000000000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5000/health || exit 1

CMD ["python", "head_node.py"] 