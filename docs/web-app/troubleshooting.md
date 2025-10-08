# Troubleshooting Guide

This guide helps you resolve common issues with the Cortex Flow web application.

## Table of Contents

1. [Application Won't Start](#application-wont-start)
2. [Agent Issues](#agent-issues)
3. [Workflow Problems](#workflow-problems)
4. [UI/Frontend Issues](#uifrontend-issues)
5. [API Errors](#api-errors)
6. [Performance Issues](#performance-issues)
7. [Database/Storage Issues](#databasestorage-issues)
8. [Environment Issues](#environment-issues)

## Application Won't Start

### Backend Server Won't Start

**Error:** `ModuleNotFoundError: No module named 'fastapi'`

**Solution:**
```bash
# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

**Error:** `Address already in use`

**Solution:**
```bash
# Find process using port 8002
lsof -i :8002  # Linux/Mac
netstat -ano | findstr :8002  # Windows

# Kill the process
kill -9 <PID>  # Linux/Mac
taskkill /PID <PID> /F  # Windows
```

**Error:** `ImportError: cannot import name 'ProcessManager'`

**Solution:**
```bash
# Ensure PYTHONPATH includes project root
export PYTHONPATH=/path/to/cortex-flow:$PYTHONPATH

# Or run from project root
cd /path/to/cortex-flow
python servers/editor_server.py
```

### Frontend Won't Build

**Error:** `npm: command not found`

**Solution:**
```bash
# Install Node.js 18+ from https://nodejs.org/
# Or use nvm:
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 18
nvm use 18
```

**Error:** `Module not found: Can't resolve '@tanstack/react-query'`

**Solution:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Error:** Build fails with memory error

**Solution:**
```bash
# Increase Node memory limit
export NODE_OPTIONS="--max-old-space-size=4096"
npm run build
```

## Agent Issues

### Agents Won't Start

**Problem:** Clicking agent badge does nothing, stays gray

**Diagnostic Steps:**

1. **Check logs:**
```bash
tail -n 50 logs/agent_name.log
```

2. **Common causes and fixes:**

**Missing API Keys:**
```bash
# Check .env file
cat .env | grep API_KEY

# Add missing keys
echo "OPENAI_API_KEY=your-key-here" >> .env
```

**Port already in use:**
```bash
# Check port usage
lsof -i :8001

# Solution 1: Kill existing process
kill -9 <PID>

# Solution 2: Change port in config
# Edit utils/process_manager.py
AGENTS_CONFIG = {
    "researcher": {"port": 8011, ...}  # Change port
}
```

**Python path issues:**
```bash
# Verify Python version
python --version  # Should be 3.10+

# Check virtual environment
which python  # Should point to .venv/bin/python
```

### Agents Start Then Stop Immediately

**Problem:** Agent badge turns green briefly then gray

**Check import errors:**
```bash
# Test agent directly
cd /path/to/cortex-flow
python servers/researcher_server.py
```

**Common import error fixes:**

```bash
# Missing dependencies
pip install langchain langchain-openai langgraph

# PYTHONPATH not set (the ProcessManager should handle this)
export PYTHONPATH=/path/to/cortex-flow:$PYTHONPATH
```

### Cannot Stop Agent

**Problem:** Agent won't stop when clicked

**Force stop:**
```bash
# Find process
ps aux | grep researcher_server

# Force kill
kill -9 <PID>

# Remove PID file
rm logs/researcher.pid
```

**Clean restart:**
```bash
# Stop all Python processes (careful!)
pkill -f python

# Remove all PID files
rm logs/*.pid

# Restart editor server
python servers/editor_server.py
```

## Workflow Problems

### Workflow Won't Execute

**Error:** "No agents available"

**Solution:**
1. Start required agents via status bar
2. Verify agents are running:
```bash
curl http://localhost:8002/api/processes/status
```

**Error:** "Workflow validation failed"

**Check:**
- All nodes are connected
- No circular dependencies
- Required parameters are provided
- Agent names are correct

### Workflow Execution Hangs

**Problem:** Workflow starts but never completes

**Diagnostics:**
```bash
# Check agent logs
tail -f logs/supervisor.log

# Monitor process resources
htop  # or top
```

**Common causes:**
- Agent timeout too short
- Infinite loop in workflow
- API rate limiting

**Solutions:**
```python
# Increase timeout in workflow config
{
    "timeout": 600,  # 10 minutes
    "max_iterations": 10
}
```

### Natural Language Generation Fails

**Error:** "Failed to generate workflow from description"

**Solutions:**
1. Be more specific in description
2. Use supported action words: "research", "analyze", "write", "summarize"
3. Break complex workflows into steps
4. Check LLM API key is valid

## UI/Frontend Issues

### Page Not Loading

**White screen or 404:**

1. **Check backend is running:**
```bash
curl http://localhost:8002/api/health
```

2. **Rebuild frontend:**
```bash
cd frontend
npm run build
```

3. **Clear browser cache:**
- Chrome: Cmd/Ctrl + Shift + R
- Firefox: Cmd/Ctrl + Shift + R
- Safari: Cmd + Option + E

### Components Not Updating

**Problem:** Status bar stuck, data not refreshing

**Solutions:**

1. **Force refresh:**
- Click 🔄 Refresh button
- Reload page (F5)

2. **Check browser console:**
- Open DevTools (F12)
- Look for red errors in Console
- Check Network tab for failed requests

3. **React Query cache issue:**
```javascript
// In browser console
localStorage.clear()
location.reload()
```

### Workflow Editor Not Working

**Can't drag nodes:**
- Ensure not in read-only mode
- Check browser compatibility (Chrome/Firefox/Safari/Edge)
- Disable browser extensions

**Connections not drawing:**
- Click and hold on output port
- Drag to input port (not the node itself)
- Ensure nodes are compatible

## API Errors

### 404 Not Found

**Check URL structure:**
```bash
# Correct
curl http://localhost:8002/api/projects

# Incorrect (missing /api)
curl http://localhost:8002/projects
```

### 500 Internal Server Error

**Check server logs:**
```bash
# If running in terminal, check output
# Or check log file
tail -n 100 logs/editor.log
```

**Common causes:**
- Database connection failed
- Missing environment variables
- Corrupted project files

### 422 Validation Error

**Invalid request format:**
```bash
# Check request body
curl -X POST http://localhost:8002/api/processes/start \
  -H "Content-Type: application/json" \
  -d '{"name": "researcher"}'  # Correct format
```

### CORS Errors

**Error:** "Access to fetch at 'http://localhost:8002' from origin 'http://localhost:3000' has been blocked by CORS"

**Solution:**
Ensure backend CORS is configured:
```python
# In editor_server.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specific origins
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Performance Issues

### Slow Application

**Frontend optimization:**
```bash
# Production build
cd frontend
npm run build

# Serve optimized build
npm install -g serve
serve -s dist -p 3000
```

**Backend optimization:**
```python
# Use production server
uvicorn servers.editor_server:app --workers 4
```

### High Memory Usage

**Monitor processes:**
```bash
# Check memory usage
ps aux | grep python | awk '{sum+=$6} END {print sum/1024 " MB"}'

# Limit agent memory
ulimit -v 500000  # 500MB limit
```

**Clear logs:**
```bash
# Truncate large log files
truncate -s 0 logs/*.log

# Or archive old logs
tar -czf logs_backup_$(date +%Y%m%d).tar.gz logs/*.log
truncate -s 0 logs/*.log
```

### Slow Workflow Execution

**Optimize LLM calls:**
- Use faster models for simple tasks
- Implement caching for repeated queries
- Parallelize independent operations

## Database/Storage Issues

### Project Data Lost

**Backup location:**
```bash
# Default project storage
ls -la projects/
```

**Recovery:**
```bash
# Restore from backup
cp -r projects_backup/* projects/
```

### Corrupted Project File

**Fix JSON syntax:**
```bash
# Validate JSON
python -m json.tool projects/my_project/project.json

# Fix common issues
# - Remove trailing commas
# - Ensure quotes are proper
# - Check bracket matching
```

## Environment Issues

### Missing Environment Variables

**Check current environment:**
```bash
# List all env vars
printenv | grep -E "API_KEY|LANGCHAIN"

# Source .env file
export $(cat .env | xargs)
```

**Required variables:**
```bash
# Minimum required
OPENAI_API_KEY=sk-...
# or
ANTHROPIC_API_KEY=sk-ant-...

# Optional but recommended
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls__...
LANGCHAIN_PROJECT=cortex-flow
```

### Python Version Issues

**Check Python version:**
```bash
python --version  # Should be 3.10+
```

**Using pyenv to manage versions:**
```bash
# Install Python 3.10
pyenv install 3.10.11
pyenv local 3.10.11

# Create new venv with correct version
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Virtual Environment Issues

**Recreate virtual environment:**
```bash
# Backup current environment
pip freeze > requirements_backup.txt

# Remove and recreate
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Getting Help

### Diagnostic Information to Collect

When reporting issues, include:

1. **System info:**
```bash
python --version
node --version
npm --version
uname -a  # OS info
```

2. **Error messages:**
- Complete error traceback
- Browser console errors
- Network request failures

3. **Logs:**
```bash
# Recent editor logs
tail -n 100 logs/editor.log

# Agent logs if relevant
tail -n 100 logs/*.log
```

4. **Configuration:**
- Sanitized .env (remove keys)
- Modified configuration files
- Custom workflows/prompts

### Debug Mode

Enable debug logging:

```python
# In servers/editor_server.py
import logging
logging.basicConfig(level=logging.DEBUG)

# Or via environment
export LOG_LEVEL=DEBUG
```

### Community Support

- GitHub Issues: Report bugs and request features
- GitHub Discussions: Ask questions and share tips
- Documentation: Check `/docs` for detailed guides

## Quick Fixes Checklist

When things go wrong, try these in order:

1. ✅ **Restart the editor server**
2. ✅ **Clear browser cache and reload**
3. ✅ **Check all required services are running**
4. ✅ **Verify environment variables are set**
5. ✅ **Review recent logs for errors**
6. ✅ **Ensure ports are not blocked**
7. ✅ **Rebuild frontend if UI issues**
8. ✅ **Reinstall dependencies if import errors**
9. ✅ **Check disk space and memory**
10. ✅ **Revert recent changes if applicable**

---

Still having issues? Check the [FAQ](./faq.md) or file an issue on GitHub with diagnostic information.