"""
Workflow Executor with Recursive Support

Executes workflows with support for:
- Nested sub-workflows
- Agent nodes (researcher, analyst, writer)
- Variable substitution
- State management
"""

import json
import re
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class RecursionError(Exception):
    """Raised when workflow recursion depth is exceeded."""
    pass


class WorkflowExecutor:
    """Executes workflows with support for nested sub-workflows and agents."""

    def __init__(self, main_workflow: str, llm_client):
        """
        Initialize the workflow executor.

        Args:
            main_workflow: Name of the main workflow to execute
            llm_client: LLM client instance for agent execution
        """
        self.main_workflow = main_workflow
        self.llm = llm_client
        self.workflows_dir = Path("workflows")
        self.workflow_cache = {}
        self.max_recursion_depth = 5

        # Import agents
        try:
            from agents import get_agent
            self.get_agent = get_agent
            logger.info("Agents module loaded successfully")
        except ImportError as e:
            logger.error(f"Failed to import agents: {e}")
            # Fallback to mock agents
            self.get_agent = self._mock_agent

    async def execute(self, params: Dict[str, Any]) -> str:
        """
        Execute the main workflow with given parameters.

        Args:
            params: Input parameters for the workflow

        Returns:
            Final output from the workflow execution
        """
        logger.info(f"Starting execution of workflow '{self.main_workflow}'")
        workflow = self._load_workflow(self.main_workflow)

        try:
            result = await self._execute_workflow(
                workflow=workflow,
                params=params,
                recursion_depth=0,
                parent_stack=[self.main_workflow]
            )
            logger.info(f"Workflow '{self.main_workflow}' completed successfully")
            return result
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            raise

    async def _execute_workflow(self,
                                workflow: Dict,
                                params: Dict[str, Any],
                                recursion_depth: int = 0,
                                parent_stack: List[str] = None) -> str:
        """
        Execute a workflow (main or sub-workflow).

        Args:
            workflow: Workflow definition
            params: Input parameters
            recursion_depth: Current recursion depth
            parent_stack: Stack of parent workflow names (for cycle detection)

        Returns:
            Output from the workflow execution
        """
        if parent_stack is None:
            parent_stack = []

        # Check recursion depth
        if recursion_depth >= self.max_recursion_depth:
            raise RecursionError(
                f"Maximum recursion depth ({self.max_recursion_depth}) exceeded. "
                f"Workflow stack: {' -> '.join(parent_stack)}"
            )

        workflow_name = workflow.get("name", "unknown")
        logger.info(f"{'  ' * recursion_depth}Executing workflow: {workflow_name} (depth: {recursion_depth})")

        # Merge workflow parameters with input parameters
        final_params = {**workflow.get("parameters", {}), **params}

        # Initialize local state for this workflow
        local_state = {}

        # Execute nodes in dependency order
        nodes = workflow.get("nodes", [])
        executed_nodes = set()

        # Simple dependency resolution (not handling parallel groups for now)
        while len(executed_nodes) < len(nodes):
            made_progress = False

            for node in nodes:
                node_id = node.get("id")

                # Skip if already executed
                if node_id in executed_nodes:
                    continue

                # Check dependencies
                dependencies = node.get("depends_on", [])
                if all(dep in executed_nodes for dep in dependencies):
                    # All dependencies met, execute node
                    logger.info(f"{'  ' * recursion_depth}  Executing node: {node_id}")

                    # Prepare instruction with variable substitution
                    instruction = self._substitute_variables(
                        node.get("instruction", ""),
                        {**final_params, **local_state}
                    )

                    # Execute based on agent type
                    output = await self._execute_node(
                        node=node,
                        instruction=instruction,
                        params={**final_params, **local_state},
                        recursion_depth=recursion_depth + 1,
                        parent_stack=parent_stack
                    )

                    # Store output in local state
                    local_state[node_id] = output
                    executed_nodes.add(node_id)
                    made_progress = True

                    logger.debug(f"{'  ' * recursion_depth}  Node '{node_id}' output: {output[:200]}...")

            if not made_progress:
                # Circular dependency or unmet dependencies
                pending = [n["id"] for n in nodes if n["id"] not in executed_nodes]
                raise RuntimeError(f"Cannot resolve dependencies for nodes: {pending}")

        # Return output from the last node
        if nodes:
            last_node_id = nodes[-1]["id"]
            return local_state.get(last_node_id, "")

        return ""

    async def _execute_node(self,
                           node: Dict,
                           instruction: str,
                           params: Dict[str, Any],
                           recursion_depth: int,
                           parent_stack: List[str]) -> str:
        """
        Execute a single workflow node.

        Args:
            node: Node definition
            instruction: Processed instruction with variables substituted
            params: Current state and parameters
            recursion_depth: Current recursion depth
            parent_stack: Stack of parent workflow names

        Returns:
            Output from the node execution
        """
        agent_type = node.get("agent")
        node_id = node.get("id")

        try:
            if agent_type == "workflow":
                # Execute sub-workflow
                sub_workflow_name = node.get("workflow_name")
                if not sub_workflow_name:
                    raise ValueError(f"Node '{node_id}' is type 'workflow' but missing 'workflow_name'")

                # Check for circular dependency
                if sub_workflow_name in parent_stack:
                    raise RecursionError(
                        f"Circular workflow dependency detected: {sub_workflow_name} is already in stack: "
                        f"{' -> '.join(parent_stack)} -> {sub_workflow_name}"
                    )

                # Load sub-workflow
                sub_workflow = self._load_workflow(sub_workflow_name)

                # Prepare parameters for sub-workflow
                sub_params = {}
                for key, value in node.get("workflow_params", {}).items():
                    if isinstance(value, str):
                        sub_params[key] = self._substitute_variables(value, params)
                    else:
                        sub_params[key] = value

                # Execute sub-workflow recursively
                return await self._execute_workflow(
                    workflow=sub_workflow,
                    params=sub_params,
                    recursion_depth=recursion_depth,
                    parent_stack=parent_stack + [sub_workflow_name]
                )

            elif agent_type in ["researcher", "analyst", "writer"]:
                # Execute agent
                agent = self.get_agent(agent_type)
                return await agent.execute(instruction, self.llm)

            elif agent_type == "mcp_tool":
                # MCP tools not supported in standalone mode
                tool_name = node.get("tool_name", "unknown")
                logger.warning(f"MCP tool '{tool_name}' not available in standalone mode")
                return f"[MCP tool '{tool_name}' not available in standalone mode - using mock response]"

            else:
                logger.error(f"Unknown agent type: {agent_type}")
                return f"[Error: Unknown agent type '{agent_type}']"

        except Exception as e:
            logger.error(f"Error executing node '{node_id}': {e}")
            raise

    def _load_workflow(self, workflow_name: str) -> Dict:
        """
        Load a workflow from file (with caching).

        Args:
            workflow_name: Name of the workflow to load

        Returns:
            Workflow definition dictionary
        """
        if workflow_name not in self.workflow_cache:
            workflow_path = self.workflows_dir / f"{workflow_name}.json"

            if not workflow_path.exists():
                raise FileNotFoundError(f"Workflow not found: {workflow_path}")

            with open(workflow_path, 'r') as f:
                self.workflow_cache[workflow_name] = json.load(f)

            logger.debug(f"Loaded workflow '{workflow_name}' from {workflow_path}")

        return self.workflow_cache[workflow_name]

    def _substitute_variables(self, text: str, variables: Dict[str, Any]) -> str:
        """
        Substitute {variable} placeholders with actual values.

        Args:
            text: Text containing {variable} placeholders
            variables: Dictionary of variable values

        Returns:
            Text with variables substituted
        """
        def replace(match):
            key = match.group(1)

            # Handle nested keys (e.g., {node.field})
            if '.' in key:
                parts = key.split('.')
                value = variables
                for part in parts:
                    if isinstance(value, dict):
                        value = value.get(part, match.group(0))
                    else:
                        return match.group(0)
                return str(value)
            else:
                # Simple key
                return str(variables.get(key, match.group(0)))

        # Replace all {variable} patterns
        result = re.sub(r'\{([^}]+)\}', replace, text)
        return result

    def _mock_agent(self, agent_type: str):
        """
        Fallback mock agent for testing.

        Args:
            agent_type: Type of agent

        Returns:
            Mock agent object
        """
        class MockAgent:
            def __init__(self, agent_type):
                self.agent_type = agent_type

            async def execute(self, instruction: str, llm) -> str:
                return f"[Mock {self.agent_type} response for: {instruction[:100]}...]"

        return MockAgent(agent_type)