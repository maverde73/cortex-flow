#!/usr/bin/env python3
"""
MCP Server for simple_research Workflow

Auto-generated standalone MCP server that executes the simple_research workflow.
This server includes all necessary dependencies and can run independently.
"""

from mcp.server.fastmcp import FastMCP
import json
import os
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
WORKFLOW_NAME = "simple_research"
WORKFLOW_VERSION = "1.0"
WORKFLOW_DESCRIPTION = """Simple reusable research workflow - building block for larger workflows"""

# Load main workflow
workflow_path = Path("workflows") / f"{WORKFLOW_NAME}.json"
if not workflow_path.exists():
    logger.error(f"Workflow file not found: {workflow_path}")
    sys.exit(1)

with open(workflow_path, 'r') as f:
    workflow = json.load(f)

# Initialize LLM client
try:
    from llm import create_llm_client
    llm_client = create_llm_client()
    logger.info("LLM client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize LLM client: {e}")
    sys.exit(1)

# Initialize workflow executor
from workflow_executor import WorkflowExecutor
executor = WorkflowExecutor(WORKFLOW_NAME, llm_client)

# Create MCP server
mcp = FastMCP(
    name=f"workflow-{workflow['name']}",
    instructions=WORKFLOW_DESCRIPTION or workflow.get('description', ''),
    version=WORKFLOW_VERSION
)

@mcp.tool()
async def execute_workflow(**params) -> str:
    """
    Execute the simple_research workflow with the given parameters.

    Parameters:
    - query: latest technology trends

    Returns:
        The workflow execution result as a string.
    """
    try:
        logger.info(f"Executing workflow '{WORKFLOW_NAME}' with params: {params}")
        result = await executor.execute(params)
        logger.info(f"Workflow execution completed successfully")
        return result
    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        return f"Error executing workflow: {str(e)}"

@mcp.tool()
def describe_workflow() -> dict:
    """
    Get detailed information about the workflow.

    Returns:
        Dictionary containing workflow metadata, parameters, and dependencies.
    """
    try:
        from dependency_analyzer import DependencyAnalyzer
        analyzer = DependencyAnalyzer()

        # Get dependencies
        deps = analyzer.analyze_deep(WORKFLOW_NAME)

        return {
            "name": workflow["name"],
            "version": workflow.get("version", "1.0"),
            "description": workflow.get("description", ""),
            "parameters": workflow.get("parameters", {}),
            "dependencies": {
                "agents": list(deps["agents"]),
                "workflows": list(deps["workflows"]),
                "mcp_tools": list(deps["mcp_tools"])
            },
            "nodes": len(workflow.get("nodes", [])),
            "has_conditions": len(workflow.get("conditional_edges", [])) > 0
        }
    except Exception as e:
        logger.error(f"Failed to describe workflow: {e}")
        return {
            "error": str(e),
            "name": workflow.get("name", WORKFLOW_NAME),
            "description": workflow.get("description", "")
        }

@mcp.tool()
def list_available_workflows() -> list:
    """
    List all available workflows in this MCP server.

    Returns:
        List of workflow names that can be executed.
    """
    workflows_dir = Path("workflows")
    available = []

    for workflow_file in workflows_dir.glob("*.json"):
        try:
            with open(workflow_file, 'r') as f:
                wf = json.load(f)
                available.append({
                    "name": wf.get("name", workflow_file.stem),
                    "description": wf.get("description", ""),
                    "is_main": wf.get("name") == WORKFLOW_NAME
                })
        except Exception as e:
            logger.warning(f"Failed to load workflow {workflow_file}: {e}")

    return available

@mcp.tool()
def get_workflow_parameters() -> dict:
    """
    Get the required and optional parameters for the main workflow.

    Returns:
        Dictionary of parameter names and their default values (if any).
    """
    return workflow.get("parameters", {})

@mcp.tool()
async def validate_parameters(**params) -> dict:
    """
    Validate parameters before executing the workflow.

    Returns:
        Dictionary with validation results and any missing required parameters.
    """
    workflow_params = workflow.get("parameters", {})

    validation = {
        "valid": True,
        "missing": [],
        "warnings": [],
        "provided": list(params.keys())
    }

    # Check for required parameters (those without default values)
    for param, default_value in workflow_params.items():
        if default_value is None or default_value == "":
            if param not in params:
                validation["missing"].append(param)
                validation["valid"] = False

    # Warn about extra parameters
    for param in params:
        if param not in workflow_params:
            validation["warnings"].append(f"Unknown parameter: {param}")

    return validation

if __name__ == "__main__":
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description=f"MCP Server for {WORKFLOW_NAME} workflow")
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http"],
        default="stdio",
        help="Transport method for MCP server"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for HTTP transport (default: 8000)"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host for HTTP transport (default: 0.0.0.0)"
    )

    args = parser.parse_args()

    logger.info(f"Starting MCP server for workflow '{WORKFLOW_NAME}'")
    logger.info(f"Transport: {args.transport}")

    if args.transport == "streamable-http":
        logger.info(f"HTTP endpoint: http://{args.host}:{args.port}/mcp")

    # Run the server
    mcp.run(
        transport=args.transport,
        host=args.host if args.transport == "streamable-http" else None,
        port=args.port if args.transport == "streamable-http" else None
    )