#!/usr/bin/env python3
"""
Project management CLI for Cortex-Flow.

Commands:
  list        - List all projects
  create      - Create a new project
  activate    - Set active project
  show        - Show project configuration
  validate    - Validate project structure
  copy        - Copy project to new name
"""

import sys
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    load_config,
    ProjectLoader,
    ConfigurationError,
    validate_project_structure,
    get_active_project,
    set_active_project
)


def list_projects():
    """List all available projects."""
    projects = ProjectLoader.list_projects()
    active = get_active_project()

    if not projects:
        print("No projects found in projects/ directory")
        return

    print("Available projects:")
    print()
    for project_name in sorted(projects):
        marker = "* " if project_name == active else "  "
        print(f"{marker}{project_name}")
    print()
    print(f"Active project: {active}")


def create_project(name: str, from_template: Optional[str] = None):
    """
    Create a new project.

    Args:
        name: Project name
        from_template: Copy from existing project (default: copy from 'default')
    """
    projects_dir = Path("projects")
    project_dir = projects_dir / name

    if project_dir.exists():
        print(f"Error: Project '{name}' already exists")
        sys.exit(1)

    # Determine template to copy from
    template_name = from_template or "default"
    template_dir = projects_dir / template_name

    if not template_dir.exists():
        print(f"Error: Template project '{template_name}' not found")
        sys.exit(1)

    # Copy template to new project
    print(f"Creating project '{name}' from template '{template_name}'...")
    shutil.copytree(template_dir, project_dir)

    # Update project.json with new name
    project_json = project_dir / "project.json"
    with open(project_json, 'r') as f:
        config = json.load(f)

    config["name"] = name
    config["description"] = f"Project {name} (created from {template_name})"
    config["created_at"] = datetime.now().isoformat()

    with open(project_json, 'w') as f:
        json.dump(config, f, indent=2)

    print(f"✓ Project '{name}' created successfully")
    print(f"  Location: {project_dir}")
    print()
    print("Next steps:")
    print(f"  1. Edit configuration: {project_dir}/project.json")
    print(f"  2. Configure agents: {project_dir}/agents.json")
    print(f"  3. Activate project: python scripts/project.py activate {name}")


def activate_project(name: str):
    """
    Set the active project.

    Args:
        name: Project name to activate
    """
    projects = ProjectLoader.list_projects()

    if name not in projects:
        print(f"Error: Project '{name}' not found")
        print(f"Available projects: {', '.join(projects)}")
        sys.exit(1)

    # Set in environment (only for current process)
    set_active_project(name)

    # Update .env file
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file, 'r') as f:
            lines = f.readlines()

        # Update ACTIVE_PROJECT line
        found = False
        for i, line in enumerate(lines):
            if line.startswith("ACTIVE_PROJECT="):
                lines[i] = f"ACTIVE_PROJECT={name}\n"
                found = True
                break

        # Add if not found
        if not found:
            lines.append(f"\nACTIVE_PROJECT={name}\n")

        with open(env_file, 'w') as f:
            f.writelines(lines)

        print(f"✓ Activated project: {name}")
        print(f"  Updated .env file")
    else:
        print(f"⚠ Project activated for this session only")
        print(f"  Create .env file to persist: cp .env.example .env")


def show_project(name: Optional[str] = None):
    """
    Show project configuration.

    Args:
        name: Project name (None = show active project)
    """
    project_name = name or get_active_project()

    try:
        loader = ProjectLoader(project_name)
        config = loader.load()
    except ConfigurationError as e:
        print(f"Error loading project '{project_name}': {e}")
        sys.exit(1)

    print(f"Project: {config.name}")
    print(f"Version: {config.project.version}")
    print(f"Description: {config.project.description}")
    print(f"Active: {config.project.active}")
    print()

    print("Agents:")
    for agent_name, agent_config in config.agents.agents.items():
        status = "enabled" if agent_config.enabled else "disabled"
        print(f"  {agent_name}: {status} ({agent_config.host}:{agent_config.port})")
    print()

    print("MCP:")
    print(f"  Enabled: {config.mcp.enabled}")
    if config.mcp.servers:
        print(f"  Servers: {len(config.mcp.servers)}")
        for server_name, server_config in config.mcp.servers.items():
            status = "enabled" if server_config.enabled else "disabled"
            print(f"    {server_name}: {status} ({server_config.transport})")
    print()

    print("Workflows:")
    workflows = loader.list_workflows()
    if workflows:
        for workflow_name in workflows:
            print(f"  {workflow_name}")
    else:
        print("  (none)")


def validate_project_cmd(name: Optional[str] = None):
    """
    Validate project structure.

    Args:
        name: Project name (None = validate active project)
    """
    project_name = name or get_active_project()
    result = validate_project_structure(project_name)

    print(f"Validating project: {project_name}")
    print()

    if result["valid"]:
        print("✓ Project structure is valid")
    else:
        print("✗ Project structure is invalid")

    if result["missing_dirs"]:
        print("\nMissing directories:")
        for dir_path in result["missing_dirs"]:
            print(f"  ✗ {dir_path}")

    if result["missing_files"]:
        print("\nMissing files:")
        for file_name in result["missing_files"]:
            print(f"  ✗ {file_name}")

    if result["warnings"]:
        print("\nWarnings:")
        for warning in result["warnings"]:
            print(f"  ⚠ {warning}")

    sys.exit(0 if result["valid"] else 1)


def copy_project(source: str, dest: str):
    """
    Copy project to new name.

    Args:
        source: Source project name
        dest: Destination project name
    """
    projects = ProjectLoader.list_projects()

    if source not in projects:
        print(f"Error: Source project '{source}' not found")
        sys.exit(1)

    create_project(dest, from_template=source)


def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/project.py <command> [args]")
        print()
        print("Commands:")
        print("  list                    - List all projects")
        print("  create <name>           - Create new project")
        print("  activate <name>         - Set active project")
        print("  show [name]             - Show project configuration")
        print("  validate [name]         - Validate project structure")
        print("  copy <source> <dest>    - Copy project")
        sys.exit(1)

    command = sys.argv[1]

    if command == "list":
        list_projects()

    elif command == "create":
        if len(sys.argv) < 3:
            print("Error: Project name required")
            print("Usage: python scripts/project.py create <name>")
            sys.exit(1)
        create_project(sys.argv[2])

    elif command == "activate":
        if len(sys.argv) < 3:
            print("Error: Project name required")
            print("Usage: python scripts/project.py activate <name>")
            sys.exit(1)
        activate_project(sys.argv[2])

    elif command == "show":
        name = sys.argv[2] if len(sys.argv) > 2 else None
        show_project(name)

    elif command == "validate":
        name = sys.argv[2] if len(sys.argv) > 2 else None
        validate_project_cmd(name)

    elif command == "copy":
        if len(sys.argv) < 4:
            print("Error: Source and destination names required")
            print("Usage: python scripts/project.py copy <source> <dest>")
            sys.exit(1)
        copy_project(sys.argv[2], sys.argv[3])

    else:
        print(f"Error: Unknown command '{command}'")
        sys.exit(1)


if __name__ == "__main__":
    main()
