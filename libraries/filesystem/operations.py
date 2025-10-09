"""
Filesystem Operations Library

Provides safe filesystem operations with path validation.
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Union

from libraries.base import library_tool, LibraryResponse

logger = logging.getLogger(__name__)

# Default allowed paths (can be overridden via config)
ALLOWED_PATHS = ["/tmp", "./data", "./output"]
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def _validate_path(path: str) -> bool:
    """Validate that a path is within allowed directories."""
    abs_path = os.path.abspath(path)

    for allowed in ALLOWED_PATHS:
        allowed_abs = os.path.abspath(allowed)
        if abs_path.startswith(allowed_abs):
            return True

    return False


@library_tool(
    name="read_file",
    description="Read contents of a text file",
    parameters={
        "path": {"type": "string", "required": True, "description": "Path to the file"},
        "encoding": {"type": "string", "required": False, "default": "utf-8", "description": "File encoding"}
    }
)
def read_file(path: str, encoding: str = "utf-8") -> LibraryResponse:
    """
    Read the contents of a text file.

    Args:
        path: Path to the file
        encoding: File encoding

    Returns:
        LibraryResponse with file contents
    """
    try:
        if not _validate_path(path):
            return LibraryResponse(
                success=False,
                error=f"Path '{path}' is not in allowed directories"
            )

        if not os.path.exists(path):
            return LibraryResponse(
                success=False,
                error=f"File not found: {path}"
            )

        # Check file size
        file_size = os.path.getsize(path)
        if file_size > MAX_FILE_SIZE:
            return LibraryResponse(
                success=False,
                error=f"File too large: {file_size} bytes (max: {MAX_FILE_SIZE})"
            )

        with open(path, 'r', encoding=encoding) as f:
            content = f.read()

        return LibraryResponse(
            success=True,
            data=content,
            metadata={
                "path": path,
                "size": file_size,
                "encoding": encoding
            }
        )

    except Exception as e:
        logger.error(f"Error reading file: {e}")
        return LibraryResponse(
            success=False,
            error=str(e)
        )


@library_tool(
    name="write_file",
    description="Write content to a text file",
    parameters={
        "path": {"type": "string", "required": True, "description": "Path to the file"},
        "content": {"type": "string", "required": True, "description": "Content to write"},
        "encoding": {"type": "string", "required": False, "default": "utf-8", "description": "File encoding"},
        "append": {"type": "boolean", "required": False, "default": False, "description": "Append to existing file"}
    }
)
def write_file(
    path: str,
    content: str,
    encoding: str = "utf-8",
    append: bool = False
) -> LibraryResponse:
    """
    Write content to a text file.

    Args:
        path: Path to the file
        content: Content to write
        encoding: File encoding
        append: Whether to append to existing file

    Returns:
        LibraryResponse indicating success
    """
    try:
        if not _validate_path(path):
            return LibraryResponse(
                success=False,
                error=f"Path '{path}' is not in allowed directories"
            )

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

        mode = 'a' if append else 'w'
        with open(path, mode, encoding=encoding) as f:
            f.write(content)

        return LibraryResponse(
            success=True,
            data=f"File written successfully: {path}",
            metadata={
                "path": path,
                "size": len(content),
                "append": append
            }
        )

    except Exception as e:
        logger.error(f"Error writing file: {e}")
        return LibraryResponse(
            success=False,
            error=str(e)
        )


@library_tool(
    name="list_files",
    description="List files in a directory",
    parameters={
        "path": {"type": "string", "required": True, "description": "Directory path"},
        "pattern": {"type": "string", "required": False, "default": "*", "description": "File pattern to match"},
        "recursive": {"type": "boolean", "required": False, "default": False, "description": "Search recursively"}
    }
)
def list_files(
    path: str,
    pattern: str = "*",
    recursive: bool = False
) -> LibraryResponse:
    """
    List files in a directory.

    Args:
        path: Directory path
        pattern: File pattern to match (e.g., "*.txt")
        recursive: Whether to search recursively

    Returns:
        LibraryResponse with list of files
    """
    try:
        if not _validate_path(path):
            return LibraryResponse(
                success=False,
                error=f"Path '{path}' is not in allowed directories"
            )

        if not os.path.exists(path):
            return LibraryResponse(
                success=False,
                error=f"Directory not found: {path}"
            )

        p = Path(path)
        if recursive:
            files = list(p.rglob(pattern))
        else:
            files = list(p.glob(pattern))

        # Convert to relative paths
        file_list = [str(f.relative_to(path)) for f in files if f.is_file()]

        return LibraryResponse(
            success=True,
            data=file_list,
            metadata={
                "path": path,
                "pattern": pattern,
                "count": len(file_list),
                "recursive": recursive
            }
        )

    except Exception as e:
        logger.error(f"Error listing files: {e}")
        return LibraryResponse(
            success=False,
            error=str(e)
        )


@library_tool(
    name="file_exists",
    description="Check if a file exists",
    parameters={
        "path": {"type": "string", "required": True, "description": "Path to check"}
    }
)
def file_exists(path: str) -> LibraryResponse:
    """
    Check if a file exists.

    Args:
        path: Path to check

    Returns:
        LibraryResponse with boolean result
    """
    try:
        if not _validate_path(path):
            return LibraryResponse(
                success=False,
                error=f"Path '{path}' is not in allowed directories"
            )

        exists = os.path.exists(path)
        is_file = os.path.isfile(path) if exists else False

        return LibraryResponse(
            success=True,
            data=exists and is_file,
            metadata={
                "path": path,
                "exists": exists,
                "is_file": is_file,
                "is_dir": os.path.isdir(path) if exists else False
            }
        )

    except Exception as e:
        logger.error(f"Error checking file existence: {e}")
        return LibraryResponse(
            success=False,
            error=str(e)
        )


@library_tool(
    name="delete_file",
    description="Delete a file",
    parameters={
        "path": {"type": "string", "required": True, "description": "Path to the file to delete"}
    }
)
def delete_file(path: str) -> LibraryResponse:
    """
    Delete a file.

    Args:
        path: Path to the file to delete

    Returns:
        LibraryResponse indicating success
    """
    try:
        if not _validate_path(path):
            return LibraryResponse(
                success=False,
                error=f"Path '{path}' is not in allowed directories"
            )

        if not os.path.exists(path):
            return LibraryResponse(
                success=False,
                error=f"File not found: {path}"
            )

        if not os.path.isfile(path):
            return LibraryResponse(
                success=False,
                error=f"Path is not a file: {path}"
            )

        os.remove(path)

        return LibraryResponse(
            success=True,
            data=f"File deleted successfully: {path}",
            metadata={"path": path}
        )

    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        return LibraryResponse(
            success=False,
            error=str(e)
        )


@library_tool(
    name="create_directory",
    description="Create a directory",
    parameters={
        "path": {"type": "string", "required": True, "description": "Directory path to create"},
        "parents": {"type": "boolean", "required": False, "default": True, "description": "Create parent directories if needed"}
    }
)
def create_directory(path: str, parents: bool = True) -> LibraryResponse:
    """
    Create a directory.

    Args:
        path: Directory path to create
        parents: Whether to create parent directories

    Returns:
        LibraryResponse indicating success
    """
    try:
        if not _validate_path(path):
            return LibraryResponse(
                success=False,
                error=f"Path '{path}' is not in allowed directories"
            )

        os.makedirs(path, exist_ok=True) if parents else os.mkdir(path)

        return LibraryResponse(
            success=True,
            data=f"Directory created successfully: {path}",
            metadata={"path": path, "parents": parents}
        )

    except Exception as e:
        logger.error(f"Error creating directory: {e}")
        return LibraryResponse(
            success=False,
            error=str(e)
        )


@library_tool(
    name="read_json",
    description="Read and parse a JSON file",
    parameters={
        "path": {"type": "string", "required": True, "description": "Path to the JSON file"}
    }
)
def read_json(path: str) -> LibraryResponse:
    """
    Read and parse a JSON file.

    Args:
        path: Path to the JSON file

    Returns:
        LibraryResponse with parsed JSON data
    """
    try:
        if not _validate_path(path):
            return LibraryResponse(
                success=False,
                error=f"Path '{path}' is not in allowed directories"
            )

        if not os.path.exists(path):
            return LibraryResponse(
                success=False,
                error=f"File not found: {path}"
            )

        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return LibraryResponse(
            success=True,
            data=data,
            metadata={"path": path}
        )

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        return LibraryResponse(
            success=False,
            error=f"Invalid JSON in file: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error reading JSON file: {e}")
        return LibraryResponse(
            success=False,
            error=str(e)
        )


@library_tool(
    name="write_json",
    description="Write data to a JSON file",
    parameters={
        "path": {"type": "string", "required": True, "description": "Path to the JSON file"},
        "data": {"type": "any", "required": True, "description": "Data to write as JSON"},
        "indent": {"type": "integer", "required": False, "default": 2, "description": "JSON indentation"}
    }
)
def write_json(
    path: str,
    data: Any,
    indent: int = 2
) -> LibraryResponse:
    """
    Write data to a JSON file.

    Args:
        path: Path to the JSON file
        data: Data to write as JSON
        indent: JSON indentation level

    Returns:
        LibraryResponse indicating success
    """
    try:
        if not _validate_path(path):
            return LibraryResponse(
                success=False,
                error=f"Path '{path}' is not in allowed directories"
            )

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)

        return LibraryResponse(
            success=True,
            data=f"JSON written successfully: {path}",
            metadata={"path": path}
        )

    except Exception as e:
        logger.error(f"Error writing JSON file: {e}")
        return LibraryResponse(
            success=False,
            error=str(e)
        )