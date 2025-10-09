# Library System Documentation

## Overview

The Library System in Cortex-Flow provides a standardized way to integrate custom Python libraries into workflows. This allows workflows to use any Python functionality beyond the built-in agents and MCP tools, such as making REST API calls, file operations, sending emails, or integrating with third-party services.

## Key Features

- **Decorator-based Registration**: Simple `@library_tool` decorator to expose functions
- **Type Validation**: Automatic parameter validation using Pydantic
- **Async/Sync Support**: Works with both synchronous and asynchronous functions
- **Security Controls**: Capability-based access control and path validation
- **Variable Substitution**: Automatic substitution from workflow state
- **Error Handling**: Built-in timeout, retry logic, and error reporting

## Quick Example

```python
# libraries/email/client.py
from libraries.base import library_tool, LibraryResponse

@library_tool(
    name="send_email",
    description="Send an email notification",
    parameters={
        "to": {"type": "string", "required": True},
        "subject": {"type": "string", "required": True},
        "body": {"type": "string", "required": True}
    },
    timeout=30
)
async def send_email(to: str, subject: str, body: str):
    # Implementation here
    return LibraryResponse(
        success=True,
        data="Email sent successfully"
    )
```

Use in workflow:
```json
{
  "nodes": [{
    "id": "notify",
    "agent": "library",
    "library_name": "email",
    "function_name": "send_email",
    "function_params": {
      "to": "user@example.com",
      "subject": "Workflow Complete",
      "body": "{workflow_result}"
    }
  }]
}
```

## Documentation Index

- [**Creating Libraries**](creating-libraries.md) - Step-by-step guide to create custom libraries
- [**Using Libraries in Workflows**](using-in-workflows.md) - How to use library nodes in workflows
- [**Security & Capabilities**](security.md) - Access control and security features
- [**Built-in Libraries**](built-in-libraries.md) - Reference for included libraries
- [**API Reference**](api-reference.md) - Complete API documentation

## Why Use Libraries?

Libraries fill the gap between:
- **Agents** (AI-powered reasoning tasks)
- **MCP Tools** (external tool servers)
- **Custom Code** (direct Python functionality)

They provide a clean, reusable way to add any Python functionality to your workflows without modifying the core system.

## Architecture

```
libraries/
├── base.py           # Core decorators and base classes
├── registry.py       # Discovery and loading system
├── executor.py       # Execution engine
├── rest_api/         # Built-in REST API library
│   ├── __init__.py
│   ├── client.py     # HTTP functions
│   └── config.yaml   # Library metadata
├── filesystem/       # Built-in filesystem library
│   ├── __init__.py
│   ├── operations.py # File operations
│   └── config.yaml   # Library metadata
└── custom/           # Your custom libraries
    └── ...
```

## Next Steps

- [Create your first library](creating-libraries.md)
- [Explore built-in libraries](built-in-libraries.md)
- [Learn about security](security.md)