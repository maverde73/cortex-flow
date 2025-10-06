"""
Shared HTTP client configuration for inter-agent communication.

Uses httpx AsyncClient with connection pooling for optimal performance.
"""

import httpx
from typing import Optional
from config import settings


class HTTPClientManager:
    """
    Manages a shared AsyncClient instance for efficient HTTP communication.

    This implements the singleton pattern to reuse connections across requests.
    """

    _client: Optional[httpx.AsyncClient] = None

    @classmethod
    def get_client(cls) -> httpx.AsyncClient:
        """
        Get or create the shared AsyncClient instance.

        Returns:
            Configured httpx.AsyncClient with connection pooling
        """
        if cls._client is None:
            limits = httpx.Limits(
                max_connections=settings.http_max_connections,
                max_keepalive_connections=settings.http_max_keepalive_connections
            )

            cls._client = httpx.AsyncClient(
                timeout=httpx.Timeout(settings.http_timeout),
                limits=limits,
                follow_redirects=True
            )

        return cls._client

    @classmethod
    async def close_client(cls):
        """Close the shared client and cleanup connections."""
        if cls._client is not None:
            await cls._client.aclose()
            cls._client = None


# Convenience function for getting the client
def get_http_client() -> httpx.AsyncClient:
    """Get the shared HTTP client instance."""
    return HTTPClientManager.get_client()
