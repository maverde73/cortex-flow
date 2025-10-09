# Library System API Reference

Complete API reference for the Cortex-Flow Library System.

## Table of Contents

1. [Base Module](#base-module)
2. [Registry Module](#registry-module)
3. [Executor Module](#executor-module)
4. [Workflow Integration](#workflow-integration)

---

## Base Module

**Module**: `libraries.base`

### Classes

#### `LibraryResponse`

Standard response format for library functions.

```python
class LibraryResponse(BaseModel):
    success: bool           # Whether the operation succeeded
    data: Any = None        # The result data
    error: Optional[str]    # Error message if failed
    metadata: Dict[str, Any] # Additional metadata
```

**Example:**
```python
return LibraryResponse(
    success=True,
    data={"result": "value"},
    metadata={"processing_time": 1.5}
)
```

#### `LibraryError`

Custom exception for library errors.

```python
class LibraryError(Exception):
    """Raised when library operations fail."""
    pass
```

#### `ParameterType`

Enum of supported parameter types.

```python
class ParameterType(Enum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DICT = "dict"
    LIST = "list"
    ANY = "any"
```

#### `ParameterDefinition`

Definition for function parameters.

```python
class ParameterDefinition(BaseModel):
    type: ParameterType
    required: bool = True
    default: Any = None
    description: Optional[str]
    validation: Optional[Dict[str, Any]]
```

#### `LibraryMetadata`

Metadata for a library module.

```python
class LibraryMetadata(BaseModel):
    name: str
    version: str = "1.0.0"
    description: str
    author: Optional[str]
    capabilities: List[str]
    config: Dict[str, Any]
```

#### `LibraryFunction`

Represents a registered library function.

```python
class LibraryFunction:
    name: str
    func: Callable
    description: str
    parameters: Dict[str, ParameterDefinition]
    is_async: bool
    timeout: Optional[int]
    retries: int
    capabilities_required: List[str]

    def validate_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]
    async def execute(self, params: Dict[str, Any]) -> LibraryResponse
```

### Decorators

#### `@library_tool`

Decorator to register functions as library tools.

```python
@library_tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    parameters: Optional[Dict[str, Union[Dict, ParameterDefinition]]] = None,
    timeout: Optional[int] = None,
    retries: int = 0,
    capabilities: Optional[List[str]] = None
) -> Callable
```

**Parameters:**
- `name`: Tool name (defaults to function name)
- `description`: Tool description (defaults to docstring)
- `parameters`: Parameter definitions
- `timeout`: Execution timeout in seconds
- `retries`: Number of retry attempts on failure
- `capabilities`: Required capabilities

**Example:**
```python
@library_tool(
    name="process_data",
    description="Process input data",
    parameters={
        "data": {"type": "dict", "required": True},
        "format": {"type": "string", "default": "json"}
    },
    timeout=30
)
async def process_data(data: dict, format: str = "json"):
    # Implementation
    return LibraryResponse(success=True, data=result)
```

### Functions

#### `get_registered_libraries()`

Get all registered library functions.

```python
def get_registered_libraries() -> Dict[str, Dict[str, LibraryFunction]]
```

**Returns:** Dictionary mapping library names to their functions

#### `get_library_function()`

Get a specific library function.

```python
def get_library_function(
    library_name: str,
    function_name: str
) -> Optional[LibraryFunction]
```

**Parameters:**
- `library_name`: Name of the library
- `function_name`: Name of the function

**Returns:** LibraryFunction if found, None otherwise

#### `clear_registry()`

Clear the library registry.

```python
def clear_registry() -> None
```

---

## Registry Module

**Module**: `libraries.registry`

### Classes

#### `LibraryCapabilities`

Defines capabilities that libraries can require.

```python
class LibraryCapabilities:
    filesystem_read: bool = False
    filesystem_write: bool = False
    network_access: bool = False
    system_commands: bool = False
    database_access: bool = False
    email_access: bool = False
    custom_capabilities: Set[str]

    def has_capability(self, capability: str) -> bool
    def validate_required(self, required: List[str]) -> bool
```

**Example:**
```python
capabilities = LibraryCapabilities(
    filesystem_read=True,
    network_access=True,
    custom_capabilities={"gpu_access"}
)
```

#### `LibraryRegistry`

Manages library discovery, loading, and access control.

```python
class LibraryRegistry:
    def __init__(
        self,
        libraries_dir: Optional[Path] = None,
        capabilities: Optional[LibraryCapabilities] = None,
        auto_discover: bool = True
    )

    def discover_libraries(self) -> Dict[str, LibraryMetadata]
    def load_library(self, library_name: str) -> bool
    def load_all_libraries(self) -> int
    def get_library_function(
        self,
        library_name: str,
        function_name: str
    ) -> Optional[LibraryFunction]
    def list_functions(
        self,
        library_name: Optional[str] = None
    ) -> Dict[str, List[str]]
    def set_blocklist(self, libraries: List[str]) -> None
    def set_allowlist(self, libraries: Optional[List[str]]) -> None
    def get_metadata(self, library_name: str) -> Optional[LibraryMetadata]
    def validate_library(self, library_name: str) -> bool
    def clear_cache(self) -> None
```

**Example:**
```python
registry = LibraryRegistry(
    libraries_dir=Path("./libraries"),
    capabilities=LibraryCapabilities(filesystem_read=True)
)

# Discover and load
registry.discover_libraries()
registry.load_library("rest_api")

# Get function
func = registry.get_library_function("rest_api", "http_get")
```

### Functions

#### `get_library_registry()`

Get or create the global library registry.

```python
def get_library_registry(
    libraries_dir: Optional[Path] = None,
    capabilities: Optional[LibraryCapabilities] = None,
    reset: bool = False
) -> LibraryRegistry
```

**Parameters:**
- `libraries_dir`: Directory containing libraries
- `capabilities`: Granted capabilities
- `reset`: Whether to reset existing registry

**Returns:** LibraryRegistry instance

---

## Executor Module

**Module**: `libraries.executor`

### Classes

#### `LibraryExecutor`

Executes library functions within workflow context.

```python
class LibraryExecutor:
    def __init__(
        self,
        registry: Optional[LibraryRegistry] = None,
        capabilities: Optional[LibraryCapabilities] = None,
        libraries_dir: Optional[Path] = None
    )

    async def execute_library_node(
        self,
        node: WorkflowNode,
        state: WorkflowState,
        params: Optional[Dict[str, Any]] = None
    ) -> str

    def list_available_functions(self) -> Dict[str, list]

    def validate_node(self, node: WorkflowNode) -> bool
```

**Example:**
```python
executor = LibraryExecutor(
    capabilities=LibraryCapabilities(network_access=True)
)

result = await executor.execute_library_node(
    node=WorkflowNode(
        id="fetch",
        agent="library",
        library_name="rest_api",
        function_name="http_get",
        function_params={"url": "https://api.example.com"}
    ),
    state=WorkflowState(),
    params={}
)
```

### Functions

#### `get_library_executor()`

Get or create the global library executor.

```python
def get_library_executor(
    capabilities: Optional[LibraryCapabilities] = None,
    libraries_dir: Optional[Path] = None,
    reset: bool = False
) -> LibraryExecutor
```

---

## Workflow Integration

### WorkflowNode Schema

When `agent="library"`, the node requires:

```python
class WorkflowNode(BaseModel):
    id: str
    agent: Literal["library"]
    instruction: str  # Optional, for logging
    library_name: str  # Required
    function_name: str  # Required
    function_params: Dict[str, Any]  # Required
    timeout: Optional[int]
    depends_on: Optional[List[str]]
```

### Variable Substitution

The executor supports variable substitution in `function_params`:

| Pattern | Description | Example |
|---------|-------------|---------|
| `{node_id_output}` | Output from previous node | `{analyze_output}` |
| `{param_name}` | Workflow parameter | `{api_key}` |
| `{state.field}` | State field value | `{state.completed_nodes}` |

### Example Workflow

```json
{
  "name": "api_workflow",
  "nodes": [
    {
      "id": "fetch_data",
      "agent": "library",
      "library_name": "rest_api",
      "function_name": "http_get",
      "function_params": {
        "url": "{api_endpoint}",
        "headers": {
          "Authorization": "Bearer {api_token}"
        }
      }
    },
    {
      "id": "save_data",
      "agent": "library",
      "library_name": "filesystem",
      "function_name": "write_json",
      "function_params": {
        "path": "./output/data.json",
        "data": "{fetch_data_output}"
      },
      "depends_on": ["fetch_data"]
    }
  ],
  "parameters": {
    "api_endpoint": "https://api.example.com/data",
    "api_token": "secret-token"
  }
}
```

### Error Handling

Library execution errors are captured in the workflow:

```python
try:
    output = await executor.execute_library_node(node, state, params)
except LibraryError as e:
    # Logged to workflow history
    # Node marked as failed
    # Error available in WorkflowResult
```

### State Updates

After library execution:
- `state.node_outputs[node.id]` contains the output
- `state.completed_nodes` includes the node ID
- `state.workflow_history` has execution log entry

---

## Complete Example

### Creating a Custom Library

```python
# libraries/data_processor/__init__.py
from libraries.data_processor.processor import transform_data, validate_data

__all__ = ['transform_data', 'validate_data']
```

```python
# libraries/data_processor/processor.py
from libraries.base import library_tool, LibraryResponse
import pandas as pd

@library_tool(
    name="transform_data",
    description="Transform data according to rules",
    parameters={
        "data": {"type": "list", "required": True},
        "rules": {"type": "dict", "required": True},
        "output_format": {
            "type": "string",
            "required": False,
            "default": "json"
        }
    },
    timeout=60
)
async def transform_data(
    data: list,
    rules: dict,
    output_format: str = "json"
):
    try:
        # Create DataFrame
        df = pd.DataFrame(data)

        # Apply transformations based on rules
        for column, rule in rules.items():
            if rule["operation"] == "rename":
                df.rename(columns={column: rule["to"]}, inplace=True)
            elif rule["operation"] == "convert":
                df[column] = df[column].astype(rule["type"])
            elif rule["operation"] == "filter":
                df = df[df[column].apply(rule["condition"])]

        # Format output
        if output_format == "json":
            result = df.to_json(orient="records")
        elif output_format == "csv":
            result = df.to_csv(index=False)
        else:
            result = df.to_dict(orient="records")

        return LibraryResponse(
            success=True,
            data=result,
            metadata={
                "rows_processed": len(df),
                "columns": list(df.columns)
            }
        )

    except Exception as e:
        return LibraryResponse(
            success=False,
            error=f"Transform failed: {str(e)}"
        )
```

```yaml
# libraries/data_processor/config.yaml
name: data_processor
version: 1.0.0
description: Data transformation and validation library
capabilities: []
config:
  max_rows: 1000000
  supported_formats:
    - json
    - csv
    - dict
```

### Using in Workflow

```json
{
  "name": "data_pipeline",
  "nodes": [
    {
      "id": "load_data",
      "agent": "library",
      "library_name": "filesystem",
      "function_name": "read_json",
      "function_params": {
        "path": "./input/raw_data.json"
      }
    },
    {
      "id": "transform",
      "agent": "library",
      "library_name": "data_processor",
      "function_name": "transform_data",
      "function_params": {
        "data": "{load_data_output}",
        "rules": {
          "old_name": {
            "operation": "rename",
            "to": "new_name"
          },
          "amount": {
            "operation": "convert",
            "type": "float"
          }
        },
        "output_format": "csv"
      },
      "depends_on": ["load_data"]
    },
    {
      "id": "save_result",
      "agent": "library",
      "library_name": "filesystem",
      "function_name": "write_file",
      "function_params": {
        "path": "./output/transformed.csv",
        "content": "{transform_output}"
      },
      "depends_on": ["transform"]
    }
  ]
}
```

---

## Migration Guide

### From Direct Code to Libraries

**Before (direct code):**
```python
# In workflow engine
import requests
response = requests.get(url)
data = response.json()
```

**After (library):**
```python
# In library
@library_tool(name="fetch_json")
async def fetch_json(url: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return LibraryResponse(
            success=True,
            data=response.json()
        )
```

### From MCP Tools to Libraries

**Before (MCP tool):**
```json
{
  "agent": "mcp_tool",
  "tool_name": "custom_processor",
  "params": {"data": "..."}
}
```

**After (library):**
```json
{
  "agent": "library",
  "library_name": "data_processor",
  "function_name": "process",
  "function_params": {"data": "..."}
}
```

---

## Best Practices

1. **Always return LibraryResponse**: Ensures consistent error handling
2. **Use async for I/O**: Better performance and non-blocking
3. **Validate inputs**: Check types and ranges before processing
4. **Set appropriate timeouts**: Prevent hanging operations
5. **Log operations**: Use logging for debugging and monitoring
6. **Handle errors gracefully**: Return informative error messages
7. **Document parameters**: Clear descriptions and examples
8. **Test thoroughly**: Unit tests for all functions
9. **Use type hints**: Improves IDE support and documentation
10. **Follow naming conventions**: snake_case for functions, PascalCase for classes