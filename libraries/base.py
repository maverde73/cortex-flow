"""
Base classes and decorators for the Library system.

Provides the foundation for creating standardized libraries that can be
integrated into workflows.
"""

import inspect
import logging
from typing import Any, Dict, Optional, Callable, List, Union
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
import asyncio

from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)


class LibraryResponse(BaseModel):
    """Standard response format for library functions."""
    success: bool = Field(..., description="Whether the operation succeeded")
    data: Any = Field(None, description="The result data")
    error: Optional[str] = Field(None, description="Error message if failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class LibraryError(Exception):
    """Custom exception for library-related errors."""
    pass


class ParameterType(str, Enum):
    """Supported parameter types for library functions."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DICT = "dict"
    LIST = "list"
    ANY = "any"


class ParameterDefinition(BaseModel):
    """Definition for a function parameter."""
    type: ParameterType = Field(..., description="Parameter type")
    required: bool = Field(True, description="Whether parameter is required")
    default: Any = Field(None, description="Default value if not required")
    description: Optional[str] = Field(None, description="Parameter description")
    validation: Optional[Dict[str, Any]] = Field(None, description="Additional validation rules")


class LibraryMetadata(BaseModel):
    """Metadata for a library module."""
    name: str = Field(..., description="Library name")
    version: str = Field("1.0.0", description="Library version")
    description: str = Field(..., description="Library description")
    author: Optional[str] = Field(None, description="Library author")
    capabilities: List[str] = Field(default_factory=list, description="Required capabilities")
    config: Dict[str, Any] = Field(default_factory=dict, description="Library configuration")


@dataclass
class LibraryFunction:
    """Represents a registered library function."""
    name: str
    func: Callable
    description: str
    parameters: Dict[str, ParameterDefinition]
    is_async: bool
    timeout: Optional[int] = None
    retries: int = 0
    capabilities_required: List[str] = field(default_factory=list)

    def validate_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and coerce parameters according to definitions.

        Args:
            params: Input parameters

        Returns:
            Validated parameters

        Raises:
            ValidationError: If parameters don't match definitions
        """
        validated = {}

        for param_name, param_def in self.parameters.items():
            if param_name in params:
                value = params[param_name]

                # Type coercion
                try:
                    if param_def.type == ParameterType.STRING:
                        validated[param_name] = str(value)
                    elif param_def.type == ParameterType.INTEGER:
                        validated[param_name] = int(value)
                    elif param_def.type == ParameterType.FLOAT:
                        validated[param_name] = float(value)
                    elif param_def.type == ParameterType.BOOLEAN:
                        validated[param_name] = bool(value)
                    elif param_def.type == ParameterType.DICT:
                        if not isinstance(value, dict):
                            raise ValueError(f"{param_name} must be a dict")
                        validated[param_name] = value
                    elif param_def.type == ParameterType.LIST:
                        if not isinstance(value, list):
                            raise ValueError(f"{param_name} must be a list")
                        validated[param_name] = value
                    else:  # ANY
                        validated[param_name] = value

                except (ValueError, TypeError) as e:
                    raise ValidationError(
                        f"Parameter '{param_name}' type error: {str(e)}"
                    )

            elif param_def.required:
                if param_def.default is not None:
                    validated[param_name] = param_def.default
                else:
                    raise ValidationError(
                        f"Required parameter '{param_name}' not provided"
                    )
            elif param_def.default is not None:
                validated[param_name] = param_def.default

        # Check for unexpected parameters
        unexpected = set(params.keys()) - set(self.parameters.keys())
        if unexpected:
            logger.warning(f"Unexpected parameters ignored: {unexpected}")

        return validated

    async def execute(self, params: Dict[str, Any]) -> LibraryResponse:
        """
        Execute the function with validated parameters.

        Args:
            params: Input parameters

        Returns:
            LibraryResponse with execution result
        """
        try:
            # Validate parameters
            validated_params = self.validate_parameters(params)

            # Execute function
            if self.is_async:
                if self.timeout:
                    result = await asyncio.wait_for(
                        self.func(**validated_params),
                        timeout=self.timeout
                    )
                else:
                    result = await self.func(**validated_params)
            else:
                if self.timeout:
                    # Run sync function in executor with timeout
                    loop = asyncio.get_event_loop()
                    result = await asyncio.wait_for(
                        loop.run_in_executor(None, self.func, **validated_params),
                        timeout=self.timeout
                    )
                else:
                    # Run sync function in executor
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(None, self.func, **validated_params)

            # Wrap result if not already a LibraryResponse
            if isinstance(result, LibraryResponse):
                return result
            else:
                return LibraryResponse(
                    success=True,
                    data=result
                )

        except asyncio.TimeoutError:
            return LibraryResponse(
                success=False,
                error=f"Function '{self.name}' timed out after {self.timeout} seconds"
            )
        except ValidationError as e:
            return LibraryResponse(
                success=False,
                error=f"Validation error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error executing library function '{self.name}': {e}")
            return LibraryResponse(
                success=False,
                error=str(e)
            )


# Registry to store decorated functions
_library_registry: Dict[str, Dict[str, LibraryFunction]] = {}


def library_tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    parameters: Optional[Dict[str, Union[Dict, ParameterDefinition]]] = None,
    timeout: Optional[int] = None,
    retries: int = 0,
    capabilities: Optional[List[str]] = None
) -> Callable:
    """
    Decorator to register a function as a library tool.

    Args:
        name: Tool name (defaults to function name)
        description: Tool description (defaults to docstring)
        parameters: Parameter definitions
        timeout: Execution timeout in seconds
        retries: Number of retry attempts on failure
        capabilities: Required capabilities for this function

    Returns:
        Decorated function

    Example:
        @library_tool(
            name="fetch_data",
            description="Fetch data from API",
            parameters={
                "url": {"type": "string", "required": True},
                "method": {"type": "string", "required": False, "default": "GET"}
            },
            timeout=30
        )
        async def fetch_data(url: str, method: str = "GET"):
            # Implementation
            return data
    """
    def decorator(func: Callable) -> Callable:
        # Extract metadata
        func_name = name or func.__name__
        func_description = description or (inspect.getdoc(func) or "No description")
        is_async = inspect.iscoroutinefunction(func)

        # Process parameters
        processed_params = {}
        if parameters:
            for param_name, param_def in parameters.items():
                if isinstance(param_def, dict):
                    # Convert dict to ParameterDefinition
                    param_type = param_def.get("type", "any")
                    if isinstance(param_type, str):
                        param_type = ParameterType(param_type)

                    processed_params[param_name] = ParameterDefinition(
                        type=param_type,
                        required=param_def.get("required", True),
                        default=param_def.get("default"),
                        description=param_def.get("description"),
                        validation=param_def.get("validation")
                    )
                elif isinstance(param_def, ParameterDefinition):
                    processed_params[param_name] = param_def
                else:
                    raise ValueError(f"Invalid parameter definition for '{param_name}'")

        # Create LibraryFunction
        library_func = LibraryFunction(
            name=func_name,
            func=func,
            description=func_description,
            parameters=processed_params,
            is_async=is_async,
            timeout=timeout,
            retries=retries,
            capabilities_required=capabilities or []
        )

        # Register function
        # Extract module name for grouping
        module_name = func.__module__.split('.')[-1] if func.__module__ else "unknown"

        if module_name not in _library_registry:
            _library_registry[module_name] = {}

        _library_registry[module_name][func_name] = library_func

        logger.debug(f"Registered library function: {module_name}.{func_name}")

        # Return original function (unchanged)
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # When called directly, just execute the function
            if is_async:
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)

        # Attach metadata for introspection
        wrapper._library_function = library_func
        wrapper._is_library_tool = True

        return wrapper

    return decorator


def get_registered_libraries() -> Dict[str, Dict[str, LibraryFunction]]:
    """
    Get all registered library functions.

    Returns:
        Dictionary mapping library names to their functions
    """
    return _library_registry.copy()


def get_library_function(library_name: str, function_name: str) -> Optional[LibraryFunction]:
    """
    Get a specific library function.

    Args:
        library_name: Name of the library
        function_name: Name of the function

    Returns:
        LibraryFunction if found, None otherwise
    """
    return _library_registry.get(library_name, {}).get(function_name)


def clear_registry():
    """Clear the library registry (useful for testing)."""
    global _library_registry
    _library_registry = {}