# Security and Capabilities

This guide explains the security features and capability-based access control system for libraries.

## Table of Contents

1. [Capability System](#capability-system)
2. [Access Control](#access-control)
3. [Path Validation](#path-validation)
4. [Sandboxing](#sandboxing)
5. [Best Practices](#best-practices)

## Capability System

Libraries must declare required capabilities in their `config.yaml`. The system grants or denies access based on these declarations.

### Available Capabilities

| Capability | Description | Risk Level |
|------------|-------------|------------|
| `filesystem_read` | Read files from disk | Medium |
| `filesystem_write` | Write/delete files | High |
| `network_access` | Make HTTP/network requests | Medium |
| `system_commands` | Execute shell commands | Critical |
| `database_access` | Connect to databases | High |
| `email_access` | Send emails | Medium |

### Declaring Capabilities

In your library's `config.yaml`:

```yaml
name: my_library
version: 1.0.0
capabilities:
  - filesystem_read
  - network_access
```

### Granting Capabilities

Configure capabilities when initializing the executor:

```python
from libraries.registry import LibraryCapabilities
from libraries.executor import LibraryExecutor

# Grant specific capabilities
capabilities = LibraryCapabilities(
    filesystem_read=True,
    filesystem_write=False,  # Deny write access
    network_access=True
)

executor = LibraryExecutor(capabilities=capabilities)
```

### Custom Capabilities

Define custom capabilities for specialized requirements:

```python
capabilities = LibraryCapabilities(
    filesystem_read=True,
    custom_capabilities={"gpu_access", "payment_processing"}
)

# In library config.yaml
capabilities:
  - filesystem_read
  - gpu_access
  - payment_processing
```

## Access Control

### Allowlist and Blocklist

Control which libraries can be loaded:

```python
from libraries.registry import get_library_registry

registry = get_library_registry()

# Only allow specific libraries
registry.set_allowlist(["rest_api", "filesystem", "email"])

# Block dangerous libraries
registry.set_blocklist(["dangerous_lib", "untrusted_lib"])
```

### Environment-Based Configuration

Set access control via environment variables:

```bash
# .env file
LIBRARY_ALLOWLIST=rest_api,filesystem,email
LIBRARY_BLOCKLIST=dangerous_lib
LIBRARY_CAPABILITIES=filesystem_read,network_access
```

Load configuration:

```python
import os
from libraries.registry import LibraryCapabilities, get_library_registry

# Parse capabilities from environment
allowed_caps = os.getenv("LIBRARY_CAPABILITIES", "").split(",")
capabilities = LibraryCapabilities(
    filesystem_read="filesystem_read" in allowed_caps,
    filesystem_write="filesystem_write" in allowed_caps,
    network_access="network_access" in allowed_caps
)

# Apply allowlist/blocklist
registry = get_library_registry(capabilities=capabilities)

allowlist = os.getenv("LIBRARY_ALLOWLIST", "").split(",")
if allowlist[0]:  # Not empty
    registry.set_allowlist(allowlist)

blocklist = os.getenv("LIBRARY_BLOCKLIST", "").split(",")
if blocklist[0]:  # Not empty
    registry.set_blocklist(blocklist)
```

## Path Validation

The filesystem library includes built-in path validation to prevent directory traversal attacks.

### Default Allowed Paths

```python
# libraries/filesystem/operations.py
ALLOWED_PATHS = [
    "/tmp",
    "./data",
    "./output"
]
```

### Configuring Allowed Paths

Override allowed paths in your library:

```python
import libraries.filesystem.operations as fs_ops

# Set custom allowed paths
fs_ops.ALLOWED_PATHS = [
    "/app/data",
    "/app/uploads",
    "/app/exports"
]
```

### Path Validation Example

```python
def _validate_path(path: str) -> bool:
    """Validate that a path is within allowed directories."""
    abs_path = os.path.abspath(path)

    for allowed in ALLOWED_PATHS:
        allowed_abs = os.path.abspath(allowed)
        if abs_path.startswith(allowed_abs):
            return True

    return False

@library_tool(name="read_file")
def read_file(path: str):
    if not _validate_path(path):
        return LibraryResponse(
            success=False,
            error=f"Path '{path}' is not in allowed directories"
        )

    # Safe to proceed
    with open(path, 'r') as f:
        content = f.read()

    return LibraryResponse(success=True, data=content)
```

## Sandboxing

### Resource Limits

Set resource limits for library execution:

```python
# In workflow engine or configuration
LIBRARY_LIMITS = {
    "max_memory": 512 * 1024 * 1024,  # 512 MB
    "max_cpu_time": 30,                # 30 seconds
    "max_file_size": 10 * 1024 * 1024, # 10 MB
    "max_open_files": 100
}
```

### Timeout Enforcement

Libraries automatically support timeouts:

```python
@library_tool(
    name="long_operation",
    timeout=60  # 60 second timeout
)
async def long_operation(data: str):
    # Will be killed if exceeds 60 seconds
    result = await process_data(data)
    return LibraryResponse(success=True, data=result)
```

### Process Isolation (Advanced)

For critical security, run libraries in isolated processes:

```python
import subprocess
import json

def execute_in_sandbox(library_name: str, function_name: str, params: dict):
    """Execute library function in isolated process."""

    # Create sandbox script
    script = f"""
import sys
import json
from libraries.{library_name} import {function_name}

params = json.loads(sys.argv[1])
result = {function_name}(**params)
print(json.dumps(result.dict()))
"""

    # Run in subprocess with resource limits
    proc = subprocess.Popen(
        ["python", "-c", script, json.dumps(params)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=lambda: resource.setrlimit(
            resource.RLIMIT_AS,
            (LIBRARY_LIMITS["max_memory"], LIBRARY_LIMITS["max_memory"])
        )
    )

    try:
        stdout, stderr = proc.communicate(timeout=30)
        if proc.returncode == 0:
            return json.loads(stdout)
        else:
            return {"success": False, "error": stderr.decode()}
    except subprocess.TimeoutExpired:
        proc.kill()
        return {"success": False, "error": "Function timed out"}
```

## Best Practices

### 1. Principle of Least Privilege

Only grant the minimum capabilities required:

```python
# Bad: Grant all capabilities
capabilities = LibraryCapabilities(
    filesystem_read=True,
    filesystem_write=True,
    network_access=True,
    system_commands=True,
    database_access=True
)

# Good: Grant only what's needed
capabilities = LibraryCapabilities(
    filesystem_read=True,
    network_access=True
)
```

### 2. Input Sanitization

Always sanitize inputs in your library functions:

```python
import re
import html

@library_tool(name="process_user_input")
def process_user_input(user_data: str):
    # Sanitize HTML
    safe_data = html.escape(user_data)

    # Remove potentially dangerous patterns
    safe_data = re.sub(r'<script.*?</script>', '', safe_data, flags=re.DOTALL)

    # Validate against whitelist
    if not re.match(r'^[a-zA-Z0-9\s\-_.]+$', safe_data):
        return LibraryResponse(
            success=False,
            error="Input contains invalid characters"
        )

    # Process safe data
    return LibraryResponse(success=True, data=process(safe_data))
```

### 3. Secure Credential Handling

Never hardcode credentials:

```python
import os
from typing import Optional

@library_tool(
    name="api_call",
    parameters={
        "endpoint": {"type": "string", "required": True}
    }
)
def api_call(endpoint: str, api_key: Optional[str] = None):
    # Get API key from environment or parameter
    key = api_key or os.getenv("API_KEY")

    if not key:
        return LibraryResponse(
            success=False,
            error="API key not provided"
        )

    # Use the key securely
    headers = {"Authorization": f"Bearer {key}"}
    # Make API call...
```

### 4. Audit Logging

Log all security-relevant operations:

```python
import logging
from datetime import datetime

security_logger = logging.getLogger("security")

@library_tool(name="sensitive_operation")
def sensitive_operation(user_id: str, action: str):
    # Log the operation
    security_logger.info(
        f"SECURITY: User {user_id} performing {action} at {datetime.now()}"
    )

    try:
        result = perform_action(action)
        security_logger.info(f"SECURITY: Action {action} succeeded for {user_id}")
        return LibraryResponse(success=True, data=result)
    except Exception as e:
        security_logger.error(
            f"SECURITY: Action {action} failed for {user_id}: {e}"
        )
        return LibraryResponse(success=False, error=str(e))
```

### 5. Rate Limiting

Implement rate limiting for resource-intensive operations:

```python
from collections import defaultdict
from time import time

rate_limits = defaultdict(list)
MAX_REQUESTS_PER_MINUTE = 60

@library_tool(name="rate_limited_function")
def rate_limited_function(user_id: str, data: str):
    # Check rate limit
    now = time()
    user_requests = rate_limits[user_id]

    # Remove old requests
    user_requests = [t for t in user_requests if now - t < 60]

    if len(user_requests) >= MAX_REQUESTS_PER_MINUTE:
        return LibraryResponse(
            success=False,
            error="Rate limit exceeded. Try again later."
        )

    # Record this request
    user_requests.append(now)
    rate_limits[user_id] = user_requests

    # Process request
    return LibraryResponse(success=True, data=process(data))
```

## Security Checklist

Before deploying a library:

- [ ] Declare all required capabilities in `config.yaml`
- [ ] Implement input validation and sanitization
- [ ] Use path validation for filesystem operations
- [ ] Store credentials in environment variables
- [ ] Implement appropriate timeouts
- [ ] Add rate limiting for expensive operations
- [ ] Log security-relevant events
- [ ] Test with minimal capabilities
- [ ] Review for injection vulnerabilities
- [ ] Document security considerations

## Vulnerability Reporting

If you discover a security vulnerability:

1. Do not disclose publicly
2. Email security@cortexflow.ai with details
3. Include steps to reproduce
4. Allow time for patching before disclosure

## Next Steps

- [Built-in libraries reference](built-in-libraries.md)
- [Creating secure libraries](creating-libraries.md)
- [API Reference](api-reference.md)