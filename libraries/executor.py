"""
Library Executor Module

Handles the execution of library functions within workflows with:
- Parameter substitution from workflow state
- Timeout management
- Error handling and retries
- Result formatting
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from libraries.base import LibraryResponse, LibraryError, LibraryFunction
from libraries.registry import LibraryRegistry, LibraryCapabilities, get_library_registry
from schemas.workflow_schemas import WorkflowNode, WorkflowState

logger = logging.getLogger(__name__)


class LibraryExecutor:
    """
    Executes library functions within the workflow context.
    """

    def __init__(
        self,
        registry: Optional[LibraryRegistry] = None,
        capabilities: Optional[LibraryCapabilities] = None,
        libraries_dir: Optional[Path] = None
    ):
        """
        Initialize the library executor.

        Args:
            registry: Library registry to use (creates new if not provided)
            capabilities: Capabilities to grant to libraries
            libraries_dir: Directory containing libraries
        """
        if registry:
            self.registry = registry
        else:
            # Create registry with specified capabilities
            self.registry = get_library_registry(
                libraries_dir=libraries_dir,
                capabilities=capabilities or LibraryCapabilities(),
                reset=False
            )

        logger.info("Initialized LibraryExecutor")

    async def execute_library_node(
        self,
        node: WorkflowNode,
        state: WorkflowState,
        params: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Execute a library node within a workflow.

        Args:
            node: Workflow node with library configuration
            state: Current workflow state
            params: Additional workflow parameters

        Returns:
            String output from the library function

        Raises:
            LibraryError: If execution fails
        """
        # Validate node configuration
        if node.agent != "library":
            raise LibraryError(f"Node {node.id} is not a library node")

        if not node.library_name:
            raise LibraryError(f"Node {node.id} missing library_name")

        if not node.function_name:
            raise LibraryError(f"Node {node.id} missing function_name")

        logger.info(
            f"Executing library function: {node.library_name}.{node.function_name} "
            f"for node {node.id}"
        )

        # Get the library function
        lib_func = self.registry.get_library_function(
            node.library_name,
            node.function_name
        )

        if not lib_func:
            raise LibraryError(
                f"Function '{node.function_name}' not found in library '{node.library_name}'"
            )

        # Prepare function parameters with variable substitution
        resolved_params = self._resolve_parameters(
            node.function_params,
            state,
            params
        )

        logger.debug(f"Resolved parameters: {resolved_params}")

        # Execute the function with timeout from node
        try:
            # Override timeout if specified in node
            if node.timeout:
                lib_func.timeout = node.timeout

            result = await lib_func.execute(resolved_params)

            if result.success:
                # Format successful result
                output = self._format_output(result)
                logger.info(f"Library function executed successfully: {node.id}")
                return output
            else:
                # Handle error response
                error_msg = f"Library function failed: {result.error}"
                logger.error(error_msg)
                raise LibraryError(error_msg)

        except asyncio.TimeoutError:
            error_msg = f"Library function timed out after {node.timeout}s"
            logger.error(error_msg)
            raise LibraryError(error_msg)

        except Exception as e:
            error_msg = f"Error executing library function: {str(e)}"
            logger.error(error_msg)
            raise LibraryError(error_msg)

    def _resolve_parameters(
        self,
        function_params: Dict[str, Any],
        state: WorkflowState,
        workflow_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Resolve parameters by substituting variables from workflow state.

        Supports variable substitution patterns:
        - {node_id_output}: Output from a specific node
        - {param_name}: Workflow parameter
        - {state.field}: State field value

        Args:
            function_params: Raw function parameters
            state: Workflow state
            workflow_params: Workflow-level parameters

        Returns:
            Resolved parameters with substitutions applied
        """
        resolved = {}
        workflow_params = workflow_params or {}

        for key, value in function_params.items():
            if isinstance(value, str):
                # Check for variable substitution patterns
                if value.startswith('{') and value.endswith('}'):
                    var_name = value[1:-1]

                    # Check node outputs
                    if var_name.endswith('_output'):
                        node_id = var_name[:-7]  # Remove '_output' suffix
                        if node_id in state.node_outputs:
                            resolved[key] = state.node_outputs[node_id]
                            continue

                    # Check workflow params
                    if var_name in workflow_params:
                        resolved[key] = workflow_params[var_name]
                        continue

                    # Check state fields
                    if var_name.startswith('state.'):
                        field_name = var_name[6:]  # Remove 'state.' prefix
                        if hasattr(state, field_name):
                            resolved[key] = getattr(state, field_name)
                            continue

                    # Check direct workflow params
                    if var_name in state.workflow_params:
                        resolved[key] = state.workflow_params[var_name]
                        continue

                    # If no substitution found, keep original
                    resolved[key] = value
                else:
                    # Not a variable, keep as-is
                    resolved[key] = value

            elif isinstance(value, dict):
                # Recursively resolve nested dictionaries
                resolved[key] = self._resolve_parameters(
                    value,
                    state,
                    workflow_params
                )

            elif isinstance(value, list):
                # Resolve list items
                resolved[key] = [
                    self._resolve_parameters(
                        {'item': item},
                        state,
                        workflow_params
                    ).get('item', item)
                    if isinstance(item, (str, dict))
                    else item
                    for item in value
                ]

            else:
                # Keep other types as-is
                resolved[key] = value

        return resolved

    def _format_output(self, result: LibraryResponse) -> str:
        """
        Format the library function result for workflow output.

        Args:
            result: Library function response

        Returns:
            Formatted string output
        """
        if isinstance(result.data, str):
            return result.data

        if isinstance(result.data, dict):
            # Format dict as key-value pairs
            lines = []
            for key, value in result.data.items():
                lines.append(f"{key}: {value}")
            return "\n".join(lines)

        if isinstance(result.data, list):
            # Format list as numbered items
            lines = []
            for i, item in enumerate(result.data, 1):
                lines.append(f"{i}. {item}")
            return "\n".join(lines)

        # Default: convert to string
        return str(result.data)

    def list_available_functions(self) -> Dict[str, list]:
        """
        List all available library functions.

        Returns:
            Dictionary mapping library names to function names
        """
        return self.registry.list_functions()

    def validate_node(self, node: WorkflowNode) -> bool:
        """
        Validate that a library node has valid configuration.

        Args:
            node: Workflow node to validate

        Returns:
            True if valid, False otherwise
        """
        if node.agent != "library":
            return True  # Not a library node, skip validation

        if not node.library_name or not node.function_name:
            logger.error(
                f"Node {node.id} missing library_name or function_name"
            )
            return False

        # Check if function exists
        lib_func = self.registry.get_library_function(
            node.library_name,
            node.function_name
        )

        if not lib_func:
            logger.error(
                f"Function '{node.function_name}' not found in "
                f"library '{node.library_name}'"
            )
            return False

        # Validate that required parameters are provided
        for param_name, param_def in lib_func.parameters.items():
            if param_def.required:
                if param_name not in node.function_params:
                    if param_def.default is None:
                        logger.error(
                            f"Node {node.id} missing required parameter "
                            f"'{param_name}' for {node.library_name}.{node.function_name}"
                        )
                        return False

        return True


# Global executor instance
_global_executor: Optional[LibraryExecutor] = None


def get_library_executor(
    capabilities: Optional[LibraryCapabilities] = None,
    libraries_dir: Optional[Path] = None,
    reset: bool = False
) -> LibraryExecutor:
    """
    Get or create the global library executor.

    Args:
        capabilities: Capabilities to grant to libraries
        libraries_dir: Directory containing libraries
        reset: Whether to reset the existing executor

    Returns:
        LibraryExecutor instance
    """
    global _global_executor

    if reset or _global_executor is None:
        _global_executor = LibraryExecutor(
            capabilities=capabilities,
            libraries_dir=libraries_dir
        )

    return _global_executor