# Cortex Flow - Usage Examples

This document provides practical examples of using the Cortex Flow multi-agent system.

## Prerequisites

```bash
# 1. Start all agents
./scripts/start_all.sh

# 2. Verify all agents are healthy
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8003/health
curl http://localhost:8004/health
```

## Example 1: Simple Web Research

Ask the supervisor to find information using the researcher agent.

```bash
curl -X POST http://localhost:8000/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "example-1",
    "source_agent_id": "user",
    "target_agent_id": "supervisor",
    "task_description": "What is LangGraph and how does it differ from LangChain?",
    "context": {}
  }'
```

**Expected workflow**:
- Supervisor → Researcher → Web search → Return results

## Example 2: Research + Analysis

Request that combines research with analysis.

```bash
curl -X POST http://localhost:8000/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "example-2",
    "source_agent_id": "user",
    "target_agent_id": "supervisor",
    "task_description": "Find the latest developments in AI agent frameworks and analyze the key trends",
    "context": {}
  }'
```

**Expected workflow**:
- Supervisor → Researcher → Find information
- Supervisor → Analyst → Analyze findings
- Supervisor → Return analysis

## Example 3: Full Report Generation

Request a complete report (research → analysis → writing).

```bash
curl -X POST http://localhost:8000/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "example-3",
    "source_agent_id": "user",
    "target_agent_id": "supervisor",
    "task_description": "Create a professional report on the current state of multi-agent AI systems, including recent developments and future trends",
    "context": {
      "report_style": "professional",
      "target_audience": "technical"
    }
  }'
```

**Expected workflow**:
- Supervisor → Researcher → Gather information
- Supervisor → Analyst → Extract insights
- Supervisor → Writer → Create formatted report
- Supervisor → Return final report

## Example 4: Python Client

Using Python to interact with the system:

```python
import httpx
import asyncio
from schemas.mcp_protocol import MCPRequest, MCPResponse

async def ask_supervisor(question: str):
    """Send a question to the supervisor agent."""
    request = MCPRequest(
        source_agent_id="python-client",
        target_agent_id="supervisor",
        task_description=question
    )

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/invoke",
            json=request.model_dump(mode='json'),
            timeout=120.0
        )

        mcp_response = MCPResponse(**response.json())

        if mcp_response.status == "success":
            print("✅ Success!")
            print(f"\nResult:\n{mcp_response.result}")
            print(f"\nMetadata: {mcp_response.metadata}")
        else:
            print(f"❌ Error: {mcp_response.error_message}")

# Run the example
asyncio.run(ask_supervisor(
    "Explain the benefits of using a multi-agent architecture for AI systems"
))
```

## Example 5: Direct Agent Access

You can also call individual agents directly (bypassing the supervisor):

### Call Researcher Directly

```bash
curl -X POST http://localhost:8001/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "direct-research",
    "source_agent_id": "user",
    "target_agent_id": "researcher",
    "task_description": "Find recent articles about FastAPI",
    "context": {}
  }'
```

### Call Analyst Directly

```bash
curl -X POST http://localhost:8003/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "direct-analysis",
    "source_agent_id": "user",
    "target_agent_id": "analyst",
    "task_description": "Analyze the following data: [your data here]",
    "context": {}
  }'
```

### Call Writer Directly

```bash
curl -X POST http://localhost:8004/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "direct-write",
    "source_agent_id": "user",
    "target_agent_id": "writer",
    "task_description": "Write a brief introduction to microservices architecture",
    "context": {}
  }'
```

## Example 6: Monitoring and Debugging

### Check System Health

```bash
# Quick health check of all agents
for port in 8000 8001 8003 8004; do
  echo "Port $port:"
  curl -s http://localhost:$port/health | jq
done
```

### View API Documentation

Open in browser:
- Supervisor: http://localhost:8000/docs
- Researcher: http://localhost:8001/docs
- Analyst: http://localhost:8003/docs
- Writer: http://localhost:8004/docs

### View Logs

```bash
# Real-time log viewing
tail -f logs/supervisor.log
tail -f logs/researcher.log
tail -f logs/analyst.log
tail -f logs/writer.log
```

## Example 7: Complex Multi-Step Task

Request that exercises multiple agents multiple times:

```bash
curl -X POST http://localhost:8000/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "complex-task",
    "source_agent_id": "user",
    "target_agent_id": "supervisor",
    "task_description": "Compare LangGraph with CrewAI frameworks. Research both, analyze their strengths and weaknesses, and create a comparison report with recommendations for when to use each.",
    "context": {
      "depth": "comprehensive",
      "include_examples": true
    }
  }'
```

**Expected workflow**:
- Supervisor → Researcher → Find LangGraph info
- Supervisor → Researcher → Find CrewAI info
- Supervisor → Analyst → Compare and contrast
- Supervisor → Writer → Create comparison report
- Supervisor → Return final report

## Example 8: Using with Different LLMs

By default, the system uses OpenAI's gpt-4o-mini. You can configure different models in .env:

```bash
# In .env file:
DEFAULT_MODEL=gpt-4-turbo
# or
DEFAULT_MODEL=gpt-3.5-turbo
# or with Anthropic (requires ANTHROPIC_API_KEY):
DEFAULT_MODEL=claude-3-sonnet-20240229
```

## Example 9: Integration with External Applications

### JavaScript/Node.js Client

```javascript
const axios = require('axios');

async function askCortexFlow(question) {
    const request = {
        task_id: `js-${Date.now()}`,
        source_agent_id: 'javascript-client',
        target_agent_id: 'supervisor',
        task_description: question,
        context: {}
    };

    const response = await axios.post(
        'http://localhost:8000/invoke',
        request,
        { timeout: 120000 }
    );

    return response.data;
}

askCortexFlow('Explain microservices in simple terms')
    .then(result => console.log(result.result))
    .catch(err => console.error(err));
```

### cURL with Pretty Output

```bash
curl -X POST http://localhost:8000/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "curl-test",
    "source_agent_id": "curl-client",
    "target_agent_id": "supervisor",
    "task_description": "What are the benefits of async programming in Python?",
    "context": {}
  }' | jq '.result' -r
```

## Tips for Best Results

1. **Be Specific**: Clear, detailed task descriptions yield better results
2. **Use Context**: The `context` field can provide additional parameters
3. **Appropriate Model**: Use gpt-4 for complex reasoning, gpt-3.5-turbo for speed
4. **Timeout Settings**: Complex tasks may need longer timeouts
5. **Check Logs**: Monitor logs for debugging and understanding agent behavior

## Troubleshooting

### No Response / Timeout
```bash
# Check if agents are running
ps aux | grep "server.py"

# Restart agents
./stop_all.sh && ./start_all.sh
```

### API Key Errors
```bash
# Verify .env configuration
cat .env | grep API_KEY

# Ensure keys are not empty strings
```

### Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```
