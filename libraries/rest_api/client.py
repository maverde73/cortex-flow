"""
REST API Client Library

Provides HTTP request functions for interacting with REST APIs.
"""

import httpx
import json
import logging
from typing import Optional, Dict, Any, Union

from libraries.base import library_tool, LibraryResponse

logger = logging.getLogger(__name__)


@library_tool(
    name="http_get",
    description="Make an HTTP GET request",
    parameters={
        "url": {"type": "string", "required": True, "description": "URL to request"},
        "headers": {"type": "dict", "required": False, "description": "Request headers"},
        "params": {"type": "dict", "required": False, "description": "Query parameters"},
        "timeout": {"type": "integer", "required": False, "default": 30, "description": "Request timeout in seconds"}
    },
    timeout=30
)
async def http_get(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    timeout: int = 30
) -> LibraryResponse:
    """
    Make an HTTP GET request to the specified URL.

    Args:
        url: URL to request
        headers: Optional request headers
        params: Optional query parameters
        timeout: Request timeout in seconds

    Returns:
        LibraryResponse with response data
    """
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(
                url,
                headers=headers,
                params=params
            )

            response.raise_for_status()

            # Try to parse as JSON
            try:
                data = response.json()
            except json.JSONDecodeError:
                data = response.text

            return LibraryResponse(
                success=True,
                data=data,
                metadata={
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "url": str(response.url)
                }
            )

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error: {e}")
        return LibraryResponse(
            success=False,
            error=f"HTTP {e.response.status_code}: {e.response.text}",
            metadata={"status_code": e.response.status_code}
        )

    except Exception as e:
        logger.error(f"Request failed: {e}")
        return LibraryResponse(
            success=False,
            error=str(e)
        )


@library_tool(
    name="http_post",
    description="Make an HTTP POST request",
    parameters={
        "url": {"type": "string", "required": True, "description": "URL to request"},
        "json_data": {"type": "dict", "required": False, "description": "JSON data to send"},
        "data": {"type": "dict", "required": False, "description": "Form data to send"},
        "headers": {"type": "dict", "required": False, "description": "Request headers"},
        "timeout": {"type": "integer", "required": False, "default": 30, "description": "Request timeout in seconds"}
    },
    timeout=30
)
async def http_post(
    url: str,
    json_data: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 30
) -> LibraryResponse:
    """
    Make an HTTP POST request to the specified URL.

    Args:
        url: URL to request
        json_data: JSON data to send in request body
        data: Form data to send in request body
        headers: Optional request headers
        timeout: Request timeout in seconds

    Returns:
        LibraryResponse with response data
    """
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            kwargs = {"headers": headers}

            if json_data is not None:
                kwargs["json"] = json_data
            elif data is not None:
                kwargs["data"] = data

            response = await client.post(url, **kwargs)
            response.raise_for_status()

            # Try to parse as JSON
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                response_data = response.text

            return LibraryResponse(
                success=True,
                data=response_data,
                metadata={
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "url": str(response.url)
                }
            )

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error: {e}")
        return LibraryResponse(
            success=False,
            error=f"HTTP {e.response.status_code}: {e.response.text}",
            metadata={"status_code": e.response.status_code}
        )

    except Exception as e:
        logger.error(f"Request failed: {e}")
        return LibraryResponse(
            success=False,
            error=str(e)
        )


@library_tool(
    name="http_put",
    description="Make an HTTP PUT request",
    parameters={
        "url": {"type": "string", "required": True, "description": "URL to request"},
        "json_data": {"type": "dict", "required": False, "description": "JSON data to send"},
        "data": {"type": "dict", "required": False, "description": "Form data to send"},
        "headers": {"type": "dict", "required": False, "description": "Request headers"},
        "timeout": {"type": "integer", "required": False, "default": 30, "description": "Request timeout in seconds"}
    },
    timeout=30
)
async def http_put(
    url: str,
    json_data: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 30
) -> LibraryResponse:
    """
    Make an HTTP PUT request to the specified URL.

    Args:
        url: URL to request
        json_data: JSON data to send in request body
        data: Form data to send in request body
        headers: Optional request headers
        timeout: Request timeout in seconds

    Returns:
        LibraryResponse with response data
    """
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            kwargs = {"headers": headers}

            if json_data is not None:
                kwargs["json"] = json_data
            elif data is not None:
                kwargs["data"] = data

            response = await client.put(url, **kwargs)
            response.raise_for_status()

            # Try to parse as JSON
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                response_data = response.text

            return LibraryResponse(
                success=True,
                data=response_data,
                metadata={
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "url": str(response.url)
                }
            )

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error: {e}")
        return LibraryResponse(
            success=False,
            error=f"HTTP {e.response.status_code}: {e.response.text}",
            metadata={"status_code": e.response.status_code}
        )

    except Exception as e:
        logger.error(f"Request failed: {e}")
        return LibraryResponse(
            success=False,
            error=str(e)
        )


@library_tool(
    name="http_delete",
    description="Make an HTTP DELETE request",
    parameters={
        "url": {"type": "string", "required": True, "description": "URL to request"},
        "headers": {"type": "dict", "required": False, "description": "Request headers"},
        "timeout": {"type": "integer", "required": False, "default": 30, "description": "Request timeout in seconds"}
    },
    timeout=30
)
async def http_delete(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 30
) -> LibraryResponse:
    """
    Make an HTTP DELETE request to the specified URL.

    Args:
        url: URL to request
        headers: Optional request headers
        timeout: Request timeout in seconds

    Returns:
        LibraryResponse with response data
    """
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.delete(
                url,
                headers=headers
            )

            response.raise_for_status()

            # Try to parse as JSON
            try:
                data = response.json() if response.text else None
            except json.JSONDecodeError:
                data = response.text

            return LibraryResponse(
                success=True,
                data=data,
                metadata={
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "url": str(response.url)
                }
            )

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error: {e}")
        return LibraryResponse(
            success=False,
            error=f"HTTP {e.response.status_code}: {e.response.text}",
            metadata={"status_code": e.response.status_code}
        )

    except Exception as e:
        logger.error(f"Request failed: {e}")
        return LibraryResponse(
            success=False,
            error=str(e)
        )


@library_tool(
    name="http_request",
    description="Make a generic HTTP request with any method",
    parameters={
        "method": {"type": "string", "required": True, "description": "HTTP method (GET, POST, PUT, DELETE, PATCH, etc.)"},
        "url": {"type": "string", "required": True, "description": "URL to request"},
        "json_data": {"type": "dict", "required": False, "description": "JSON data to send"},
        "data": {"type": "dict", "required": False, "description": "Form data to send"},
        "headers": {"type": "dict", "required": False, "description": "Request headers"},
        "params": {"type": "dict", "required": False, "description": "Query parameters"},
        "timeout": {"type": "integer", "required": False, "default": 30, "description": "Request timeout in seconds"}
    },
    timeout=30
)
async def http_request(
    method: str,
    url: str,
    json_data: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    timeout: int = 30
) -> LibraryResponse:
    """
    Make a generic HTTP request with any method.

    Args:
        method: HTTP method (GET, POST, PUT, DELETE, PATCH, etc.)
        url: URL to request
        json_data: JSON data to send in request body
        data: Form data to send in request body
        headers: Optional request headers
        params: Optional query parameters
        timeout: Request timeout in seconds

    Returns:
        LibraryResponse with response data
    """
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            kwargs = {
                "headers": headers,
                "params": params
            }

            if json_data is not None:
                kwargs["json"] = json_data
            elif data is not None:
                kwargs["data"] = data

            response = await client.request(
                method.upper(),
                url,
                **kwargs
            )

            response.raise_for_status()

            # Try to parse as JSON
            try:
                response_data = response.json() if response.text else None
            except json.JSONDecodeError:
                response_data = response.text

            return LibraryResponse(
                success=True,
                data=response_data,
                metadata={
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "url": str(response.url),
                    "method": method.upper()
                }
            )

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error: {e}")
        return LibraryResponse(
            success=False,
            error=f"HTTP {e.response.status_code}: {e.response.text}",
            metadata={"status_code": e.response.status_code}
        )

    except Exception as e:
        logger.error(f"Request failed: {e}")
        return LibraryResponse(
            success=False,
            error=str(e)
        )