"""
Workflow Template Registry

Loads, validates, and provides access to workflow templates from JSON and Python files.
Supports auto-matching templates based on user input patterns.
"""

import json
import logging
import re
import sys
import importlib.util
from pathlib import Path
from typing import Dict, Optional, List
from schemas.workflow_schemas import WorkflowTemplate

logger = logging.getLogger(__name__)


class WorkflowRegistry:
    """Registry for workflow templates"""

    def __init__(self, templates_dir: Optional[str] = None):
        """
        Initialize workflow registry.

        Args:
            templates_dir: Directory containing template JSON files
        """
        if templates_dir:
            self.templates_dir = Path(templates_dir)
        else:
            # Default to workflows/templates relative to project root
            self.templates_dir = Path(__file__).parent / "templates"

        self._templates: Dict[str, WorkflowTemplate] = {}
        self._loaded = False

    def load_templates(self) -> int:
        """
        Load all workflow templates from directory (both JSON and Python).

        Returns:
            Number of templates loaded
        """
        if not self.templates_dir.exists():
            logger.warning(f"Templates directory not found: {self.templates_dir}")
            self.templates_dir.mkdir(parents=True, exist_ok=True)
            return 0

        loaded_count = 0

        # Load JSON templates
        for template_file in self.templates_dir.glob("*.json"):
            try:
                with open(template_file, 'r') as f:
                    template_data = json.load(f)

                template = WorkflowTemplate(**template_data)
                self._templates[template.name] = template

                logger.info(
                    f"Loaded JSON workflow template: {template.name} "
                    f"({len(template.nodes)} nodes)"
                )
                loaded_count += 1

            except Exception as e:
                logger.error(f"Error loading JSON template {template_file}: {e}")

        # Load Python templates
        python_count = self.load_python_templates()
        loaded_count += python_count

        self._loaded = True
        logger.info(f"Workflow registry loaded: {loaded_count} templates ({loaded_count - python_count} JSON, {python_count} Python)")

        return loaded_count

    def load_python_templates(self) -> int:
        """
        Load workflow templates from Python files in workflows/python/ directory.

        Python workflow files should:
        - Be in the workflows/python/ directory
        - Export a WorkflowTemplate instance as 'workflow' module variable
        - OR have a create_workflow() function that returns WorkflowTemplate

        Returns:
            Number of Python templates loaded
        """
        loaded_count = 0

        # Get the python subdirectory
        python_dir = Path(__file__).parent / "python"

        if not python_dir.exists():
            logger.debug("No workflows/python/ directory found, skipping Python template loading")
            return 0

        # Scan for Python files (exclude __init__.py and helpers.py)
        for py_file in python_dir.glob("*.py"):
            if py_file.name in ["__init__.py", "helpers.py"]:
                continue

            try:
                # Dynamically import the module
                module_name = f"workflows.python.{py_file.stem}"
                spec = importlib.util.spec_from_file_location(module_name, py_file)

                if spec is None or spec.loader is None:
                    logger.error(f"Could not load module spec for {py_file}")
                    continue

                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)

                # Try to get workflow from module
                workflow = None

                # Option 1: Module-level 'workflow' variable
                if hasattr(module, "workflow"):
                    workflow = module.workflow
                    logger.debug(f"Found 'workflow' variable in {py_file.name}")

                # Option 2: create_workflow() function
                elif hasattr(module, "create_workflow"):
                    workflow = module.create_workflow()
                    logger.debug(f"Called create_workflow() from {py_file.name}")

                else:
                    logger.warning(
                        f"Python workflow file {py_file.name} has no 'workflow' variable "
                        f"or 'create_workflow()' function, skipping"
                    )
                    continue

                # Validate it's a WorkflowTemplate
                if not isinstance(workflow, WorkflowTemplate):
                    logger.error(
                        f"Python workflow file {py_file.name} exported invalid type: "
                        f"{type(workflow)}, expected WorkflowTemplate"
                    )
                    continue

                # Register the template
                self._templates[workflow.name] = workflow

                logger.info(
                    f"Loaded Python workflow template: {workflow.name} "
                    f"({len(workflow.nodes)} nodes) from {py_file.name}"
                )
                loaded_count += 1

            except Exception as e:
                logger.error(
                    f"Error loading Python workflow from {py_file}: {e}",
                    exc_info=True
                )

        return loaded_count

    def get(self, template_name: str) -> Optional[WorkflowTemplate]:
        """
        Get workflow template by name.

        Args:
            template_name: Template name

        Returns:
            WorkflowTemplate or None if not found
        """
        if not self._loaded:
            self.load_templates()

        return self._templates.get(template_name)

    def list_templates(self) -> List[str]:
        """
        List all available template names.

        Returns:
            List of template names
        """
        if not self._loaded:
            self.load_templates()

        return list(self._templates.keys())

    async def match_template(self, user_input: str) -> Optional[WorkflowTemplate]:
        """
        Auto-match workflow template based on user input.

        Uses regex patterns defined in template's trigger_patterns.

        Args:
            user_input: User's input text

        Returns:
            Matched template or None
        """
        if not self._loaded:
            self.load_templates()

        user_input_lower = user_input.lower()

        for template in self._templates.values():
            for pattern in template.trigger_patterns:
                try:
                    if re.search(pattern, user_input_lower):
                        logger.info(
                            f"Auto-matched template '{template.name}' "
                            f"(pattern: '{pattern}')"
                        )
                        return template
                except re.error as e:
                    logger.warning(
                        f"Invalid regex pattern in template '{template.name}': "
                        f"{pattern} - {e}"
                    )

        logger.debug(f"No template matched for input: {user_input[:100]}...")
        return None

    def validate_template(self, template: WorkflowTemplate) -> List[str]:
        """
        Validate workflow template for common issues.

        Args:
            template: Template to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check for duplicate node IDs
        node_ids = [node.id for node in template.nodes]
        if len(node_ids) != len(set(node_ids)):
            errors.append("Duplicate node IDs found")

        # Check dependencies reference existing nodes
        for node in template.nodes:
            for dep in node.depends_on:
                if dep not in node_ids:
                    errors.append(
                        f"Node '{node.id}' depends on non-existent node '{dep}'"
                    )

        # Check conditional edges reference existing nodes
        for edge in template.conditional_edges:
            if edge.from_node not in node_ids:
                errors.append(
                    f"Conditional edge from non-existent node '{edge.from_node}'"
                )

            for condition in edge.conditions:
                if condition.next_node not in node_ids:
                    errors.append(
                        f"Condition routes to non-existent node '{condition.next_node}'"
                    )

            if edge.default not in node_ids:
                errors.append(
                    f"Default edge routes to non-existent node '{edge.default}'"
                )

        # Check for circular dependencies
        if self._has_circular_dependency(template):
            errors.append("Circular dependency detected in workflow")

        # Check MCP tool nodes have tool_name
        for node in template.nodes:
            if node.agent == "mcp_tool" and not node.tool_name:
                errors.append(
                    f"MCP tool node '{node.id}' missing tool_name parameter"
                )

        return errors

    def _has_circular_dependency(self, template: WorkflowTemplate) -> bool:
        """
        Check for circular dependencies in workflow.

        Uses DFS to detect cycles.

        Args:
            template: Template to check

        Returns:
            True if circular dependency found
        """
        # Build adjacency list
        graph = {node.id: node.depends_on for node in template.nodes}

        # Track visited and recursion stack
        visited = set()
        rec_stack = set()

        def dfs(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)

            for neighbor in graph.get(node_id, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True  # Cycle found

            rec_stack.remove(node_id)
            return False

        for node_id in graph:
            if node_id not in visited:
                if dfs(node_id):
                    return True

        return False

    def register_template(
        self,
        template: WorkflowTemplate,
        validate: bool = True
    ) -> bool:
        """
        Programmatically register a workflow template.

        Args:
            template: Template to register
            validate: Whether to validate before registering

        Returns:
            True if successfully registered
        """
        if validate:
            errors = self.validate_template(template)
            if errors:
                logger.error(
                    f"Template validation failed for '{template.name}': {errors}"
                )
                return False

        self._templates[template.name] = template
        logger.info(f"Registered workflow template: {template.name}")
        return True


# Global registry instance
_registry: Optional[WorkflowRegistry] = None


def get_workflow_registry(templates_dir: Optional[str] = None) -> WorkflowRegistry:
    """
    Get global workflow registry instance.

    Args:
        templates_dir: Templates directory (only used on first call)

    Returns:
        WorkflowRegistry instance
    """
    global _registry

    if _registry is None:
        _registry = WorkflowRegistry(templates_dir)

    return _registry
