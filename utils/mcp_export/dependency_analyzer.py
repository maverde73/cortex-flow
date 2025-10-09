"""
Dependency Analyzer for Workflow Export

Analyzes workflow dependencies recursively to identify all required components
for standalone MCP server export.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Set, Optional

logger = logging.getLogger(__name__)


class DependencyAnalyzer:
    """Analyzes workflow dependencies recursively."""

    def __init__(self, project: str = "default"):
        """
        Initialize dependency analyzer.

        Args:
            project: Project name to analyze workflows from
        """
        self.project = project
        self.project_path = Path(f"projects/{project}")
        self.workflows_dir = self.project_path / "workflows"
        self.analyzed = set()  # Prevent infinite recursion

    def analyze_deep(self, workflow_name: str, depth: int = 0) -> Dict[str, Set[str]]:
        """
        Analyze all dependencies of a workflow recursively.

        Args:
            workflow_name: Name of the workflow to analyze
            depth: Current recursion depth (for limiting)

        Returns:
            Dictionary with sets of agents, workflows, and mcp_tools
        """
        # Check if already analyzed to prevent cycles
        if workflow_name in self.analyzed:
            return {"agents": set(), "workflows": set(), "mcp_tools": set()}

        # Check recursion depth limit
        if depth > 10:
            logger.warning(f"Maximum recursion depth reached for workflow: {workflow_name}")
            return {"agents": set(), "workflows": set(), "mcp_tools": set()}

        self.analyzed.add(workflow_name)

        dependencies = {
            "agents": set(),
            "workflows": {workflow_name},  # Include the workflow itself
            "mcp_tools": set()
        }

        # Load workflow
        workflow_path = self.workflows_dir / f"{workflow_name}.json"
        if not workflow_path.exists():
            logger.error(f"Workflow not found: {workflow_path}")
            raise FileNotFoundError(f"Workflow '{workflow_name}' not found in project '{self.project}'")

        try:
            with open(workflow_path, 'r') as f:
                workflow = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in workflow {workflow_name}: {e}")
            raise

        logger.info(f"{'  ' * depth}Analyzing workflow: {workflow_name}")

        # Analyze each node
        for node in workflow.get("nodes", []):
            agent_type = node.get("agent")
            node_id = node.get("id", "unknown")

            if agent_type in ["researcher", "analyst", "writer"]:
                # Standard agent
                dependencies["agents"].add(agent_type)
                logger.debug(f"{'  ' * depth}  Node '{node_id}': agent={agent_type}")

            elif agent_type == "workflow":
                # Sub-workflow - recursive analysis
                sub_workflow = node.get("workflow_name")
                if sub_workflow:
                    logger.info(f"{'  ' * depth}  Node '{node_id}': sub-workflow={sub_workflow}")

                    # Recursive call
                    sub_deps = self.analyze_deep(sub_workflow, depth + 1)

                    # Merge dependencies
                    dependencies["agents"].update(sub_deps["agents"])
                    dependencies["workflows"].update(sub_deps["workflows"])
                    dependencies["mcp_tools"].update(sub_deps["mcp_tools"])

            elif agent_type == "mcp_tool":
                # MCP tool
                tool_name = node.get("tool_name")
                if tool_name:
                    dependencies["mcp_tools"].add(tool_name)
                    logger.debug(f"{'  ' * depth}  Node '{node_id}': mcp_tool={tool_name}")

            else:
                logger.warning(f"{'  ' * depth}  Node '{node_id}': unknown agent type '{agent_type}'")

        # Reset analyzed set for this branch (allows reuse in other branches)
        if depth == 0:
            self.analyzed = set()

        return dependencies

    def get_workflow_info(self, workflow_name: str) -> Dict[str, any]:
        """
        Get basic information about a workflow.

        Args:
            workflow_name: Name of the workflow

        Returns:
            Dictionary with workflow metadata
        """
        workflow_path = self.workflows_dir / f"{workflow_name}.json"

        if not workflow_path.exists():
            raise FileNotFoundError(f"Workflow '{workflow_name}' not found")

        with open(workflow_path, 'r') as f:
            workflow = json.load(f)

        return {
            "name": workflow.get("name"),
            "version": workflow.get("version", "1.0"),
            "description": workflow.get("description", ""),
            "parameters": workflow.get("parameters", {}),
            "node_count": len(workflow.get("nodes", []))
        }

    def validate_dependencies(self, dependencies: Dict[str, Set[str]]) -> Dict[str, list]:
        """
        Validate that all dependencies exist and are accessible.

        Args:
            dependencies: Dependencies dictionary from analyze_deep

        Returns:
            Dictionary of validation issues (empty if all valid)
        """
        issues = {
            "missing_workflows": [],
            "missing_agents": [],
            "unsupported_tools": []
        }

        # Check workflows exist
        for workflow in dependencies["workflows"]:
            workflow_path = self.workflows_dir / f"{workflow}.json"
            if not workflow_path.exists():
                issues["missing_workflows"].append(workflow)

        # Check agent support (we support these)
        supported_agents = {"researcher", "analyst", "writer"}
        for agent in dependencies["agents"]:
            if agent not in supported_agents:
                issues["missing_agents"].append(agent)

        # MCP tools will be mocked in standalone mode
        if dependencies["mcp_tools"]:
            logger.info(f"Note: {len(dependencies['mcp_tools'])} MCP tools will be mocked in standalone mode")
            issues["unsupported_tools"] = list(dependencies["mcp_tools"])

        return {k: v for k, v in issues.items() if v}