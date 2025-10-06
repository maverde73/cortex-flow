"""
Configuration loader for JSON-based project configuration.

Loads and validates configuration from projects/{name}/ directory.
Supports environment variable substitution using ${VAR} syntax.
"""

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional, TypeVar, Type

from pydantic import BaseModel, ValidationError

from config.models import (
    ProjectModel,
    AgentsModel,
    MCPModel,
    ReactModel,
    ProjectConfiguration
)
from config.secrets import get_secrets

T = TypeVar('T', bound=BaseModel)


class ConfigurationError(Exception):
    """Raised when configuration loading or validation fails"""
    pass


class ProjectLoader:
    """
    Loads and validates project configuration from JSON files.

    Each project has a directory in projects/ with these files:
    - project.json: Core project settings
    - agents.json: Per-agent configuration
    - mcp.json: MCP server configuration
    - react.json: ReAct pattern configuration
    - workflows/: Workflow templates
    """

    def __init__(self, project_name: str, projects_base_dir: str = "projects"):
        """
        Initialize loader for a specific project.

        Args:
            project_name: Name of the project to load
            projects_base_dir: Base directory for all projects (default: "projects")

        Raises:
            ConfigurationError: If project directory doesn't exist
        """
        self.project_name = project_name
        self.projects_base_dir = Path(projects_base_dir)
        self.project_dir = self.projects_base_dir / project_name

        if not self.project_dir.exists():
            raise ConfigurationError(
                f"Project directory not found: {self.project_dir}\n"
                f"Available projects: {self.list_projects()}"
            )

        # Load secrets for variable substitution
        self.secrets = get_secrets()

    def load(self) -> ProjectConfiguration:
        """
        Load complete project configuration.

        Returns:
            ProjectConfiguration with all loaded and validated config

        Raises:
            ConfigurationError: If any config file is missing or invalid
        """
        try:
            project = self._load_json("project.json", ProjectModel)
            agents = self._load_json("agents.json", AgentsModel)
            mcp = self._load_json("mcp.json", MCPModel)
            react = self._load_json("react.json", ReactModel)

            return ProjectConfiguration(
                project=project,
                agents=agents,
                mcp=mcp,
                react=react
            )
        except ValidationError as e:
            raise ConfigurationError(f"Validation error in project '{self.project_name}': {e}")
        except FileNotFoundError as e:
            raise ConfigurationError(f"Missing configuration file in '{self.project_name}': {e}")
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in project '{self.project_name}': {e}")

    def _load_json(self, filename: str, model_class: Type[T]) -> T:
        """
        Load and validate a JSON configuration file.

        Args:
            filename: Name of the JSON file (relative to project dir)
            model_class: Pydantic model class for validation

        Returns:
            Validated model instance

        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If JSON is invalid
            ValidationError: If validation fails
        """
        file_path = self.project_dir / filename

        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")

        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Substitute environment variables
        content = self._substitute_env_vars(content)

        # Parse JSON
        data = json.loads(content)

        # Validate with Pydantic
        return model_class(**data)

    def _substitute_env_vars(self, content: str) -> str:
        """
        Replace ${VAR} placeholders with environment variable values.

        Supports:
        - ${VAR}: Required variable, raises error if not set
        - ${VAR:-default}: Optional variable with default value

        Args:
            content: JSON content with placeholders

        Returns:
            Content with substituted values

        Raises:
            ConfigurationError: If required variable is not set
        """
        # Pattern: ${VAR} or ${VAR:-default}
        pattern = r'\$\{([A-Z_][A-Z0-9_]*?)(?::-([^}]*))?\}'

        def replacer(match):
            var_name = match.group(1)
            default_value = match.group(2)

            # Try to get from environment
            value = os.getenv(var_name)

            if value is None:
                # Not in environment, try secrets
                if hasattr(self.secrets, var_name.lower()):
                    value = getattr(self.secrets, var_name.lower())

            if value is None:
                if default_value is not None:
                    # Use default value
                    return default_value
                else:
                    # Required variable missing
                    raise ConfigurationError(
                        f"Required environment variable not set: {var_name}\n"
                        f"Set it in .env or use ${{{var_name}:-default}} for optional value"
                    )

            return str(value)

        return re.sub(pattern, replacer, content)

    def list_workflows(self) -> list[str]:
        """
        List all workflow templates in the project.

        Returns:
            List of workflow template names (without .json extension)
        """
        workflows_dir = self.project_dir / "workflows"
        if not workflows_dir.exists():
            return []

        return [
            f.stem for f in workflows_dir.glob("*.json")
            if f.is_file()
        ]

    def load_workflow(self, workflow_name: str) -> Dict[str, Any]:
        """
        Load a specific workflow template.

        Args:
            workflow_name: Name of the workflow (without .json)

        Returns:
            Workflow configuration as dictionary

        Raises:
            FileNotFoundError: If workflow doesn't exist
            json.JSONDecodeError: If JSON is invalid
        """
        workflow_path = self.project_dir / "workflows" / f"{workflow_name}.json"

        if not workflow_path.exists():
            raise FileNotFoundError(
                f"Workflow not found: {workflow_name}\n"
                f"Available workflows: {self.list_workflows()}"
            )

        with open(workflow_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Substitute environment variables
        content = self._substitute_env_vars(content)

        return json.loads(content)

    @classmethod
    def list_projects(cls, projects_base_dir: str = "projects") -> list[str]:
        """
        List all available projects.

        Args:
            projects_base_dir: Base directory for projects

        Returns:
            List of project names
        """
        base_path = Path(projects_base_dir)
        if not base_path.exists():
            return []

        return [
            d.name for d in base_path.iterdir()
            if d.is_dir() and not d.name.startswith('.')
        ]

    @classmethod
    def get_active_project(cls) -> str:
        """
        Get the name of the currently active project.

        Returns:
            Active project name from ACTIVE_PROJECT env var or "default"
        """
        return get_secrets().active_project


# Global configuration instance
_config: Optional[ProjectConfiguration] = None


def load_config(project_name: Optional[str] = None, force_reload: bool = False) -> ProjectConfiguration:
    """
    Load project configuration (singleton pattern).

    Args:
        project_name: Project to load (None = use ACTIVE_PROJECT from env)
        force_reload: Force reload even if already loaded

    Returns:
        ProjectConfiguration instance

    Raises:
        ConfigurationError: If loading or validation fails
    """
    global _config

    if _config is not None and not force_reload:
        return _config

    # Determine project name
    if project_name is None:
        project_name = ProjectLoader.get_active_project()

    # Load configuration
    loader = ProjectLoader(project_name)
    _config = loader.load()

    return _config


def reload_config(project_name: Optional[str] = None) -> ProjectConfiguration:
    """
    Force reload configuration.

    Args:
        project_name: Project to load (None = use ACTIVE_PROJECT)

    Returns:
        Newly loaded ProjectConfiguration
    """
    return load_config(project_name=project_name, force_reload=True)


def get_config() -> ProjectConfiguration:
    """
    Get current configuration (must be loaded first).

    Returns:
        Current ProjectConfiguration

    Raises:
        RuntimeError: If configuration not loaded yet
    """
    if _config is None:
        raise RuntimeError(
            "Configuration not loaded. Call load_config() first."
        )
    return _config


def validate_project_structure(project_name: str) -> Dict[str, Any]:
    """
    Validate that a project has all required files and structure.

    Args:
        project_name: Name of project to validate

    Returns:
        Dictionary with validation results:
        {
            "valid": bool,
            "missing_files": list[str],
            "missing_dirs": list[str],
            "warnings": list[str]
        }
    """
    project_dir = Path("projects") / project_name

    result = {
        "valid": True,
        "missing_files": [],
        "missing_dirs": [],
        "warnings": []
    }

    # Check directory exists
    if not project_dir.exists():
        result["valid"] = False
        result["missing_dirs"].append(str(project_dir))
        return result

    # Check required files
    required_files = ["project.json", "agents.json", "mcp.json", "react.json"]
    for filename in required_files:
        file_path = project_dir / filename
        if not file_path.exists():
            result["valid"] = False
            result["missing_files"].append(filename)

    # Check workflows directory
    workflows_dir = project_dir / "workflows"
    if not workflows_dir.exists():
        result["warnings"].append("No workflows/ directory found")
    elif not list(workflows_dir.glob("*.json")):
        result["warnings"].append("workflows/ directory is empty")

    return result
