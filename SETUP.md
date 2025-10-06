# Cortex Flow - Setup Guide

Complete step-by-step guide to get Cortex Flow up and running.

## Prerequisites

- **Python 3.10+** (tested with Python 3.12)
- **pip** and **venv** installed
- **OpenAI API account** with credits
- **Tavily API account** (free tier available)

---

## Step 1: Get Your API Keys

### OpenAI API Key (REQUIRED)

1. Go to [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Sign in or create an account
3. Click **"Create new secret key"**
4. Copy the key (starts with `sk-...`)
5. **Important**: Make sure you have credits in your OpenAI account

### Tavily API Key (REQUIRED)

1. Go to [https://tavily.com](https://tavily.com)
2. Sign up for a free account
3. Navigate to **API Keys** section
4. Copy your API key
5. **Free tier includes**: 1,000 searches/month

### LangSmith API Key (OPTIONAL - for debugging)

1. Go to [https://smith.langchain.com](https://smith.langchain.com)
2. Sign in with your account
3. Go to **Settings → API Keys**
4. Create a new API key
5. Copy the key

---

## Step 2: Configure the Environment

### 2.1 Create Virtual Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate it
source .venv/bin/activate  # On Linux/Mac
# OR
.venv\Scripts\activate     # On Windows
```

### 2.2 Install Dependencies

```bash
pip install -r requirements.txt
```

### 2.3 Configure API Keys and LLM Models

The `.env` file already exists. Open it and add your API keys:

```bash
# Edit .env file
nano .env   # or vim .env, or use your favorite editor
```

**Minimal configuration** (required):

```bash
# REQUIRED - Add your keys here
OPENAI_API_KEY="sk-your-openai-key-here"
TAVILY_API_KEY="tvly-your-tavily-key-here"

# Keep default values
ENABLED_AGENTS=researcher,analyst,writer
DEFAULT_MODEL=openai/gpt-4o-mini
```

**Multi-Provider configuration** (use any LLM provider):

Cortex Flow now supports **multiple LLM providers** with flexible per-agent configuration!

```bash
# Add API keys for providers you want to use
OPENAI_API_KEY="sk-..."
ANTHROPIC_API_KEY="sk-ant-..."
GOOGLE_API_KEY="..."
GROQ_API_KEY="gsk_..."
OPENROUTER_API_KEY="sk-or-..."

# Option 1: Use same model for all agents
DEFAULT_MODEL=anthropic/claude-sonnet-4-20250514

# Option 2: Different model per agent (recommended for optimization)
RESEARCHER_MODEL=anthropic/claude-sonnet-4-20250514  # Best for research
ANALYST_MODEL=openai/gpt-4o                          # Fast analysis
WRITER_MODEL=anthropic/claude-opus-4-20250514        # Best for writing
SUPERVISOR_MODEL=openai/gpt-4o-mini                  # Economical orchestration

# Option 3: Task-specific models (advanced)
RESEARCHER_DEEP_ANALYSIS_MODEL=anthropic/claude-opus-4-20250514
RESEARCHER_QUICK_SEARCH_MODEL=openai/gpt-4o-mini
WRITER_CREATIVE_MODEL=anthropic/claude-opus-4-20250514
WRITER_TECHNICAL_MODEL=openai/gpt-4o
```

**Provider format**: Use `provider/model` format:
- OpenAI: `openai/gpt-4o`, `openai/gpt-4o-mini`, `openai/o1`
- Anthropic: `anthropic/claude-opus-4-20250514`, `anthropic/claude-sonnet-4-20250514`
- Google: `google/gemini-1.5-pro`, `google/gemini-2.0-flash-exp`
- Groq: `groq/llama-3.3-70b-versatile`
- OpenRouter: `openrouter/anthropic/claude-3.5-sonnet` (access 100+ models!)

**Automatic fallback**: If a provider is unavailable, the system automatically tries the next available provider in order.

**For LangSmith tracing** (optional - for debugging):

```bash
LANGSMITH_API_KEY="your-langsmith-key"
LANGSMITH_TRACING=true
```

---

## Step 3: Verify Installation

### 3.1 Test Configuration

```bash
# Test that config loads correctly
python -c "from config import Settings; s = Settings(); print('✅ Config OK')"
```

### 3.2 Test Agent Imports

```bash
# Test agent imports
python -c "from agents.researcher import get_researcher_agent; print('✅ Researcher OK')"
python -c "from agents.analyst import get_analyst_agent; print('✅ Analyst OK')"
python -c "from agents.writer import get_writer_agent; print('✅ Writer OK')"
```

If you see errors about API keys, make sure you've set `OPENAI_API_KEY` in your `.env` file.

---

## Step 4: Start the System

### Option A: Start All Agents (Recommended)

```bash
./scripts/start_all.sh
```

**Expected output:**
```
🚀 Starting Cortex Flow Multi-Agent System...

📋 Enabled agents: researcher,analyst,writer

📡 Starting Researcher Agent (port 8001)...
📊 Starting Analyst Agent (port 8003)...
✍️  Starting Writer Agent (port 8004)...
🎯 Starting Supervisor Agent (port 8000)...

⏳ Waiting for servers to start...

🏥 Checking server health...
   ✅ Researcher is healthy
   ✅ Analyst is healthy
   ✅ Writer is healthy
   ✅ Supervisor is healthy

✅ All agents are running!

Supervisor API: http://localhost:8000
Swagger Docs:   http://localhost:8000/docs
```

### Option B: Start Selective Agents

Edit `.env` to enable only specific agents:

```bash
# Enable only researcher and writer
ENABLED_AGENTS=researcher,writer
```

Then start:

```bash
./scripts/start_all.sh
```

---

## Step 5: Test the System

### 5.1 Run Integration Tests

```bash
python tests/test_system.py
```

**Expected output:**
```
🧪 Cortex Flow System Test Suite
================================================================
📋 Phase 1: Health Checks
   ✅ Researcher is healthy
   ✅ Analyst is healthy
   ✅ Writer is healthy
   ✅ Supervisor is healthy

📋 Phase 2: Supervisor Orchestration
   ✅ Supervisor orchestration successful!
```

### 5.2 Test with curl

```bash
curl -X POST http://localhost:8000/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "test-001",
    "source_agent_id": "client",
    "target_agent_id": "supervisor",
    "task_description": "What is LangGraph and how does it work?",
    "context": {}
  }'
```

### 5.3 Test with Swagger UI

1. Open browser: [http://localhost:8000/docs](http://localhost:8000/docs)
2. Click on **POST /invoke**
3. Click **"Try it out"**
4. Use this example request:

```json
{
  "task_id": "demo-001",
  "source_agent_id": "client",
  "target_agent_id": "supervisor",
  "task_description": "Research the latest trends in AI agents and write a brief summary",
  "context": {}
}
```

5. Click **"Execute"**

---

## Step 6: Monitor and Debug

### View Logs

```bash
# View all logs
tail -f logs/supervisor.log
tail -f logs/researcher.log
tail -f logs/analyst.log
tail -f logs/writer.log

# Or use multi-tail
tail -f logs/*.log
```

### Check Health Endpoints

```bash
# Supervisor
curl http://localhost:8000/health

# Individual agents
curl http://localhost:8001/health  # Researcher
curl http://localhost:8003/health  # Analyst
curl http://localhost:8004/health  # Writer
```

### Enable LangSmith Tracing

For detailed debugging, enable LangSmith:

1. Get API key from [https://smith.langchain.com](https://smith.langchain.com)
2. Edit `.env`:
   ```bash
   LANGSMITH_API_KEY="your-key-here"
   LANGSMITH_TRACING=true
   ```
3. Restart the system
4. View traces at [https://smith.langchain.com](https://smith.langchain.com)

---

## Step 7: Stop the System

```bash
./scripts/stop_all.sh
```

---

## Common Issues & Solutions

### Issue: "OpenAI API key not set" or "No API key configured"

**Solution**: Make sure you have at least one LLM provider API key configured in `.env` file.

```bash
# Option 1: Use OpenAI (default)
OPENAI_API_KEY="sk-your-key"

# Option 2: Use Anthropic instead
ANTHROPIC_API_KEY="sk-ant-your-key"
DEFAULT_MODEL=anthropic/claude-sonnet-4-20250514

# Option 3: Use any provider via OpenRouter
OPENROUTER_API_KEY="sk-or-your-key"
DEFAULT_MODEL=openrouter/anthropic/claude-3.5-sonnet
```

**Note**: With the new multi-provider system, you can use **any** LLM provider, not just OpenAI!

### Issue: "Researcher failed to start"

**Solution**: Check that `TAVILY_API_KEY` is set in `.env` file.

### Issue: "Port already in use"

**Solution**:
```bash
# Find process using port 8000
lsof -i :8000

# Kill it
kill -9 <PID>

# Or stop all agents and restart
./scripts/stop_all.sh
./scripts/start_all.sh
```

### Issue: "Module not found"

**Solution**: Make sure virtual environment is activated and dependencies are installed:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### Issue: Agent shows as unhealthy

**Solution**: Check logs for specific error:

```bash
tail -50 logs/researcher.log  # or analyst.log, writer.log
```

Common causes:
- Missing API keys
- Port already in use
- Python dependencies not installed

---

## Docker Setup (Alternative)

### Using Docker Compose

```bash
# 1. Configure .env as described above

# 2. Start all services
docker-compose --profile=full up --build

# 3. Test
python tests/test_system.py

# 4. Stop
docker-compose down
```

### Selective Docker Deployment

```bash
# Start only supervisor + researcher
docker-compose --profile=minimal --profile=research up

# Start only supervisor + analyst + writer
docker-compose --profile=minimal --profile=analysis --profile=writing up
```

---

## Next Steps

Now that your system is running:

1. **Read Examples**: Check [EXAMPLES.md](EXAMPLES.md) for usage examples
2. **Learn Agent Management**: Read [AGENT_MANAGEMENT.md](AGENT_MANAGEMENT.md) to learn about dynamic agent configuration
3. **Add Custom Agents**: Follow the guide in [AGENT_MANAGEMENT.md](AGENT_MANAGEMENT.md#adding-new-agents) to create your own agents
4. **Deploy to Production**: See [README.md](README.md) Phase 6 checklist for deployment considerations

---

## Quick Reference

```bash
# Start system
./scripts/start_all.sh

# Stop system
./scripts/stop_all.sh

# Run tests
python tests/test_system.py

# View logs
tail -f logs/*.log

# Check health
curl http://localhost:8000/health

# API Docs
open http://localhost:8000/docs
```

---

## Support

If you encounter issues:

1. Check the logs in `logs/` directory
2. Verify API keys are set correctly
3. Make sure ports 8000-8004 are available
4. Check [AGENT_MANAGEMENT.md](AGENT_MANAGEMENT.md) for troubleshooting

---

## Summary Checklist

Before starting the system, ensure:

- [ ] Python 3.10+ installed
- [ ] Virtual environment created and activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file configured with:
  - [ ] `OPENAI_API_KEY` (required)
  - [ ] `TAVILY_API_KEY` (required)
  - [ ] `ENABLED_AGENTS` set (default: `researcher,analyst,writer`)
- [ ] Ports 8000-8004 available
- [ ] All import tests pass

Then run:
```bash
./scripts/start_all.sh
python tests/test_system.py
```

✅ You're ready to use Cortex Flow!
