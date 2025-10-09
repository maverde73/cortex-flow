# Railway Deployment Guide for MCP Servers

## Overview

This guide provides comprehensive instructions for deploying exported MCP workflow servers to Railway.app, a modern Platform-as-a-Service (PaaS) that makes it easy to deploy Docker containers with automatic scaling, SSL certificates, and integrated monitoring.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Preparation Steps](#preparation-steps)
3. [Deployment Methods](#deployment-methods)
4. [Configuration](#configuration)
5. [Monitoring & Maintenance](#monitoring--maintenance)
6. [Troubleshooting](#troubleshooting)
7. [Cost Optimization](#cost-optimization)
8. [Security Best Practices](#security-best-practices)

## Prerequisites

### Railway Account Setup
1. Create an account at [railway.app](https://railway.app)
2. Verify your email address
3. Add a payment method (required for production deployments)

### Local Requirements
- Docker installed locally for testing
- Git installed and configured
- Railway CLI (optional but recommended):
  ```bash
  npm install -g @railway/cli
  ```

### Project Requirements
- Exported MCP server in a dedicated folder
- Working Dockerfile and docker-compose.yml
- Environment variables configured
- Tested locally with Docker

## Preparation Steps

### 1. Test Local Docker Build

Before deploying to Railway, ensure your Docker image builds and runs correctly:

```bash
cd export/research_and_report

# Build the image
docker build -t mcp-research-report:test .

# Test with required environment variables
docker run -p 8808:8808 \
  -e OPENAI_API_KEY="your-key" \
  -e MCP_PORT=8808 \
  mcp-research-report:test
```

### 2. Optimize Dockerfile for Production

Review and update your Dockerfile for production deployment:

```dockerfile
# Use specific Python version for consistency
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:${MCP_PORT:-8808}/health')" || exit 1

# Use environment variable for port
EXPOSE ${MCP_PORT:-8808}

# Run the application
CMD ["python", "server.py", "--transport", "streamable-http"]
```

### 3. Create Railway Configuration Files

#### railway.json
Create a `railway.json` file in your project root:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "numReplicas": 1,
    "healthcheckPath": "/health",
    "healthcheckTimeout": 10,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 3
  }
}
```

#### railway.toml
Create a `railway.toml` file for build configuration:

```toml
[build]
builder = "dockerfile"
dockerfilePath = "Dockerfile"

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 10
numReplicas = 1
region = "us-west1"

[[services]]
name = "mcp-research-report"
port = 8808
```

### 4. Update server.py for Railway

Ensure your `server.py` properly handles Railway's environment:

```python
import os

# Railway provides PORT environment variable
PORT = int(os.getenv("PORT", os.getenv("MCP_PORT", "8808")))
HOST = "0.0.0.0"  # Required for Railway

# Update FastMCP initialization
mcp = FastMCP(
    name="research-report-workflow",
    instructions=WORKFLOW_DESCRIPTION,
    host=HOST,
    port=PORT
)

# Add health check endpoint
@mcp.tool()
def health():
    """Health check endpoint for Railway"""
    return {"status": "healthy", "service": "mcp-research-report"}
```

## Deployment Methods

### Method 1: GitHub Integration (Recommended)

#### Step 1: Push to GitHub

```bash
# Initialize git repository
cd export/research_and_report
git init
git add .
git commit -m "Initial MCP server export"

# Create GitHub repository and push
gh repo create mcp-research-report --private
git remote add origin https://github.com/YOUR_USERNAME/mcp-research-report.git
git push -u origin main
```

#### Step 2: Connect to Railway

1. Log in to Railway dashboard
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Authorize Railway to access your GitHub
5. Select the `mcp-research-report` repository
6. Railway will auto-detect the Dockerfile

#### Step 3: Configure Environment Variables

In Railway dashboard:
1. Click on your service
2. Go to "Variables" tab
3. Add required variables:
   - `OPENAI_API_KEY`
   - `ANTHROPIC_API_KEY`
   - `GROQ_API_KEY`
   - `LOG_LEVEL`
   - Any other API keys

### Method 2: Railway CLI Deployment

#### Step 1: Login and Initialize

```bash
# Login to Railway
railway login

# Initialize new project
cd export/research_and_report
railway init
```

#### Step 2: Link and Deploy

```bash
# Link to a new Railway project
railway link

# Set environment variables
railway variables set OPENAI_API_KEY="your-key"
railway variables set LOG_LEVEL="INFO"

# Deploy
railway up
```

#### Step 3: Monitor Deployment

```bash
# Watch logs
railway logs -f

# Get deployment URL
railway open
```

### Method 3: Docker Hub Integration

#### Step 1: Build and Push to Docker Hub

```bash
# Build for multiple platforms
docker buildx build --platform linux/amd64,linux/arm64 \
  -t yourusername/mcp-research-report:latest \
  --push .
```

#### Step 2: Deploy from Docker Hub

1. In Railway dashboard, click "New Project"
2. Select "Deploy from Docker Image"
3. Enter image: `yourusername/mcp-research-report:latest`
4. Configure environment variables
5. Deploy

## Configuration

### Environment Variables

Railway provides several built-in variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `PORT` | Port Railway expects your app to listen on | `8808` |
| `RAILWAY_ENVIRONMENT` | Current environment | `production` |
| `RAILWAY_STATIC_URL` | Your service's public URL | `https://app.railway.app` |
| `RAILWAY_GIT_COMMIT_SHA` | Current deployment's commit | `abc123...` |

### Custom Domain Setup

1. In Railway dashboard, go to "Settings"
2. Click "Generate Domain" for a railway.app subdomain
3. Or add custom domain:
   ```
   Settings → Domains → Add Custom Domain
   ```
4. Update your DNS with provided CNAME record

### Scaling Configuration

Configure in `railway.json`:

```json
{
  "deploy": {
    "numReplicas": 2,
    "region": "us-west1",
    "maxConcurrency": 100,
    "cpuBalancing": true
  }
}
```

### Resource Limits

Set resource limits in Railway dashboard:

1. Go to service Settings
2. Under "Resources":
   - Memory: 512MB - 8GB
   - CPU: 0.5 - 32 vCPUs
   - Disk: 1GB - 100GB

## Monitoring & Maintenance

### Logs

View logs through multiple channels:

```bash
# CLI
railway logs -f

# Dashboard
# Navigate to Deployments → Logs

# Programmatic (in your app)
import logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Metrics

Railway provides built-in metrics:
- CPU usage
- Memory usage
- Network I/O
- Request count
- Response time

Access via: Service → Metrics tab

### Alerts

Configure alerts in Railway:

1. Go to Settings → Notifications
2. Add webhook or email
3. Configure triggers:
   - Deployment failures
   - High resource usage
   - Health check failures

### Backup Strategy

```bash
# Backup environment variables
railway variables export > .env.backup

# Backup deployment config
railway info --json > deployment-backup.json
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Port Binding Issues

**Problem**: "Error: listen EADDRINUSE"

**Solution**:
```python
# Use Railway's PORT variable
PORT = int(os.getenv("PORT", "8808"))
```

#### 2. Memory Exceeded

**Problem**: "Container exceeded memory limit"

**Solution**:
- Increase memory limit in Settings
- Optimize code for memory usage
- Add pagination to large data operations

#### 3. Build Failures

**Problem**: "Build failed"

**Solution**:
```bash
# Test locally first
docker build --no-cache -t test .

# Check logs
railway logs --build
```

#### 4. Environment Variable Issues

**Problem**: "KeyError: 'OPENAI_API_KEY'"

**Solution**:
```python
# Add defaults and validation
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is required")
```

#### 5. Timeout Issues

**Problem**: "Request timeout"

**Solution**:
```python
# Increase timeout settings
WORKFLOW_TIMEOUT = int(os.getenv("WORKFLOW_TIMEOUT", "600"))
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "300"))
```

### Debug Mode

Enable debug mode for troubleshooting:

```python
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

if DEBUG:
    import debugpy
    debugpy.listen(("0.0.0.0", 5678))
    logging.getLogger().setLevel(logging.DEBUG)
```

## Cost Optimization

### Railway Pricing

- **Hobby Plan**: $5/month (includes $5 credits)
- **Pro Plan**: $20/month (includes $20 credits)
- **Usage-based**: $0.000463/GB-minute RAM, $0.000463/vCPU-minute

### Optimization Strategies

1. **Right-size resources**:
   ```json
   {
     "deploy": {
       "memory": "512MB",
       "cpu": "0.5"
     }
   }
   ```

2. **Use sleep/wake on low traffic**:
   ```json
   {
     "deploy": {
       "sleepTimeout": 300,
       "minReplicas": 0,
       "maxReplicas": 3
     }
   }
   ```

3. **Implement caching**:
   ```python
   from functools import lru_cache

   @lru_cache(maxsize=100)
   def expensive_operation(param):
       # Cache results
       pass
   ```

4. **Optimize Docker image**:
   ```dockerfile
   # Multi-stage build
   FROM python:3.11-slim as builder
   COPY requirements.txt .
   RUN pip install --user -r requirements.txt

   FROM python:3.11-slim
   COPY --from=builder /root/.local /root/.local
   ```

## Security Best Practices

### 1. Secrets Management

Never commit secrets. Use Railway's encrypted variables:

```bash
# Set sensitive variables
railway variables set OPENAI_API_KEY="sk-..." --secret
```

### 2. Network Security

Configure allowed origins:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_methods=["POST"],
    allow_headers=["*"],
)
```

### 3. Rate Limiting

Implement rate limiting:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per hour"]
)
```

### 4. Authentication

Add API key authentication:

```python
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != os.getenv("API_KEY"):
        raise HTTPException(status_code=401)
    return credentials.credentials
```

### 5. Input Validation

Validate all inputs:

```python
from pydantic import BaseModel, validator

class WorkflowRequest(BaseModel):
    topic: str

    @validator('topic')
    def validate_topic(cls, v):
        if len(v) > 1000:
            raise ValueError("Topic too long")
        return v
```

## Appendix: Quick Reference

### Essential Commands

```bash
# Deploy
railway up

# View logs
railway logs -f

# Set variable
railway variables set KEY=value

# Restart service
railway restart

# Remove deployment
railway down
```

### Environment File Template

Create `.env.railway` for local testing:

```env
# Railway Environment
PORT=8808
RAILWAY_ENVIRONMENT=production

# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GROQ_API_KEY=gsk_...

# Configuration
LOG_LEVEL=INFO
WORKFLOW_TIMEOUT=600
LLM_TIMEOUT=300
MAX_WORKERS=4

# Features
ENABLE_CACHE=true
ENABLE_METRICS=true
DEBUG=false
```

### Monitoring Script

Create `scripts/monitor.sh`:

```bash
#!/bin/bash
# Monitor Railway deployment

while true; do
    echo "=== $(date) ==="
    railway status
    railway logs --last 10
    sleep 60
done
```

## Next Steps

1. **Test locally** with Docker
2. **Create GitHub repository** for your exported server
3. **Deploy to Railway** using GitHub integration
4. **Configure environment variables** in Railway dashboard
5. **Set up custom domain** if needed
6. **Monitor deployment** and optimize as needed
7. **Implement additional security** measures
8. **Set up CI/CD** pipeline for automatic deployments

## Support Resources

- [Railway Documentation](https://docs.railway.app)
- [Railway Discord](https://discord.gg/railway)
- [Status Page](https://status.railway.app)
- [Pricing Calculator](https://railway.app/pricing)

---

*This guide will be updated as Railway adds new features. Last updated: January 2025*