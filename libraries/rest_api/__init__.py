"""
REST API Library

Provides functions for making HTTP requests to REST APIs.
"""

from libraries.rest_api.client import (
    http_get,
    http_post,
    http_put,
    http_delete,
    http_request
)

__all__ = [
    'http_get',
    'http_post',
    'http_put',
    'http_delete',
    'http_request'
]