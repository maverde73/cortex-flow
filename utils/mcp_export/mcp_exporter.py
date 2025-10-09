"""
MCP Workflow Exporter

Exports workflows as standalone MCP servers with all dependencies.
"""

import json
import shutil
import logging
from pathlib import Path
from typing import Dict, Set, Any

from .dependency_analyzer import DependencyAnalyzer

logger = logging.getLogger(__name__)


class MCPWorkflowExporter:
    """Exports workflows as standalone MCP servers."""

    def __init__(self, project: str = "default"):
        """
        Initialize exporter.

        Args:
            project: Project name to export from
        """
        self.project = project
        self.project_path = Path(f"projects/{project}")
        self.workflows_dir = self.project_path / "workflows"
        self.templates_dir = Path("templates/mcp_export")
        self.analyzer = DependencyAnalyzer(project)

    def export_workflow(self, workflow_name: str, output_dir: str,
                       include_docker: bool = True) -> Dict[str, Any]:
        """
        Export a workflow as a standalone MCP server.

        Args:
            workflow_name: Name of the workflow to export
            output_dir: Directory to export to
            include_docker: Whether to include Docker files

        Returns:
            Export result with status and details
        """
        try:
            output_path = Path(output_dir)
            logger.info(f"Exporting workflow '{workflow_name}' to {output_path}")

            # Analyze dependencies
            logger.info("Analyzing workflow dependencies...")
            dependencies = self.analyzer.analyze_deep(workflow_name)

            # Validate dependencies
            issues = self.analyzer.validate_dependencies(dependencies)
            if issues and "missing_workflows" in issues:
                raise ValueError(f"Missing workflow dependencies: {issues['missing_workflows']}")

            # Get workflow info
            workflow_info = self.analyzer.get_workflow_info(workflow_name)

            # Create output directory
            output_path.mkdir(parents=True, exist_ok=True)

            # Create directory structure
            self._create_directory_structure(output_path)

            # Copy all workflow files
            self._copy_workflows(output_path, dependencies["workflows"])

            # Generate Python files from templates
            self._generate_from_templates(
                output_path,
                workflow_name,
                workflow_info,
                dependencies
            )

            # Generate requirements.txt
            self._generate_requirements(output_path)

            # Generate .env.example
            self._generate_env_example(output_path)

            # Generate Docker files if requested
            if include_docker:
                self._generate_docker_files(output_path, workflow_name)

            # Generate README
            self._generate_readme(output_path, workflow_name, workflow_info, dependencies)

            # Generate run script
            self._generate_run_script(output_path, workflow_name)

            logger.info(f"Successfully exported workflow to {output_path}")

            return {
                "success": True,
                "output_dir": str(output_path),
                "workflow": workflow_name,
                "dependencies": {
                    "agents": list(dependencies["agents"]),
                    "workflows": list(dependencies["workflows"]),
                    "mcp_tools": list(dependencies["mcp_tools"])
                },
                "files_created": self._list_created_files(output_path)
            }

        except Exception as e:
            logger.error(f"Export failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "workflow": workflow_name
            }

    def _create_directory_structure(self, output_path: Path):
        """Create the required directory structure."""
        directories = [
            "workflows",
            "agents",
            "logs"
        ]

        for dir_name in directories:
            (output_path / dir_name).mkdir(exist_ok=True)

    def _copy_workflows(self, output_path: Path, workflows: Set[str]):
        """Copy all required workflow files."""
        dest_dir = output_path / "workflows"

        for workflow_name in workflows:
            src_file = self.workflows_dir / f"{workflow_name}.json"
            dest_file = dest_dir / f"{workflow_name}.json"

            if src_file.exists():
                shutil.copy2(src_file, dest_file)
                logger.debug(f"Copied workflow: {workflow_name}")
            else:
                logger.warning(f"Workflow file not found: {src_file}")

    def _generate_from_templates(self, output_path: Path, workflow_name: str,
                                workflow_info: Dict, dependencies: Dict):
        """Generate Python files from templates."""

        template_files = {
            "server.py.jinja": "server.py",
            "workflow_executor.py.jinja": "workflow_executor.py",
            "dependency_analyzer.py.jinja": "dependency_analyzer.py",
            "llm.py.jinja": "llm.py",
            "agents/__init__.py.jinja": "agents/__init__.py",
            "agents/base_agent.py.jinja": "agents/base_agent.py",
            "agents/researcher_lite.py.jinja": "agents/researcher_lite.py",
            "agents/analyst_lite.py.jinja": "agents/analyst_lite.py",
            "agents/writer_lite.py.jinja": "agents/writer_lite.py",
        }

        for template_file, output_file in template_files.items():
            template_path = self.templates_dir / template_file
            output_file_path = output_path / output_file

            # Ensure parent directory exists
            output_file_path.parent.mkdir(parents=True, exist_ok=True)

            if template_path.exists():
                with open(template_path, 'r') as f:
                    content = f.read()

                # Simple template replacement
                # Replace {{ variable }} patterns
                content = content.replace("{{ workflow_name }}", workflow_name)
                content = content.replace("{{ workflow_version }}", workflow_info.get("version", "1.0.0"))
                content = content.replace("{{ workflow_description }}", workflow_info.get("description", ""))

                # Handle workflow parameters in server.py
                if "server.py" in output_file:
                    params_doc = ""
                    for param, default in workflow_info.get("parameters", {}).items():
                        params_doc += f"    - {param}: {default if default else 'Required parameter'}\n"
                    if params_doc:
                        content = content.replace("    {% for param, default in workflow_params.items() %}\n    - {{ param }}: {{ default if default else 'Required parameter' }}\n    {% endfor %}", params_doc.rstrip())
                    else:
                        content = content.replace("    {% for param, default in workflow_params.items() %}\n    - {{ param }}: {{ default if default else 'Required parameter' }}\n    {% endfor %}", "    - No parameters required")

                # Write output
                with open(output_file_path, 'w') as f:
                    f.write(content)

                logger.debug(f"Generated: {output_file}")
            else:
                logger.warning(f"Template not found: {template_path}")

    def _generate_requirements(self, output_path: Path):
        """Generate requirements.txt file."""
        requirements = [
            "fastmcp>=0.1.0",
            "httpx>=0.24.0",
            "python-dotenv>=1.0.0",
            "pydantic>=2.0.0",
            "uvloop>=0.17.0",  # For better async performance
        ]

        req_file = output_path / "requirements.txt"
        with open(req_file, 'w') as f:
            for req in requirements:
                f.write(f"{req}\n")

        logger.debug("Generated requirements.txt")

    def _generate_env_example(self, output_path: Path):
        """Generate .env.example file."""
        env_content = """# LLM Provider Configuration
# Uncomment and set the API keys for your preferred provider

# OpenAI
#OPENAI_API_KEY=your-openai-key-here
#OPENAI_MODEL=gpt-4o-mini

# Anthropic
#ANTHROPIC_API_KEY=your-anthropic-key-here
#ANTHROPIC_MODEL=claude-3-haiku-20240307

# Groq
#GROQ_API_KEY=your-groq-key-here
#GROQ_MODEL=mixtral-8x7b-32768

# OpenRouter
#OPENROUTER_API_KEY=your-openrouter-key-here
#OPENROUTER_MODEL=openai/gpt-3.5-turbo

# Ollama (local)
#OLLAMA_BASE_URL=http://localhost:11434
#OLLAMA_MODEL=llama2

# Server Configuration
MCP_HOST=0.0.0.0  # Host to bind to (0.0.0.0 for all interfaces, needed for Docker)
MCP_PORT=8000  # Port for HTTP transport (change if 8000 is already in use)
LLM_TIMEOUT=300  # Timeout in seconds for LLM calls (default 300 = 5 minutes)
WORKFLOW_TIMEOUT=600  # Overall workflow timeout in seconds (default 600 = 10 minutes)

# Logging
LOG_LEVEL=INFO
"""

        env_file = output_path / ".env.example"
        with open(env_file, 'w') as f:
            f.write(env_content)

        logger.debug("Generated .env.example")

    def _generate_docker_files(self, output_path: Path, workflow_name: str):
        """Generate Docker-related files."""

        # Dockerfile
        dockerfile_content = f"""FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Expose port for HTTP transport
EXPOSE 8000

# Run the MCP server
CMD ["python", "server.py", "--transport", "stdio"]
"""

        dockerfile = output_path / "Dockerfile"
        with open(dockerfile, 'w') as f:
            f.write(dockerfile_content)

        # docker-compose.yml
        compose_content = f"""services:
  mcp-{workflow_name}:
    build: .
    container_name: mcp-{workflow_name}
    environment:
      - LOG_LEVEL=${{LOG_LEVEL:-INFO}}
      - MCP_PORT=${{MCP_PORT:-8000}}
      - OPENAI_API_KEY=${{OPENAI_API_KEY}}
      - ANTHROPIC_API_KEY=${{ANTHROPIC_API_KEY}}
      - GROQ_API_KEY=${{GROQ_API_KEY}}
      - OPENROUTER_API_KEY=${{OPENROUTER_API_KEY}}
    volumes:
      - ./logs:/app/logs
    ports:
      - "${{MCP_PORT:-8000}}:${{MCP_PORT:-8000}}"
    command: ["python", "server.py", "--transport", "streamable-http"]
    restart: unless-stopped
"""

        compose_file = output_path / "docker-compose.yml"
        with open(compose_file, 'w') as f:
            f.write(compose_content)

        logger.debug("Generated Docker files")

    def _generate_readme(self, output_path: Path, workflow_name: str,
                        workflow_info: Dict, dependencies: Dict):
        """Generate README.md file."""

        # Format dependencies for display
        agents_list = "\n".join(f"- {agent}" for agent in dependencies["agents"]) or "- None"
        workflows_list = "\n".join(f"- {wf}" for wf in dependencies["workflows"]) or "- None"
        tools_list = "\n".join(f"- {tool}" for tool in dependencies["mcp_tools"]) or "- None (standalone mode)"

        readme_content = f"""# {workflow_name} MCP Server

{workflow_info.get('description', 'Standalone MCP server for workflow execution.')}

## Overview

This is a standalone MCP (Model Context Protocol) server that executes the `{workflow_name}` workflow.
It includes all necessary dependencies and can run independently.

## Dependencies

### Agents
{agents_list}

### Workflows
{workflows_list}

### MCP Tools
{tools_list}

## Setup

1. **Install Requirements**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure LLM Provider**

   Copy `.env.example` to `.env` and configure your preferred LLM provider:
   ```bash
   cp .env.example .env
   ```

   Then edit `.env` and add your API keys.

## Running the Server

### Standard Mode (stdio)
```bash
python server.py
```

### HTTP Mode
```bash
python server.py --transport streamable-http --port 8000
```

### Using Docker
```bash
# Build the image
docker-compose build

# Run the server
docker-compose up
```

## Available Tools

The server exposes the following MCP tools:

### execute_workflow
Execute the main workflow with parameters.

Parameters:
{json.dumps(workflow_info.get('parameters', {}), indent=2)}

### describe_workflow
Get detailed information about the workflow including dependencies and structure.

### list_available_workflows
List all workflows available in this server.

### get_workflow_parameters
Get the required and optional parameters for the main workflow.

### validate_parameters
Validate parameters before executing the workflow.

## Usage Example

### Via MCP Client
```python
from mcp import Client

client = Client()
await client.connect_stdio(["python", "server.py"])

# Execute the workflow
result = await client.call_tool(
    "execute_workflow",
    {json.dumps(workflow_info.get('parameters', {}), indent=8) if workflow_info.get('parameters') else "{}"}
)
print(result)
```

### Via HTTP API
```bash
# Default port is 8000, change MCP_PORT in .env if needed
curl -X POST http://localhost:8000/mcp/tools/execute_workflow \\
  -H "Content-Type: application/json" \\
  -d '{json.dumps(workflow_info.get('parameters', {})) if workflow_info.get('parameters') else "{}"}'
```

## LLM Provider Support

This server supports multiple LLM providers:
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- Groq (Mixtral, Llama)
- OpenRouter (Multiple models)
- Ollama (Local models)

The provider is auto-detected based on available API keys, or you can specify one explicitly.

## Logging

Logs are written to the `logs/` directory. Set `LOG_LEVEL` in your `.env` file to control verbosity:
- `DEBUG`: Detailed debugging information
- `INFO`: General information (default)
- `WARNING`: Warnings and errors only
- `ERROR`: Errors only

## License

This exported MCP server is part of the Cortex Flow project.
"""

        readme_file = output_path / "README.md"
        with open(readme_file, 'w') as f:
            f.write(readme_content)

        logger.debug("Generated README.md")

    def _generate_run_script(self, output_path: Path, workflow_name: str):
        """Generate a run.sh script for easy execution."""

        script_content = f"""#!/bin/bash

# Run script for {workflow_name} MCP Server

# Colors for output
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
NC='\\033[0m' # No Color

echo -e "${{GREEN}}Starting {workflow_name} MCP Server${{NC}}"

# Check if .env exists
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        echo -e "${{YELLOW}}No .env file found. Copying from .env.example...${{NC}}"
        cp .env.example .env
        echo "Please edit .env and add your API keys"
        exit 1
    fi
fi

# Check if virtual environment exists
if [ ! -d .venv ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install/update requirements
echo "Installing requirements..."
pip install -q -r requirements.txt

# Create logs directory if it doesn't exist
mkdir -p logs

# Parse command line arguments
TRANSPORT="${{1:-stdio}}"

if [ "$TRANSPORT" == "http" ]; then
    # Load port from .env if available
    if [ -f .env ]; then
        export $(grep MCP_PORT .env | xargs) 2>/dev/null || true
    fi
    PORT=${{MCP_PORT:-8000}}
    echo -e "${{GREEN}}Starting HTTP server on port $PORT...${{NC}}"
    python server.py --transport streamable-http
elif [ "$TRANSPORT" == "sse" ]; then
    echo -e "${{GREEN}}Starting SSE server...${{NC}}"
    python server.py --transport sse
else
    echo -e "${{GREEN}}Starting stdio server...${{NC}}"
    python server.py --transport stdio
fi
"""

        script_file = output_path / "run.sh"
        with open(script_file, 'w') as f:
            f.write(script_content)

        # Make executable
        script_file.chmod(0o755)

        logger.debug("Generated run.sh script")

    def _list_created_files(self, output_path: Path) -> list:
        """List all files created in the export."""
        files = []
        for item in output_path.rglob("*"):
            if item.is_file():
                files.append(str(item.relative_to(output_path)))
        return sorted(files)