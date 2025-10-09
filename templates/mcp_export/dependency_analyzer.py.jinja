"""
Dependency Analyzer for Exported Workflow

Minimal implementation for standalone MCP server.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Set

logger = logging.getLogger(__name__)


class DependencyAnalyzer:
    """Simplified dependency analyzer for exported workflows."""

    def __init__(self, project: str = "default"):
        """
        Initialize dependency analyzer.

        Args:
            project: Project name (not used in standalone mode)
        """
        self.workflows_dir = Path("workflows")
        self.analyzed = set()

    def analyze_deep(self, workflow_name: str, depth: int = 0) -> Dict[str, Set[str]]:
        """
        Analyze all dependencies of a workflow recursively.

        Args:
            workflow_name: Name of the workflow to analyze
            depth: Current recursion depth

        Returns:
            Dictionary with sets of agents, workflows, and mcp_tools
        """
        # Check if already analyzed
        if workflow_name in self.analyzed:
            return {"agents": set(), "workflows": set(), "mcp_tools": set()}

        # Check recursion depth
        if depth > 10:
            logger.warning(f"Maximum recursion depth reached for workflow: {workflow_name}")
            return {"agents": set(), "workflows": set(), "mcp_tools": set()}

        self.analyzed.add(workflow_name)

        dependencies = {
            "agents": set(),
            "workflows": {workflow_name},
            "mcp_tools": set()
        }

        # Load workflow
        workflow_path = self.workflows_dir / f"{workflow_name}.json"
        if not workflow_path.exists():
            logger.error(f"Workflow not found: {workflow_path}")
            return dependencies

        try:
            with open(workflow_path, 'r') as f:
                workflow = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in workflow {workflow_name}: {e}")
            return dependencies

        logger.info(f"{'  ' * depth}Analyzing workflow: {workflow_name}")

        # Analyze each node
        for node in workflow.get("nodes", []):
            agent_type = node.get("agent")
            node_id = node.get("id", "unknown")

            if agent_type in ["researcher", "analyst", "writer"]:
                dependencies["agents"].add(agent_type)
                logger.debug(f"{'  ' * depth}  Node '{node_id}': agent={agent_type}")

            elif agent_type == "workflow":
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
                tool_name = node.get("tool_name")
                if tool_name:
                    dependencies["mcp_tools"].add(tool_name)
                    logger.debug(f"{'  ' * depth}  Node '{node_id}': mcp_tool={tool_name}")

        # Reset for reuse
        if depth == 0:
            self.analyzed = set()

        return dependencies