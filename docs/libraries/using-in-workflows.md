# Using Libraries in Workflows

This guide explains how to use library functions in your workflows.

## Table of Contents

1. [Basic Usage](#basic-usage)
2. [Parameter Substitution](#parameter-substitution)
3. [Working with Outputs](#working-with-outputs)
4. [Error Handling](#error-handling)
5. [Complete Examples](#complete-examples)

## Basic Usage

To use a library function in a workflow, create a node with `agent: "library"`:

```json
{
  "nodes": [{
    "id": "fetch_data",
    "agent": "library",
    "instruction": "Fetch data from API",
    "library_name": "rest_api",
    "function_name": "http_get",
    "function_params": {
      "url": "https://api.example.com/data",
      "headers": {
        "Authorization": "Bearer token123"
      }
    },
    "timeout": 30
  }]
}
```

### Required Fields

- `agent`: Must be `"library"`
- `library_name`: Name of the library to use
- `function_name`: Function to call within the library
- `function_params`: Parameters to pass to the function

### Optional Fields

- `instruction`: Description for logging (not passed to function)
- `timeout`: Override function timeout (seconds)
- `depends_on`: Node dependencies for execution order

## Parameter Substitution

Library nodes support automatic variable substitution from workflow state:

### 1. Using Previous Node Outputs

Reference outputs from other nodes using `{node_id_output}`:

```json
{
  "nodes": [
    {
      "id": "analyze",
      "agent": "analyst",
      "instruction": "Analyze the market data"
    },
    {
      "id": "save_analysis",
      "agent": "library",
      "library_name": "filesystem",
      "function_name": "write_file",
      "function_params": {
        "path": "./analysis.txt",
        "content": "{analyze_output}"  // Uses output from 'analyze' node
      },
      "depends_on": ["analyze"]
    }
  ]
}
```

### 2. Using Workflow Parameters

Reference workflow parameters using `{param_name}`:

```json
{
  "nodes": [{
    "id": "fetch",
    "agent": "library",
    "library_name": "rest_api",
    "function_name": "http_get",
    "function_params": {
      "url": "{api_endpoint}",        // From workflow parameters
      "headers": {
        "Authorization": "Bearer {api_key}"  // From workflow parameters
      }
    }
  }],
  "parameters": {
    "api_endpoint": "https://api.example.com/v1/data",
    "api_key": "sk-12345"
  }
}
```

### 3. Using State Fields

Reference workflow state fields using `{state.field_name}`:

```json
{
  "nodes": [{
    "id": "log_progress",
    "agent": "library",
    "library_name": "filesystem",
    "function_name": "write_file",
    "function_params": {
      "path": "./progress.log",
      "content": "Completed nodes: {state.completed_nodes}"
    }
  }]
}
```

### 4. Complex Substitution

Substitution works in nested structures:

```json
{
  "nodes": [{
    "id": "process",
    "agent": "library",
    "library_name": "data_processor",
    "function_name": "transform",
    "function_params": {
      "input_data": {
        "raw": "{fetch_data_output}",
        "metadata": {
          "source": "{data_source}",
          "timestamp": "{state.execution_start_time}"
        }
      },
      "options": {
        "format": "{output_format}",
        "validate": true
      }
    }
  }]
}
```

## Working with Outputs

Library node outputs are available to subsequent nodes:

### String Outputs

```json
{
  "nodes": [
    {
      "id": "read_config",
      "agent": "library",
      "library_name": "filesystem",
      "function_name": "read_file",
      "function_params": {
        "path": "./config.json"
      }
    },
    {
      "id": "process",
      "agent": "analyst",
      "instruction": "Process this configuration: {read_config_output}",
      "depends_on": ["read_config"]
    }
  ]
}
```

### JSON/Dict Outputs

When a library returns structured data, it's automatically serialized:

```json
{
  "nodes": [
    {
      "id": "fetch_json",
      "agent": "library",
      "library_name": "rest_api",
      "function_name": "http_get",
      "function_params": {
        "url": "https://api.example.com/user/123"
      }
    },
    {
      "id": "extract_email",
      "agent": "library",
      "library_name": "json_utils",
      "function_name": "extract_field",
      "function_params": {
        "data": "{fetch_json_output}",
        "field": "email"
      },
      "depends_on": ["fetch_json"]
    }
  ]
}
```

## Error Handling

### Timeout Configuration

Set timeouts at multiple levels:

```json
{
  "nodes": [{
    "id": "slow_operation",
    "agent": "library",
    "library_name": "data_processor",
    "function_name": "heavy_computation",
    "function_params": {
      "data": "{input_data}"
    },
    "timeout": 300  // Override default timeout to 5 minutes
  }]
}
```

### Conditional Routing on Errors

Use conditional edges to handle failures:

```json
{
  "nodes": [
    {
      "id": "risky_operation",
      "agent": "library",
      "library_name": "external_api",
      "function_name": "fetch_critical_data",
      "function_params": {
        "source": "primary"
      }
    },
    {
      "id": "fallback_operation",
      "agent": "library",
      "library_name": "external_api",
      "function_name": "fetch_critical_data",
      "function_params": {
        "source": "backup"
      }
    }
  ],
  "conditional_edges": [
    {
      "from_node": "risky_operation",
      "conditions": [
        {
          "field": "node_outputs",
          "operator": "contains",
          "value": "error",
          "next_node": "fallback_operation"
        }
      ],
      "default": "END"
    }
  ]
}
```

## Complete Examples

### Example 1: Data Collection and Storage

```json
{
  "name": "data_collection",
  "description": "Fetch data from API and store locally",
  "nodes": [
    {
      "id": "fetch_data",
      "agent": "library",
      "library_name": "rest_api",
      "function_name": "http_get",
      "function_params": {
        "url": "{api_url}",
        "headers": {
          "API-Key": "{api_key}"
        }
      }
    },
    {
      "id": "validate_data",
      "agent": "analyst",
      "instruction": "Validate the fetched data: {fetch_data_output}",
      "depends_on": ["fetch_data"]
    },
    {
      "id": "store_raw",
      "agent": "library",
      "library_name": "filesystem",
      "function_name": "write_json",
      "function_params": {
        "path": "{output_dir}/raw_data.json",
        "data": "{fetch_data_output}"
      },
      "depends_on": ["fetch_data"]
    },
    {
      "id": "store_validated",
      "agent": "library",
      "library_name": "filesystem",
      "function_name": "write_file",
      "function_params": {
        "path": "{output_dir}/validation_report.txt",
        "content": "{validate_data_output}"
      },
      "depends_on": ["validate_data"]
    }
  ],
  "parameters": {
    "api_url": "https://api.example.com/data",
    "api_key": "your-api-key",
    "output_dir": "./data/collections"
  }
}
```

### Example 2: Multi-Source Data Aggregation

```json
{
  "name": "multi_source_aggregation",
  "description": "Aggregate data from multiple sources",
  "nodes": [
    {
      "id": "fetch_source1",
      "agent": "library",
      "library_name": "rest_api",
      "function_name": "http_get",
      "function_params": {
        "url": "https://api1.example.com/data"
      },
      "parallel_group": "fetch"
    },
    {
      "id": "fetch_source2",
      "agent": "library",
      "library_name": "rest_api",
      "function_name": "http_get",
      "function_params": {
        "url": "https://api2.example.com/data"
      },
      "parallel_group": "fetch"
    },
    {
      "id": "read_local",
      "agent": "library",
      "library_name": "filesystem",
      "function_name": "read_json",
      "function_params": {
        "path": "./local_data.json"
      },
      "parallel_group": "fetch"
    },
    {
      "id": "aggregate",
      "agent": "analyst",
      "instruction": "Aggregate data from all sources:\nSource 1: {fetch_source1_output}\nSource 2: {fetch_source2_output}\nLocal: {read_local_output}",
      "depends_on": ["fetch_source1", "fetch_source2", "read_local"]
    },
    {
      "id": "save_report",
      "agent": "library",
      "library_name": "filesystem",
      "function_name": "write_file",
      "function_params": {
        "path": "./aggregated_report.md",
        "content": "{aggregate_output}"
      },
      "depends_on": ["aggregate"]
    }
  ]
}
```

### Example 3: Email Notification Workflow

```json
{
  "name": "email_notification",
  "description": "Process data and send email notification",
  "nodes": [
    {
      "id": "process_data",
      "agent": "analyst",
      "instruction": "Analyze the provided data: {input_data}"
    },
    {
      "id": "generate_report",
      "agent": "writer",
      "instruction": "Create an executive summary: {process_data_output}",
      "template": "executive_summary",
      "depends_on": ["process_data"]
    },
    {
      "id": "save_report",
      "agent": "library",
      "library_name": "filesystem",
      "function_name": "write_file",
      "function_params": {
        "path": "./reports/{report_name}.md",
        "content": "{generate_report_output}"
      },
      "depends_on": ["generate_report"]
    },
    {
      "id": "send_notification",
      "agent": "library",
      "library_name": "email",
      "function_name": "send_email",
      "function_params": {
        "to": "{recipient_email}",
        "subject": "Report Ready: {report_name}",
        "body": "Your report has been generated and saved.\n\nSummary:\n{generate_report_output}"
      },
      "depends_on": ["save_report"]
    }
  ],
  "parameters": {
    "input_data": "Market analysis data for Q4 2024",
    "report_name": "Q4_2024_Analysis",
    "recipient_email": "manager@company.com"
  }
}
```

## Best Practices

1. **Use Dependencies**: Always specify `depends_on` when a node needs another's output
2. **Handle Errors**: Plan for failures with conditional routing or fallback nodes
3. **Validate Inputs**: Ensure required parameters are provided in workflow parameters
4. **Set Timeouts**: Configure appropriate timeouts for long-running operations
5. **Log Progress**: Use library nodes to save intermediate results for debugging
6. **Parallel Execution**: Use `parallel_group` for independent operations
7. **Test Locally**: Test library functions independently before using in workflows

## Debugging Tips

1. **Check Library Registration**: Ensure library is properly registered:
   ```python
   from libraries.registry import get_library_registry
   registry = get_library_registry()
   print(registry.list_functions())
   ```

2. **Validate Parameters**: Test parameter substitution:
   ```python
   from libraries.executor import LibraryExecutor
   executor = LibraryExecutor()
   validated = executor._resolve_parameters(
       function_params,
       state,
       workflow_params
   )
   ```

3. **Enable Debug Logging**: Set log level to DEBUG to see substitution details:
   ```python
   import logging
   logging.getLogger("libraries").setLevel(logging.DEBUG)
   ```

## Next Steps

- [Security and capabilities](security.md)
- [Built-in libraries reference](built-in-libraries.md)
- [API Reference](api-reference.md)