# LangGraph Workflow Compatibility

## Overview

Starting from version 0.4.0, Cortex Flow workflow templates are **natively compatible with LangGraph**. Workflow templates defined in JSON or YAML are now compiled directly to LangGraph `StateGraph` objects, enabling access to powerful LangGraph features while maintaining the simplicity of our DSL.

This guide explains the LangGraph compilation system, its benefits, migration path, and usage.

## Table of Contents

- [Why LangGraph Compilation?](#why-langgraph-compilation)
- [Architecture](#architecture)
- [Benefits](#benefits)
- [Execution Modes](#execution-modes)
- [Configuration](#configuration)
- [Migration Guide](#migration-guide)
- [Usage Examples](#usage-examples)
- [Comparison: LangGraph vs Custom Mode](#comparison-langgraph-vs-custom-mode)
- [Advanced Features](#advanced-features)
- [Troubleshooting](#troubleshooting)

---

## Why LangGraph Compilation?

Previously, workflow templates were executed by a custom engine that manually orchestrated nodes, dependencies, and conditions. While functional, this approach missed out on LangGraph's native capabilities:

- **No checkpointing**: State was not persisted between steps
- **No streaming**: Could not stream intermediate results to clients
- **No human-in-the-loop**: Could not interrupt workflows for human feedback
- **No LangSmith tracing**: Missing distributed tracing for debugging
- **Duplicated logic**: Maintained separate execution engine from agents

**Solution**: Compile workflow templates to native LangGraph `StateGraph` objects, unifying the execution system.

---

## Architecture

### Compilation Pipeline

```
WorkflowTemplate (Pydantic DSL)
          ↓
   LangGraphWorkflowCompiler
          ↓
   StateGraph (LangGraph)
          ↓
    CompiledGraph
          ↓
   ainvoke() / astream()
```

### Key Components

1. **`LangGraphWorkflowCompiler`** (`workflows/langgraph_compiler.py`)
   - Compiles `WorkflowTemplate` to `StateGraph`
   - Generates node functions for each `WorkflowNode`
   - Handles parallel execution via `Send()` API
   - Converts conditional edges to LangGraph routing

2. **`WorkflowEngine`** (`workflows/engine.py`)
   - Hybrid mode support: `langgraph` (default) or `custom` (legacy)
   - Routes execution to compiler or custom engine
   - Returns unified `WorkflowResult` structure

3. **`WorkflowStateGraph`** (`workflows/langgraph_compiler.py`)
   - Extended state class for LangGraph compatibility
   - Includes `user_input`, `node_outputs`, `completed_nodes`, etc.

---

## Benefits

### 1. Native Checkpointing

Workflow state is automatically persisted using LangGraph's checkpointing system (PostgreSQL, Redis, or in-memory).

**Benefits**:
- Resume workflows after crashes
- Implement retry logic
- Audit workflow execution history

**Configuration**:
```python
from langgraph.checkpoint.postgres import PostgresSaver

checkpointer = PostgresSaver.from_conn_string("postgresql://...")
compiled_graph = compiler.compile(template)
compiled_with_checkpoints = compiled_graph.with_config(checkpointer=checkpointer)
```

### 2. Streaming Responses

Stream intermediate node results to clients in real-time using `.astream()`.

**Example**:
```python
async for event in compiled_graph.astream({"user_input": "research AI trends"}):
    print(f"Node: {event['current_node']}, Output: {event['node_outputs']}")
```

### 3. Human-in-the-Loop (HITL)

Interrupt workflows to request human approval or input.

**Example**:
```python
compiled_graph = compiler.compile(template).with_interrupt(
    before=["approval_node"]
)

# Workflow pauses before "approval_node"
result = await compiled_graph.ainvoke({"user_input": "..."})

# Human reviews and resumes
result = await compiled_graph.ainvoke(None, config={"resume": True})
```

### 4. LangSmith Tracing

Automatic distributed tracing for debugging and monitoring.

**Configuration**:
```bash
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY=your_api_key
export LANGCHAIN_PROJECT=cortex-flow-workflows
```

### 5. Unified Execution System

Agents and workflows now share the same LangGraph execution engine, simplifying the codebase.

---

## Execution Modes

The `WorkflowEngine` supports two modes:

### 1. LangGraph Mode (Default, Recommended)

Compiles templates to native LangGraph `StateGraph`.

**Configuration**:
```python
from workflows.engine import WorkflowEngine

engine = WorkflowEngine(mode="langgraph")
```

**When to use**:
- ✅ Production deployments
- ✅ Need checkpointing, streaming, or HITL
- ✅ Want LangSmith tracing
- ✅ New workflows

### 2. Custom Mode (Legacy)

Uses the original custom execution engine.

**Configuration**:
```python
engine = WorkflowEngine(mode="custom")
```

**When to use**:
- ⚠️ Backward compatibility during migration
- ⚠️ Debugging issues with compiled mode
- ⚠️ Workflows with edge cases not yet supported in compiler

**Note**: Custom mode is deprecated and will be removed in future versions.

---

## Configuration

### Environment Variables

Set the default execution mode via `.env`:

```bash
# .env
WORKFLOW_ENGINE_MODE=langgraph  # or "custom"
```

### Programmatic Configuration

Override mode per-workflow:

```python
# config_legacy.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    workflow_engine_mode: str = "langgraph"

settings = Settings()
```

### Supervisor Configuration

The workflow supervisor automatically uses the configured mode:

```python
# agents/workflow_supervisor.py
engine_mode = getattr(settings, 'workflow_engine_mode', 'langgraph')
workflow_engine = WorkflowEngine(mode=engine_mode)
```

---

## Migration Guide

### Step 1: Verify Template Compatibility

Ensure your templates follow the standard DSL schema:

```yaml
name: my_workflow
description: Example workflow
nodes:
  - id: step1
    agent: researcher
    instruction: "Research {user_input}"
  - id: step2
    agent: analyst
    instruction: "Analyze {step1}"
    depends_on: [step1]
```

**Check**:
- ✅ All `depends_on` references exist
- ✅ Conditional edge targets exist
- ✅ No circular dependencies
- ✅ Valid agent types (`researcher`, `analyst`, `writer`, `mcp_tool`)

### Step 2: Test with LangGraph Mode

Switch to LangGraph mode and run tests:

```bash
# .env
WORKFLOW_ENGINE_MODE=langgraph

# Run tests
pytest tests/test_langgraph_compiler.py -v
```

### Step 3: Monitor Logs

Enable verbose logging to compare execution:

```python
import logging
logging.basicConfig(level=logging.INFO)

# Look for:
# "🔨 Compiling workflow 'my_workflow' to LangGraph (3 nodes)"
# "📍 Executing node 'step1' (agent: researcher)"
# "✅ Workflow 'my_workflow' compiled successfully"
```

### Step 4: Validate Results

Ensure `WorkflowResult` structure is consistent:

```python
result = await engine.execute_workflow(template, user_input, params)

assert result.workflow_name == template.name
assert result.success == True
assert isinstance(result.final_output, str)
assert isinstance(result.node_results, list)
assert isinstance(result.execution_log, list)
```

### Step 5: Enable Checkpointing (Optional)

For production, configure persistent checkpointing:

```python
from langgraph.checkpoint.postgres import PostgresSaver

checkpointer = PostgresSaver.from_conn_string(
    "postgresql://user:pass@localhost/cortex_flow"
)

# Apply to compiled graphs
compiler = LangGraphWorkflowCompiler()
compiled = compiler.compile(template)
compiled_with_checkpoints = compiled.with_config(checkpointer=checkpointer)
```

### Step 6: Remove Custom Mode

Once migration is complete, remove custom mode fallback:

```python
# Remove from config
WORKFLOW_ENGINE_MODE=langgraph

# Update supervisor
engine = WorkflowEngine(mode="langgraph")  # Explicit
```

---

## Usage Examples

### Example 1: Simple Sequential Workflow

**Template** (`templates/research_workflow.yaml`):
```yaml
name: research_workflow
description: Research and analyze a topic
nodes:
  - id: research
    agent: researcher
    instruction: "Research {user_input}"
  - id: analyze
    agent: analyst
    instruction: "Analyze {research}"
    depends_on: [research]
  - id: write
    agent: writer
    instruction: "Write report based on {analyze}"
    depends_on: [analyze]
```

**Execution**:
```python
from workflows.engine import WorkflowEngine
from workflows.registry import get_workflow_registry

engine = WorkflowEngine(mode="langgraph")
registry = get_workflow_registry("templates/")
template = registry.get("research_workflow")

result = await engine.execute_workflow(
    template=template,
    user_input="AI trends in 2025",
    params={}
)

print(result.final_output)
```

### Example 2: Parallel Execution

**Template**:
```yaml
name: parallel_research
description: Research multiple topics in parallel
nodes:
  - id: research_ai
    agent: researcher
    instruction: "Research AI trends"
    parallel_group: research
  - id: research_blockchain
    agent: researcher
    instruction: "Research blockchain trends"
    parallel_group: research
  - id: synthesize
    agent: analyst
    instruction: "Synthesize {research_ai} and {research_blockchain}"
    depends_on: [research_ai, research_blockchain]
```

**Compiled Graph Structure**:
```
START → [research_ai, research_blockchain] (parallel) → synthesize → END
```

### Example 3: Conditional Routing

**Template**:
```yaml
name: sentiment_routing
description: Route based on sentiment analysis
nodes:
  - id: analyze
    agent: analyst
    instruction: "Analyze sentiment of {user_input}"
  - id: positive_response
    agent: writer
    instruction: "Write positive response"
  - id: negative_response
    agent: writer
    instruction: "Write empathetic response"

conditional_edges:
  - from_node: analyze
    conditions:
      - field: sentiment_score
        operator: greater_than
        value: 0.5
        next_node: positive_response
    default: negative_response
```

**Compiled Graph Structure**:
```
START → analyze → [condition]
                   ├─ sentiment_score > 0.5 → positive_response → END
                   └─ else → negative_response → END
```

### Example 4: Streaming Workflow

```python
from workflows.langgraph_compiler import compile_workflow

compiled_graph = compile_workflow(template)

async for event in compiled_graph.astream({"user_input": "research AI"}):
    if "current_node" in event:
        print(f"Executing: {event['current_node']}")
    if "node_outputs" in event:
        print(f"Output: {event['node_outputs'][event['current_node']][:100]}...")
```

**Output**:
```
Executing: research
Output: AI trends in 2025 include multimodal models, agentic AI, and edge computing...
Executing: analyze
Output: The research shows three key trends: 1) Multimodal models are becoming mainstream...
Executing: write
Output: **AI Trends Report 2025**\n\nExecutive Summary:\nThe artificial intelligence landscape...
```

---

## Comparison: LangGraph vs Custom Mode

| Feature | LangGraph Mode | Custom Mode |
|---------|----------------|-------------|
| **Checkpointing** | ✅ Native support (PostgreSQL/Redis) | ❌ No state persistence |
| **Streaming** | ✅ `.astream()` for real-time updates | ❌ Returns final result only |
| **Human-in-the-Loop** | ✅ `.with_interrupt()` | ❌ Not supported |
| **LangSmith Tracing** | ✅ Automatic distributed tracing | ❌ Manual logging only |
| **Parallel Execution** | ✅ Native `Send()` API | ✅ Manual asyncio.gather() |
| **Conditional Routing** | ✅ `add_conditional_edges()` | ✅ Manual condition evaluation |
| **Performance** | ⚡ Optimized by LangGraph | 🐢 Custom orchestration overhead |
| **Maintenance** | ✅ Leverages LangGraph updates | ⚠️ Manual maintenance required |
| **Unified with Agents** | ✅ Same execution engine | ❌ Separate engine |
| **Future Support** | ✅ Active development | ⚠️ Deprecated |

**Recommendation**: Use LangGraph mode for all new workflows. Migrate existing workflows during maintenance windows.

---

## Advanced Features

### Variable Substitution

The compiler supports three types of variable substitution:

1. **User Input**: `{user_input}`
   ```yaml
   instruction: "Research {user_input}"
   ```

2. **Node Outputs**: `{node_id}`
   ```yaml
   instruction: "Analyze {research_step}"
   ```

3. **Workflow Parameters**: `{param_name}`
   ```yaml
   instruction: "Create report for {date} on {topic}"
   ```

**Example**:
```python
result = await engine.execute_workflow(
    template=template,
    user_input="AI trends",
    params={"date": "2025-10-07", "topic": "Multimodal AI"}
)
```

### Metadata Extraction

The compiler automatically extracts metadata for conditional routing:

- **`sentiment_score`**: Float between -1 (negative) and 1 (positive)
- **`content_length`**: Length of output text

**Usage in Conditions**:
```yaml
conditional_edges:
  - from_node: analyze
    conditions:
      - field: sentiment_score
        operator: greater_than
        value: 0.5
        next_node: positive_path
      - field: content_length
        operator: greater_than
        value: 1000
        next_node: detailed_path
    default: default_path
```

### Custom State Fields

Extend `WorkflowStateGraph` for custom metadata:

```python
from workflows.langgraph_compiler import WorkflowStateGraph

class CustomWorkflowState(WorkflowStateGraph):
    custom_field: str = ""
    custom_counter: int = 0

# Use in compiler
compiler = LangGraphWorkflowCompiler()
graph = StateGraph(CustomWorkflowState)
# ... add nodes and edges
```

### Checkpointing Strategies

**1. PostgreSQL (Production)**:
```python
from langgraph.checkpoint.postgres import PostgresSaver

checkpointer = PostgresSaver.from_conn_string(
    "postgresql://user:pass@localhost/cortex_flow"
)
```

**2. Redis (High-throughput)**:
```python
from langgraph.checkpoint.redis import RedisSaver

checkpointer = RedisSaver(host="localhost", port=6379, db=0)
```

**3. In-Memory (Development)**:
```python
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()  # Lost on restart
```

---

## Troubleshooting

### Issue 1: Import Error - `Send` from `langgraph.constants`

**Error**:
```
DeprecationWarning: Importing Send from langgraph.constants is deprecated
```

**Solution**: Update import (will be fixed in future versions):
```python
# Old
from langgraph.constants import Send

# New
from langgraph.graph import Send
```

### Issue 2: Unknown Target Node

**Error**:
```
ValueError: At 'node1' node, 'condition_function' branch found unknown target 'node2'
```

**Cause**: Conditional edge references a node that doesn't exist in the template.

**Solution**: Ensure all conditional targets are defined:
```yaml
nodes:
  - id: node1
    agent: analyst
    instruction: "Analyze"
  - id: node2  # ✅ Must exist
    agent: writer
    instruction: "Write"

conditional_edges:
  - from_node: node1
    conditions:
      - next_node: node2  # References node2
    default: node2
```

### Issue 3: Agent Not Found

**Error**:
```
ValueError: Unknown agent type: custom_agent
```

**Cause**: Workflow references an agent type not available in the system.

**Solution**: Use valid agent types or register custom agents:
```python
# Valid agents
- researcher
- analyst
- writer
- mcp_tool

# Or register custom agent in agents/factory.py
```

### Issue 4: State Key Error

**Error**:
```
KeyError: 'user_input'
```

**Cause**: State not properly initialized before execution.

**Solution**: Ensure `WorkflowEngine` initializes state:
```python
initial_state = {
    "user_input": user_input,
    "workflow_name": template.name,
    "workflow_params": params,
    "node_outputs": {},
    "completed_nodes": [],
    "workflow_history": []
}

result = await compiled_graph.ainvoke(initial_state)
```

### Issue 5: Compilation Timeout

**Error**:
```
Workflow compilation taking too long (> 10s)
```

**Cause**: Very large workflow (100+ nodes) or complex dependencies.

**Solution**: Break into sub-workflows or optimize dependencies:
```yaml
# Instead of one 100-node workflow
name: monolithic_workflow
nodes: [100 nodes]

# Split into sub-workflows
name: main_workflow
nodes:
  - id: phase1
    agent: mcp_tool
    tool_name: execute_sub_workflow
    params:
      workflow_name: phase1_workflow
  - id: phase2
    agent: mcp_tool
    tool_name: execute_sub_workflow
    params:
      workflow_name: phase2_workflow
```

### Issue 6: Checkpointing Not Persisting

**Problem**: State lost after server restart despite using PostgreSQL checkpointer.

**Solution**: Verify checkpointer configuration:
```python
# Check connection
checkpointer = PostgresSaver.from_conn_string(settings.checkpoint_db_url)

# Apply to graph
compiled = compiler.compile(template).with_config(
    checkpointer=checkpointer,
    thread_id="unique_workflow_instance_id"  # ⚠️ Required for persistence
)
```

### Debug Mode

Enable verbose logging for troubleshooting:

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Look for compiler logs:
# "🔨 Compiling workflow 'X' to LangGraph (N nodes)"
# "📍 Executing node 'Y' (agent: Z)"
# "🔀 Routing to N nodes"
# "✅ Workflow 'X' compiled successfully"
```

---

## Testing

### Unit Tests

Run compiler tests:
```bash
pytest tests/test_langgraph_compiler.py -v
```

**Coverage**:
- ✅ Compiler initialization
- ✅ Simple sequential workflows
- ✅ Parallel execution
- ✅ Conditional routing
- ✅ Variable substitution
- ✅ Metadata extraction
- ✅ Hybrid mode (langgraph/custom)
- ✅ Backward compatibility regression tests

### Integration Tests

Test full workflow execution:
```python
import pytest
from workflows.engine import WorkflowEngine
from workflows.registry import get_workflow_registry

@pytest.mark.asyncio
async def test_workflow_integration():
    engine = WorkflowEngine(mode="langgraph")
    registry = get_workflow_registry("templates/")
    template = registry.get("test_workflow")

    result = await engine.execute_workflow(
        template=template,
        user_input="test input",
        params={}
    )

    assert result.success
    assert result.workflow_name == "test_workflow"
    assert len(result.node_results) > 0
```

### Regression Tests

Verify backward compatibility:
```bash
pytest tests/test_langgraph_compiler.py::TestRegressionTests -v
```

---

## Related Documentation

- [Creating Workflow Templates](01_creating_templates.md)
- [Conditional Routing Guide](02_conditional_routing.md)
- [MCP Integration](03_mcp_integration.md)
- [Workflow Cookbook](05_cookbook.md)
- [Migration Guide (DSL)](06_migration_guide.md)

---

## Changelog

### v0.4.0 (2025-10-07)
- ✨ Added LangGraph workflow compilation
- ✨ Hybrid mode support (langgraph/custom)
- ✨ Native checkpointing support
- ✨ Streaming via `.astream()`
- ✨ Human-in-the-loop support
- 📝 Comprehensive test suite (19 tests)
- 🐛 Fixed variable substitution edge cases
- ⚡ Performance improvements via native LangGraph execution

### v0.3.0 (Previous)
- Custom workflow execution engine
- Basic parallel execution
- Conditional routing support

---

## Support

**Issues**: [GitHub Issues](https://github.com/your-org/cortex-flow/issues)
**Discussions**: [GitHub Discussions](https://github.com/your-org/cortex-flow/discussions)
**Documentation**: [Full Docs](../README.md)

---

**Next Steps**:
- [Try the cookbook examples](05_cookbook.md)
- [Migrate existing workflows](#migration-guide)
- [Enable checkpointing for production](#checkpointing-strategies)
