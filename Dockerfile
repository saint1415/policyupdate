# PolicyUpdate GRC Platform
# Multi-stage build for production deployment

# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Production stage
FROM python:3.11-slim

# Create non-root user for security
RUN groupadd -r policyupdate && useradd -r -g policyupdate policyupdate

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels from builder and install
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache /wheels/*

# Copy application code
COPY src/ ./src/
COPY config/ ./config/
COPY policies/ ./policies/
COPY setup.py .
COPY requirements.txt .

# Create directories for data and output
RUN mkdir -p /app/data /app/output /app/logs && \
    chown -R policyupdate:policyupdate /app

# Install the package
RUN pip install -e .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV POLICYUPDATE_LOG_LEVEL=INFO
ENV POLICYUPDATE_LOG_FILE=/app/logs/policyupdate.log
ENV FLASK_APP=src.web.app:create_app

# Switch to non-root user
USER policyupdate

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/api/health', timeout=5)" || exit 1

# Default command - run web server
CMD ["python", "-m", "gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "src.web.app:create_app()"]
