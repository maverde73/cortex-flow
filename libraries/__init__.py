"""
Libraries Module for Cortex Flow

This module provides a standardized way to integrate custom Python libraries
into workflows. Libraries can expose functions that can be called from
workflow nodes using the "library" agent type.

Features:
- Decorator-based function registration
- Type validation
- Async/sync support
- Metadata configuration
- Sandboxed execution
"""

from libraries.base import (
    library_tool,
    LibraryResponse,
    LibraryError,
    LibraryMetadata,
    LibraryFunction
)

__all__ = [
    'library_tool',
    'LibraryResponse',
    'LibraryError',
    'LibraryMetadata',
    'LibraryFunction'
]