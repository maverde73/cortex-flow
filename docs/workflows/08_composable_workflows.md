# Composable Workflows

## Overview

**Composable workflows** allow workflows to call other workflows as nodes, enabling modular design and reusability. This powerful feature lets you build complex workflows by combining simpler, reusable workflow components.

## Key Features

- 🔄 **Workflow Reusability**: Use existing workflows as building blocks
- 📦 **Modular Design**: Build complex workflows from simple components
- 🎯 **Recursive Execution**: Workflows can call other workflows up to a configurable depth
- ⚡ **Parallel Sub-workflows**: Execute multiple sub-workflows in parallel
- 🔒 **Safety Controls**: Built-in recursion limits and circular dependency detection

## How It Works

### Workflow Node Type

A workflow node uses `agent: "workflow"` to specify that it should execute another workflow:

```json
{
  "id": "sub_workflow_node",
  "agent": "workflow",
  "workflow_name": "simple_research",
  "instruction": "Execute research workflow for {topic}",
  "workflow_params": {
    "query": "{topic}",
    "depth": "detailed"
  },
  "max_depth": 3
}
```

### Node Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `agent` | string | Yes | Must be `"workflow"` |
| `workflow_name` | string | Yes | Name of the workflow to execute |
| `instruction` | string | Yes | User input for the sub-workflow |
| `workflow_params` | object | No | Parameters to pass to the sub-workflow |
| `max_depth` | integer | No | Maximum recursion depth (default: 5) |
| `depends_on` | array | No | Dependencies on other nodes |
| `parallel_group` | string | No | Group for parallel execution |
| `timeout` | integer | No | Timeout in seconds |

## Examples

### 1. Simple Composition

**research_and_report.json** - Combines two existing workflows:

```json
{
  "name": "research_and_report",
  "description": "Execute research then generate report",
  "nodes": [
    {
      "id": "research_phase",
      "agent": "workflow",
      "workflow_name": "multi_source_research",
      "instruction": "Research about: {topic}",
      "workflow_params": {
        "topic": "{topic}"
      }
    },
    {
      "id": "report_phase",
      "agent": "workflow",
      "workflow_name": "report_generation",
      "instruction": "Generate report from research",
      "depends_on": ["research_phase"],
      "workflow_params": {
        "data": "{research_phase}"
      }
    }
  ],
  "parameters": {
    "topic": "AI trends 2024"
  }
}
```

### 2. Parallel Sub-workflows

**comparative_research.json** - Execute multiple workflows in parallel:

```json
{
  "name": "comparative_research",
  "description": "Compare multiple topics using parallel workflows",
  "nodes": [
    {
      "id": "research_react",
      "agent": "workflow",
      "workflow_name": "simple_research",
      "parallel_group": "research",
      "workflow_params": {
        "query": "React framework"
      }
    },
    {
      "id": "research_vue",
      "agent": "workflow",
      "workflow_name": "simple_research",
      "parallel_group": "research",
      "workflow_params": {
        "query": "Vue framework"
      }
    },
    {
      "id": "research_angular",
      "agent": "workflow",
      "workflow_name": "simple_research",
      "parallel_group": "research",
      "workflow_params": {
        "query": "Angular framework"
      }
    },
    {
      "id": "compare",
      "agent": "analyst",
      "instruction": "Compare the three frameworks",
      "depends_on": ["research_react", "research_vue", "research_angular"]
    }
  ]
}
```

### 3. Building Blocks

Create simple, reusable workflows as building blocks:

**simple_research.json**:
```json
{
  "name": "simple_research",
  "description": "Reusable research building block",
  "nodes": [
    {
      "id": "search",
      "agent": "researcher",
      "instruction": "Search: {query}"
    },
    {
      "id": "summarize",
      "agent": "analyst",
      "instruction": "Summarize findings",
      "depends_on": ["search"]
    }
  ],
  "parameters": {
    "query": ""
  }
}
```

### 4. Multi-level Composition

**modular_analysis.json** - Complex workflow with nested sub-workflows:

```json
{
  "name": "modular_analysis",
  "nodes": [
    {
      "id": "initial_research",
      "agent": "researcher",
      "instruction": "Initial research on {topic}"
    },
    {
      "id": "deep_analysis",
      "agent": "workflow",
      "workflow_name": "data_analysis_report",
      "depends_on": ["initial_research"],
      "workflow_params": {
        "data": "{initial_research}"
      }
    },
    {
      "id": "sentiment_check",
      "agent": "workflow",
      "workflow_name": "sentiment_routing",
      "depends_on": ["initial_research"],
      "workflow_params": {
        "content": "{initial_research}"
      }
    },
    {
      "id": "final_report",
      "agent": "workflow",
      "workflow_name": "report_generation",
      "depends_on": ["deep_analysis", "sentiment_check"],
      "workflow_params": {
        "analysis": "{deep_analysis}",
        "sentiment": "{sentiment_check}"
      }
    }
  ]
}
```

## Parameter Passing

### Inheritance

Sub-workflows inherit parameters from their parent workflow:

```json
{
  "nodes": [
    {
      "id": "parent_node",
      "agent": "analyst",
      "instruction": "Process {global_param}"
    },
    {
      "id": "child_workflow",
      "agent": "workflow",
      "workflow_name": "sub_workflow",
      "workflow_params": {
        "inherited": "{global_param}",
        "from_parent": "{parent_node}",
        "new_param": "static_value"
      }
    }
  ],
  "parameters": {
    "global_param": "shared_value"
  }
}
```

### Variable Substitution

Variables from parent workflow can be used in sub-workflow parameters:

- `{node_id}` - Output from a previous node
- `{param_name}` - Parameter from parent workflow
- `{node_id.field}` - Specific field from node output (if structured)

## Safety Features

### Recursion Depth Limit

Prevent infinite recursion with `max_depth`:

```json
{
  "id": "recursive_node",
  "agent": "workflow",
  "workflow_name": "some_workflow",
  "max_depth": 3  // Maximum 3 levels deep
}
```

Default maximum depth: **5 levels**

### Circular Dependency Detection

The system automatically detects and prevents circular dependencies:

```
WorkflowA → WorkflowB → WorkflowC → WorkflowA  ❌ Detected!
```

Error message:
```
Circular workflow dependency detected: workflow_a is already in the execution stack
```

### Execution Stack Tracking

The system maintains a stack of parent workflows to track the execution path:

```python
state.parent_workflow_stack = ["root", "workflow_a", "workflow_b"]
state.recursion_depth = 3
```

## Best Practices

### 1. Design Modular Workflows

Create small, focused workflows that do one thing well:

```json
{
  "name": "validate_data",
  "description": "Reusable data validation workflow",
  "nodes": [
    {
      "id": "validate",
      "agent": "analyst",
      "instruction": "Validate data format"
    }
  ]
}
```

### 2. Use Meaningful Names

Choose descriptive names for workflows and parameters:

```json
{
  "workflow_name": "customer_sentiment_analysis",  // ✅ Clear
  "workflow_name": "workflow1",                    // ❌ Vague
}
```

### 3. Document Dependencies

Clearly document what each workflow expects:

```json
{
  "description": "Requires: 'customer_data' and 'time_period' parameters",
  "parameters": {
    "customer_data": "",
    "time_period": "30_days"
  }
}
```

### 4. Set Appropriate Timeouts

Sub-workflows may take longer than individual nodes:

```json
{
  "agent": "workflow",
  "workflow_name": "complex_analysis",
  "timeout": 600  // 10 minutes for complex workflow
}
```

### 5. Test Incrementally

Test building blocks before composing them:

1. Test `simple_research` workflow
2. Test `report_generation` workflow
3. Then combine them in `research_and_report`

## Performance Considerations

### Parallel Execution

Maximize performance with parallel sub-workflows:

```json
{
  "nodes": [
    {
      "id": "workflow1",
      "agent": "workflow",
      "parallel_group": "parallel_workflows"
    },
    {
      "id": "workflow2",
      "agent": "workflow",
      "parallel_group": "parallel_workflows"
    }
  ]
}
```

### Resource Usage

Each sub-workflow creates:
- New WorkflowEngine instance
- Separate execution context
- Independent state management

Consider resource implications for deeply nested workflows.

## Error Handling

### Sub-workflow Failures

If a sub-workflow fails, the parent workflow receives an error:

```json
{
  "success": false,
  "error": "Sub-workflow 'analysis' failed: Timeout exceeded"
}
```

### Graceful Degradation

Use conditional edges to handle failures:

```json
{
  "conditional_edges": [
    {
      "from_node": "sub_workflow",
      "conditions": [
        {
          "field": "custom_metadata.sub_workflow_failed",
          "operator": "equals",
          "value": true,
          "next_node": "fallback_node"
        }
      ],
      "default": "continue_node"
    }
  ]
}
```

## Testing Composable Workflows

### Unit Testing

Test individual workflows in isolation:

```python
async def test_simple_workflow():
    template = load_template("simple_research.json")
    result = await engine.execute_workflow(
        template=template,
        user_input="test query",
        params={"query": "AI"}
    )
    assert result.success
```

### Integration Testing

Test workflow composition:

```python
async def test_composed_workflow():
    template = load_template("research_and_report.json")
    result = await engine.execute_workflow(
        template=template,
        user_input="Research AI",
        params={"topic": "AI"}
    )
    assert result.success
    assert "research_phase" in result.node_results
    assert "report_phase" in result.node_results
```

## Troubleshooting

### Common Issues

1. **Workflow not found**
   - Ensure workflow exists in the project's workflows directory
   - Check workflow name spelling

2. **Maximum recursion depth exceeded**
   - Increase `max_depth` if needed
   - Review workflow design for unnecessary nesting

3. **Circular dependency detected**
   - Review workflow relationships
   - Ensure workflows don't call each other in a loop

4. **Parameter not passed correctly**
   - Check variable substitution syntax
   - Verify parameter names match

### Debug Logging

Enable debug logging to trace execution:

```python
import logging
logging.getLogger("workflows.engine").setLevel(logging.DEBUG)
```

Output shows:
```
🔄 Executing sub-workflow 'simple_research' from node 'research_node' (depth: 2/5)
   ✓ Sub-workflow 'simple_research' completed successfully in 3.2s
```

## Migration Guide

### Converting Existing Workflows

Transform repetitive nodes into reusable workflows:

**Before** (repetitive):
```json
{
  "nodes": [
    {
      "id": "research1",
      "agent": "researcher",
      "instruction": "Research topic 1"
    },
    {
      "id": "analyze1",
      "agent": "analyst",
      "instruction": "Analyze research 1"
    },
    {
      "id": "research2",
      "agent": "researcher",
      "instruction": "Research topic 2"
    },
    {
      "id": "analyze2",
      "agent": "analyst",
      "instruction": "Analyze research 2"
    }
  ]
}
```

**After** (composable):
```json
{
  "nodes": [
    {
      "id": "workflow1",
      "agent": "workflow",
      "workflow_name": "research_and_analyze",
      "workflow_params": {"topic": "topic 1"}
    },
    {
      "id": "workflow2",
      "agent": "workflow",
      "workflow_name": "research_and_analyze",
      "workflow_params": {"topic": "topic 2"}
    }
  ]
}
```

## Summary

Composable workflows provide:
- **Modularity**: Build complex from simple
- **Reusability**: Write once, use many times
- **Maintainability**: Update in one place
- **Scalability**: Create workflow libraries
- **Safety**: Built-in recursion and circular dependency protection

Start with simple building blocks and compose them into powerful, complex workflows!