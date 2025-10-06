# Agents Overview

Cortex-Flow implements specialized AI agents using the **ReAct (Reasoning and Acting)** pattern with LangGraph.

---

## What are ReAct Agents?

**ReAct** is a paradigm that combines:
- **Reasoning**: LLM thinks about the problem
- **Acting**: LLM uses tools to gather information or perform actions
- **Observing**: LLM processes tool results

This cycle repeats until the agent reaches a satisfactory answer.

---

## Agent Types

### 🎯 Supervisor Agent

**Role**: Central orchestrator that coordinates other agents

**Strategy**: FAST (3 iterations, 30s timeout, temperature 0.3)

**Responsibilities**:
- Receive user queries
- Decompose complex tasks
- Delegate to specialized agents
- Synthesize final responses
- Route based on task type

**Tools**:
- `delegate_to_researcher`: Request web research
- `delegate_to_analyst`: Request data analysis
- `delegate_to_writer`: Request content generation

**Port**: 8000

---

### 🔬 Researcher Agent

**Role**: Web research and information gathering

**Strategy**: DEEP (20 iterations, 300s timeout, temperature 0.7)

**Responsibilities**:
- Search the web for information
- Validate sources
- Extract relevant facts
- Synthesize findings

**Tools**:
- `tavily_search`: Advanced web search API
- `web_scraper`: Extract content from URLs

**Reflection**: Optional (configurable)

**Port**: 8001

---

### 📊 Analyst Agent

**Role**: Data analysis and insight generation

**Strategy**: BALANCED (10 iterations, 120s timeout, temperature 0.7)

**Responsibilities**:
- Analyze structured data
- Identify patterns
- Generate insights
- Support decision-making

**Tools**:
- `analyze_data`: Statistical analysis
- `query_database`: Database queries (via MCP)
- `generate_chart`: Data visualization

**Reflection**: Optional (configurable)

**Port**: 8003

---

### ✍️ Writer Agent

**Role**: Professional content creation

**Strategy**: CREATIVE (15 iterations, 180s timeout, temperature 0.9)

**Responsibilities**:
- Write articles and reports
- Structure content effectively
- Adapt tone and style
- Ensure quality through self-reflection

**Tools**:
- `generate_outline`: Create content structure
- `write_section`: Generate content sections
- `refine_content`: Improve existing text

**Reflection**: **Enabled by default** (threshold 0.8, max 3 iterations)

**Port**: 8004

---

## ReAct Execution Cycle

### Basic Cycle

```
1. THOUGHT
   Agent: "I need to search for information about X"

2. ACTION
   Agent calls: search_web(query="X")

3. OBSERVATION
   Tool returns: "Found 10 results about X..."

4. THOUGHT
   Agent: "I now have enough information to answer"

5. FINAL ANSWER
   Agent provides response
```

### With Self-Reflection (Writer Agent)

```
1-5. [Normal ReAct cycle produces draft]

6. REFLECTION
   Reflection LLM evaluates draft:
   - Quality score: 0.65
   - Decision: REFINE
   - Suggestions: "Add more examples, improve structure"

7. REFINEMENT
   Agent: "Improving content based on suggestions"
   [Generates improved version]

8. REFLECTION (Round 2)
   - Quality score: 0.85
   - Decision: ACCEPT
   - Result: "Quality sufficient"

9. FINAL ANSWER (Refined)
```

---

## Agent Configuration

### Per-Agent Strategy

Configure reasoning strategy for each agent:

```bash
# Fast decisions for coordination
SUPERVISOR_REACT_STRATEGY=fast

# Deep research for thoroughness
RESEARCHER_REACT_STRATEGY=deep

# Balanced analysis
ANALYST_REACT_STRATEGY=balanced

# Creative content generation
WRITER_REACT_STRATEGY=creative
```

### Strategy Parameters

| Strategy | Iterations | Timeout | Temperature | Use Case |
|----------|-----------|---------|-------------|----------|
| **FAST** | 3 | 30s | 0.3 | Quick decisions, routing |
| **BALANCED** | 10 | 120s | 0.7 | Standard analysis |
| **DEEP** | 20 | 300s | 0.7 | Complex research |
| **CREATIVE** | 15 | 180s | 0.9 | Content generation |

### Self-Reflection Configuration

Enable quality assessment for specific agents:

```bash
# Enable reflection
REACT_ENABLE_REFLECTION=true

# Per-agent configuration
WRITER_ENABLE_REFLECTION=true
WRITER_REFLECTION_THRESHOLD=0.8  # Minimum quality score
WRITER_REFLECTION_MAX_ITERATIONS=3  # Max refinement rounds
```

---

## Agent Communication

Agents communicate via HTTP using a standardized protocol:

```json
{
  "task_id": "unique-id",
  "source_agent_id": "supervisor",
  "target_agent_id": "researcher",
  "task_description": "Research latest AI trends",
  "context": {
    "constraints": ["max 3 sources", "recent only"],
    "previous_results": {}
  },
  "response": null
}
```

---

## Implementation Details

### LangGraph State Machine

Each agent is implemented as a LangGraph `StateGraph`:

```python
from langgraph.graph import StateGraph

class AgentState(TypedDict):
    messages: list
    task_id: str
    iteration: int
    # ... other fields

# Build graph
graph = StateGraph(AgentState)
graph.add_node("agent", agent_node)
graph.add_node("tools", tool_node)
graph.add_conditional_edges("agent", should_continue)
graph.add_edge("tools", "agent")
```

### Tool Integration

Tools are defined using LangChain's `@tool` decorator:

```python
from langchain_core.tools import tool

@tool
def search_web(query: str) -> str:
    """Search the web for information."""
    result = tavily_client.search(query)
    return result
```

---

## Health Checks

Each agent exposes health check endpoints:

```bash
# Check agent health
curl http://localhost:8000/health

# Response
{
  "status": "healthy",
  "agent": "supervisor",
  "version": "1.0.0",
  "uptime_seconds": 3600
}
```

---

## Documentation

### Detailed Guides
- [**ReAct Pattern**](react-pattern.md) - Deep dive into reasoning cycle
- [**Agent Management**](agent-management.md) - Health checks, retries, service discovery
- [**Agent Factory**](factory.md) - Dynamic agent instantiation
- [**Implementation Checklist**](implementation-checklist.md) - ReAct features implementation status

### Related Documentation
- [Architecture Overview](../architecture/README.md) - System design
- [MCP Integration](../mcp/README.md) - External tools
- [Workflows](../workflows/README.md) - Template-based execution

---

**Last Updated**: 2025-10-06
