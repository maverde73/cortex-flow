# Multi-stage Dockerfile for Cortex Flow agents

# Stage 1: Build stage
FROM python:3.12-slim as builder

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime stage
FROM python:3.12-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY agents/ ./agents/
COPY servers/ ./servers/
COPY tools/ ./tools/
COPY schemas/ ./schemas/
COPY utils/ ./utils/
COPY config.py .

# Make sure scripts are in PATH
ENV PATH=/root/.local/bin:$PATH

# Expose port (will be overridden by docker-compose)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command (will be overridden by docker-compose)
CMD ["python", "servers/supervisor_server.py"]
