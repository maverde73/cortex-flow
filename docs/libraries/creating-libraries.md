# Creating Custom Libraries

This guide walks you through creating custom libraries for use in Cortex-Flow workflows.

## Table of Contents

1. [Basic Structure](#basic-structure)
2. [Using the Decorator](#using-the-decorator)
3. [Parameter Definitions](#parameter-definitions)
4. [Return Values](#return-values)
5. [Configuration File](#configuration-file)
6. [Best Practices](#best-practices)
7. [Complete Example](#complete-example)

## Basic Structure

Every library follows this structure:

```
libraries/
└── your_library/
    ├── __init__.py       # Exports public functions
    ├── client.py         # Main implementation (or any name)
    └── config.yaml       # Library metadata and capabilities
```

## Using the Decorator

The `@library_tool` decorator registers functions for use in workflows:

```python
from libraries.base import library_tool, LibraryResponse

@library_tool(
    name="function_name",           # Required: Name used in workflows
    description="What it does",     # Optional: For documentation
    parameters={...},                # Optional: Parameter definitions
    timeout=30,                      # Optional: Execution timeout in seconds
    retries=3,                       # Optional: Number of retries on failure
    capabilities=["network_access"]  # Optional: Required capabilities
)
def your_function(param1: str, param2: int = 10):
    # Function implementation
    return LibraryResponse(
        success=True,
        data="Result data"
    )
```

## Parameter Definitions

Define parameters with type information and validation:

```python
parameters={
    "url": {
        "type": "string",      # string, integer, float, boolean, dict, list, any
        "required": True,       # Whether parameter is required
        "default": None,        # Default value if not provided
        "description": "URL to fetch",  # Documentation
        "validation": {         # Optional: Additional validation
            "pattern": "^https?://",
            "min_length": 10
        }
    },
    "timeout": {
        "type": "integer",
        "required": False,
        "default": 30,
        "description": "Request timeout"
    }
}
```

### Supported Types

- `string`: Text values
- `integer`: Whole numbers
- `float`: Decimal numbers
- `boolean`: True/False
- `dict`: JSON objects/dictionaries
- `list`: Arrays/lists
- `any`: Any type (no validation)

## Return Values

Always return a `LibraryResponse` object:

```python
from libraries.base import LibraryResponse

# Success response
return LibraryResponse(
    success=True,
    data="Any data here",  # Can be string, dict, list, etc.
    metadata={             # Optional: Additional info
        "processing_time": 1.5,
        "records_processed": 100
    }
)

# Error response
return LibraryResponse(
    success=False,
    error="What went wrong",
    metadata={"error_code": 404}
)
```

## Configuration File

Every library needs a `config.yaml`:

```yaml
name: your_library
version: 1.0.0
description: Brief description of what your library does
author: Your Name (optional)
capabilities:              # Required system capabilities
  - filesystem_read        # Read files
  - filesystem_write       # Write files
  - network_access         # Make network requests
  - system_commands        # Execute system commands
  - database_access        # Access databases
config:                    # Library-specific configuration
  api_endpoint: https://api.example.com
  max_retries: 3
  cache_ttl: 3600
```

## Best Practices

### 1. Error Handling

Always handle errors gracefully:

```python
@library_tool(name="safe_function")
def safe_function(param: str):
    try:
        # Your code here
        result = process(param)
        return LibraryResponse(success=True, data=result)
    except SpecificError as e:
        logger.error(f"Processing failed: {e}")
        return LibraryResponse(
            success=False,
            error=f"Processing failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return LibraryResponse(
            success=False,
            error="An unexpected error occurred"
        )
```

### 2. Async Functions

Use async for I/O operations:

```python
@library_tool(name="async_fetch", timeout=30)
async def async_fetch(url: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return LibraryResponse(
            success=True,
            data=response.json()
        )
```

### 3. Input Validation

Validate inputs beyond type checking:

```python
@library_tool(
    name="validated_function",
    parameters={
        "email": {
            "type": "string",
            "required": True,
            "validation": {
                "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            }
        }
    }
)
def validated_function(email: str):
    # Additional validation if needed
    if not email.endswith("@company.com"):
        return LibraryResponse(
            success=False,
            error="Only company emails are allowed"
        )

    # Process...
```

### 4. Logging

Use proper logging:

```python
import logging

logger = logging.getLogger(__name__)

@library_tool(name="logged_function")
def logged_function(param: str):
    logger.info(f"Processing: {param}")
    try:
        result = process(param)
        logger.debug(f"Result: {result}")
        return LibraryResponse(success=True, data=result)
    except Exception as e:
        logger.error(f"Failed: {e}", exc_info=True)
        return LibraryResponse(success=False, error=str(e))
```

## Complete Example

Here's a complete example of a LinkedIn integration library:

### Directory Structure

```
libraries/
└── linkedin/
    ├── __init__.py
    ├── client.py
    └── config.yaml
```

### `config.yaml`

```yaml
name: linkedin
version: 1.0.0
description: LinkedIn integration for profile data and messaging
author: Cortex Flow Team
capabilities:
  - network_access
config:
  api_base_url: https://api.linkedin.com/v2
  rate_limit: 100  # requests per minute
```

### `client.py`

```python
"""
LinkedIn Integration Library
"""

import httpx
import logging
from typing import Optional, Dict, List
from libraries.base import library_tool, LibraryResponse

logger = logging.getLogger(__name__)

@library_tool(
    name="get_profile",
    description="Fetch LinkedIn profile information",
    parameters={
        "profile_url": {
            "type": "string",
            "required": True,
            "description": "LinkedIn profile URL or username"
        },
        "fields": {
            "type": "list",
            "required": False,
            "default": ["name", "headline", "summary"],
            "description": "Fields to retrieve"
        }
    },
    timeout=30,
    capabilities=["network_access"]
)
async def get_profile(
    profile_url: str,
    fields: List[str] = None
) -> LibraryResponse:
    """
    Fetch LinkedIn profile information.

    Args:
        profile_url: LinkedIn profile URL or username
        fields: List of fields to retrieve

    Returns:
        Profile data or error
    """
    try:
        # Extract username from URL if needed
        username = extract_username(profile_url)

        # Mock API call (replace with actual LinkedIn API)
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.example.com/linkedin/{username}",
                params={"fields": ",".join(fields or [])}
            )
            response.raise_for_status()

            profile_data = response.json()

            logger.info(f"Successfully fetched profile for {username}")

            return LibraryResponse(
                success=True,
                data=profile_data,
                metadata={
                    "username": username,
                    "fields_requested": fields
                }
            )

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching profile: {e}")
        return LibraryResponse(
            success=False,
            error=f"Failed to fetch profile: HTTP {e.response.status_code}",
            metadata={"status_code": e.response.status_code}
        )
    except Exception as e:
        logger.error(f"Error fetching profile: {e}")
        return LibraryResponse(
            success=False,
            error=f"Error fetching profile: {str(e)}"
        )


@library_tool(
    name="send_message",
    description="Send a LinkedIn message",
    parameters={
        "recipient": {
            "type": "string",
            "required": True,
            "description": "Recipient's LinkedIn username or profile URL"
        },
        "subject": {
            "type": "string",
            "required": False,
            "description": "Message subject"
        },
        "body": {
            "type": "string",
            "required": True,
            "description": "Message body"
        }
    },
    timeout=30
)
async def send_message(
    recipient: str,
    body: str,
    subject: Optional[str] = None
) -> LibraryResponse:
    """
    Send a message via LinkedIn.

    Args:
        recipient: Recipient's username or profile URL
        body: Message content
        subject: Optional message subject

    Returns:
        Success status or error
    """
    try:
        username = extract_username(recipient)

        # Validate message length
        if len(body) > 1000:
            return LibraryResponse(
                success=False,
                error="Message body exceeds 1000 character limit"
            )

        # Mock sending (replace with actual implementation)
        message_data = {
            "recipient": username,
            "subject": subject,
            "body": body
        }

        # Simulate API call
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.example.com/linkedin/messages",
                json=message_data
            )
            response.raise_for_status()

        logger.info(f"Message sent to {username}")

        return LibraryResponse(
            success=True,
            data="Message sent successfully",
            metadata={
                "recipient": username,
                "message_length": len(body)
            }
        )

    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        return LibraryResponse(
            success=False,
            error=f"Failed to send message: {str(e)}"
        )


def extract_username(url_or_username: str) -> str:
    """Extract username from LinkedIn URL or return as-is."""
    if url_or_username.startswith("http"):
        # Extract from URL
        parts = url_or_username.rstrip("/").split("/")
        return parts[-1]
    return url_or_username
```

### `__init__.py`

```python
"""
LinkedIn Integration Library
"""

from libraries.linkedin.client import (
    get_profile,
    send_message
)

__all__ = [
    'get_profile',
    'send_message'
]
```

## Testing Your Library

Create a test file:

```python
# tests/test_linkedin_library.py
import pytest
from libraries.linkedin.client import get_profile, send_message

@pytest.mark.asyncio
async def test_get_profile():
    result = await get_profile("john-doe")
    assert result.success
    assert "name" in result.data

@pytest.mark.asyncio
async def test_invalid_message():
    result = await send_message(
        recipient="john-doe",
        body="x" * 1001  # Exceeds limit
    )
    assert not result.success
    assert "exceeds 1000 character limit" in result.error
```

## Next Steps

- [Using libraries in workflows](using-in-workflows.md)
- [Security and capabilities](security.md)
- [API Reference](api-reference.md)