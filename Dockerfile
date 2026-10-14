# ====================================================================
# RefundShield AI - Production Cloud Dockerfile
# Optimized for Render, Railway, AWS ECS, GCP Cloud Run, and Fly.io
# ====================================================================

FROM python:3.10-slim AS base

# Set environment variables for high performance
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8000

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application source code
COPY . .

# Create non-root user for security best practices
RUN addgroup --system appgroup && adduser --system --group appgroup && \
    mkdir -p data data/processed saved_models && \
    chown -R appgroup:appgroup /app

USER appgroup

# Expose server port
EXPOSE 8000

# Health check to ensure 24/7 reliability
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Production Gunicorn process manager with Uvicorn workers
CMD exec gunicorn main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:${PORT} \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
