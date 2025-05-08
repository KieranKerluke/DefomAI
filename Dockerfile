FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ENV_MODE="production" \
    PYTHONPATH=/app/backend

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user and log directory
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/backend/logs && \
    chown -R appuser:appuser /app

# Copy only requirements and install dependencies
COPY --chown=appuser:appuser backend/requirements.txt /app/backend/
WORKDIR /app/backend
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy backend code
COPY --chown=appuser:appuser backend/ /app/backend/

# Switch to non-root user
USER appuser

# Expose app port (used by Railway)
EXPOSE ${PORT:-8000}

# Gunicorn launch (minimal resource usage for Railway)
CMD ["sh", "-c", "gunicorn api:app \
  --workers 1 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:${PORT:-8000} \
  --timeout 600 \
  --log-level info \
  --access-logfile - \
  --error-logfile -"]