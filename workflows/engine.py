"""
Workflow Execution Engine

Executes workflow templates with support for:
- Parallel node execution
- Conditional routing
- Dependency resolution
- MCP tool integration
- State management

Supports two execution modes:
- "langgraph": Compile to native LangGraph StateGraph (default, recommended)
- "custom": Use custom execution engine (legacy fallback)
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any, Set, Literal
from collections import defaultdict

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from schemas.workflow_schemas import (
    WorkflowTemplate,
    WorkflowNode,
    WorkflowState,
    WorkflowResult,
    NodeExecutionResult,
    WorkflowExecutionLog
)
from workflows.conditions import ConditionEvaluator, extract_sentiment_score
from config_legacy import settings

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """
    Executes workflow templates.

    Supports hybrid execution mode:
    - "langgraph": Compile template to LangGraph StateGraph (default)
    - "custom": Use custom execution engine
    """

    def __init__(self, mode: Literal["langgraph", "custom"] = "langgraph"):
        """
        Initialize WorkflowEngine.

        Args:
            mode: Execution mode
                - "langgraph": Native LangGraph compilation (recommended)
                - "custom": Legacy custom engine
        """
        self.mode = mode
        self.condition_evaluator = ConditionEvaluator()

        # Lazy-load compiler to avoid circular imports
        self._compiler = None

        logger.info(f"WorkflowEngine initialized in '{mode}' mode")

    async def execute_workflow(
        self,
        template: WorkflowTemplate,
        user_input: str,
        params: Optional[Dict[str, Any]] = None
    ) -> WorkflowResult:
        """
        Execute a workflow template.

        Delegates to either LangGraph compilation or custom engine
        based on the mode set in __init__.

        Args:
            template: Workflow template to execute
            user_input: User's input message
            params: Workflow parameters for variable substitution

        Returns:
            WorkflowResult with execution details
        """
        # Route to appropriate execution method
        if self.mode == "langgraph":
            return await self._execute_langgraph(template, user_input, params)
        else:
            return await self._execute_custom(template, user_input, params)

    async def _execute_langgraph(
        self,
        template: WorkflowTemplate,
        user_input: str,
        params: Optional[Dict[str, Any]] = None
    ) -> WorkflowResult:
        """
        Execute workflow using LangGraph compilation.

        Benefits:
        - Native checkpointing support
        - Streaming via .astream()
        - Human-in-the-loop via interrupt()
        - LangSmith tracing
        """
        start_time = time.time()
        params = params or {}

        try:
            # Lazy-load compiler
            if self._compiler is None:
                from workflows.langgraph_compiler import LangGraphWorkflowCompiler
                self._compiler = LangGraphWorkflowCompiler()

            # Compile template to StateGraph
            compiled_graph = self._compiler.compile(template)

            # Prepare initial state
            initial_state = {
                "user_input": user_input,
                "workflow_name": template.name,
                "workflow_params": {**template.parameters, **params},
                "node_outputs": {},
                "completed_nodes": [],
                "workflow_history": [],
                "execution_start_time": start_time,
                "node_retry_counts": {},
                "max_retries": 3
            }

            logger.debug(f"📋 Initial state prepared: {list(initial_state.keys())}")
            logger.debug(f"   user_input: {user_input[:100]}...")
            logger.debug(f"   workflow_params: {initial_state['workflow_params']}")

            # Execute compiled graph
            logger.info(f"🚀 Executing LangGraph workflow '{template.name}'")
            result_state = await compiled_graph.ainvoke(initial_state)
            logger.info(f"🏁 LangGraph execution completed")

            # Extract results
            execution_time = time.time() - start_time

            logger.debug(f"📊 Result state keys: {list(result_state.keys())}")
            logger.debug(f"   completed_nodes: {result_state.get('completed_nodes', [])}")
            logger.debug(f"   node_outputs keys: {list(result_state.get('node_outputs', {}).keys())}")

            # Get final output (last completed node)
            final_output = ""
            if result_state.get("completed_nodes"):
                last_node = result_state["completed_nodes"][-1]
                final_output = result_state["node_outputs"].get(last_node, "")
                logger.debug(f"   final_output from node '{last_node}': {len(final_output)} chars")

            # Build node results from history
            node_results = []
            for log_entry in result_state.get("workflow_history", []):
                if log_entry.action == "executed":
                    node_id = log_entry.node_id
                    node_results.append(NodeExecutionResult(
                        node_id=node_id,
                        agent=log_entry.agent,
                        output=result_state["node_outputs"].get(node_id, ""),
                        execution_time=log_entry.details.get("execution_time", 0),
                        success=True
                    ))

            logger.info(
                f"✅ LangGraph workflow '{template.name}' completed in {execution_time:.2f}s "
                f"({len(node_results)} nodes executed)"
            )

            return WorkflowResult(
                workflow_name=template.name,
                success=not bool(result_state.get("error")),
                final_output=final_output,
                execution_log=result_state.get("workflow_history", []),
                node_results=node_results,
                total_execution_time=execution_time,
                error=result_state.get("error")
            )

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ LangGraph workflow '{template.name}' failed: {e}")

            return WorkflowResult(
                workflow_name=template.name,
                success=False,
                final_output="",
                execution_log=[],
                node_results=[],
                total_execution_time=execution_time,
                error=str(e)
            )

    async def _execute_custom(
        self,
        template: WorkflowTemplate,
        user_input: str,
        params: Optional[Dict[str, Any]] = None
    ) -> WorkflowResult:
        """
        Execute workflow using custom engine (legacy mode).

        This is the original implementation, kept for backward compatibility.
        """
        start_time = time.time()
        params = params or {}

        # Initialize workflow state
        state = WorkflowState(
            workflow_name=template.name,
            workflow_params=params
        )

        # Merge template parameters
        state.workflow_params.update(template.parameters)

        # Build execution DAG
        execution_plan = self._build_execution_plan(template)

        logger.info(
            f"🚀 Starting workflow '{template.name}' "
            f"({len(template.nodes)} nodes)"
        )

        node_results: List[NodeExecutionResult] = []

        try:
            # Execute nodes in topological order
            for step in execution_plan:
                if step["type"] == "parallel":
                    # Execute parallel group
                    results = await self._execute_parallel_nodes(
                        step["nodes"],
                        user_input,
                        state,
                        params
                    )
                    node_results.extend(results)

                    # Update state with results
                    for result in results:
                        state.node_outputs[result.node_id] = result.output
                        state.completed_nodes.append(result.node_id)

                else:
                    # Execute single node
                    node = step["node"]
                    result = await self._execute_node(
                        node,
                        user_input,
                        state,
                        params
                    )
                    node_results.append(result)

                    # Update state
                    state.node_outputs[node.id] = result.output
                    state.completed_nodes.append(node.id)
                    state.current_node = node.id

                    # Extract metadata for conditional routing
                    self._extract_metadata(result.output, state)

                    # Check for conditional routing
                    next_node_id = self._evaluate_conditional_routing(
                        template,
                        node.id,
                        state
                    )

                    if next_node_id and next_node_id != self._get_next_node(execution_plan, node.id):
                        logger.info(
                            f"🔀 Conditional routing: {node.id} → {next_node_id}"
                        )
                        # Adjust execution plan
                        execution_plan = self._reroute_execution(
                            execution_plan,
                            node.id,
                            next_node_id
                        )

            # Get final output (from last completed node)
            final_output = ""
            if state.completed_nodes:
                last_node = state.completed_nodes[-1]
                final_output = state.node_outputs.get(last_node, "")

            execution_time = time.time() - start_time

            logger.info(
                f"✅ Workflow '{template.name}' completed in {execution_time:.2f}s"
            )

            return WorkflowResult(
                workflow_name=template.name,
                success=True,
                final_output=final_output,
                execution_log=state.workflow_history,
                node_results=node_results,
                total_execution_time=execution_time
            )

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ Workflow '{template.name}' failed: {e}")

            return WorkflowResult(
                workflow_name=template.name,
                success=False,
                final_output="",
                execution_log=state.workflow_history,
                node_results=node_results,
                total_execution_time=execution_time,
                error=str(e)
            )

    async def _execute_node(
        self,
        node: WorkflowNode,
        user_input: str,
        state: WorkflowState,
        params: Dict[str, Any]
    ) -> NodeExecutionResult:
        """
        Execute a single workflow node.

        Args:
            node: Node to execute
            user_input: Original user input
            state: Current workflow state
            params: Workflow parameters

        Returns:
            NodeExecutionResult
        """
        start_time = time.time()

        try:
            # Substitute variables in instruction
            instruction = self._substitute_variables(
                node.instruction,
                state,
                params
            )

            logger.info(f"📍 Executing node '{node.id}' (agent: {node.agent})")
            logger.debug(f"   Instruction: {instruction}")

            # Log to workflow history
            state.workflow_history.append(WorkflowExecutionLog(
                timestamp=time.time(),
                node_id=node.id,
                agent=node.agent,
                action="start_execution",
                details={"instruction": instruction}
            ))

            # Execute based on agent type
            if node.agent == "workflow":
                output = await self._execute_workflow(node, state, params)
            elif node.agent == "mcp_tool":
                output = await self._execute_mcp_tool(node, state, params)
            elif node.agent == "library":
                output = await self._execute_library(node, state, params)
            else:
                output = await self._execute_agent(node.agent, instruction, state)

            execution_time = time.time() - start_time

            logger.info(
                f"   ✓ Node '{node.id}' completed in {execution_time:.2f}s"
            )

            return NodeExecutionResult(
                node_id=node.id,
                agent=node.agent,
                output=output,
                execution_time=execution_time,
                success=True
            )

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"   ✗ Node '{node.id}' failed: {e}")

            return NodeExecutionResult(
                node_id=node.id,
                agent=node.agent,
                output="",
                execution_time=execution_time,
                success=False,
                error=str(e)
            )

    async def _execute_parallel_nodes(
        self,
        nodes: List[WorkflowNode],
        user_input: str,
        state: WorkflowState,
        params: Dict[str, Any]
    ) -> List[NodeExecutionResult]:
        """Execute multiple nodes in parallel"""
        logger.info(
            f"⚡ Executing {len(nodes)} nodes in parallel: "
            f"{[n.id for n in nodes]}"
        )

        tasks = [
            self._execute_node(node, user_input, state, params)
            for node in nodes
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle any exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Parallel execution error in node {nodes[i].id}: {result}")
                processed_results.append(NodeExecutionResult(
                    node_id=nodes[i].id,
                    agent=nodes[i].agent,
                    output="",
                    execution_time=0,
                    success=False,
                    error=str(result)
                ))
            else:
                processed_results.append(result)

        return processed_results

    async def _execute_agent(
        self,
        agent_name: str,
        instruction: str,
        state: WorkflowState
    ) -> str:
        """
        Execute an agent (researcher, analyst, writer).

        Args:
            agent_name: Agent to execute
            instruction: Instruction for agent
            state: Workflow state

        Returns:
            Agent output
        """
        # Import agent tools dynamically
        if agent_name == "researcher":
            from tools.proxy_tools import research_web
            result = await research_web.ainvoke({"query": instruction})

        elif agent_name == "analyst":
            from tools.proxy_tools import analyze_data
            result = await analyze_data.ainvoke({"data": instruction})

        elif agent_name == "writer":
            from tools.proxy_tools import write_content
            result = await write_content.ainvoke({"content_request": instruction})

        else:
            raise ValueError(f"Unknown agent: {agent_name}")

        return result

    async def _execute_mcp_tool(
        self,
        node: WorkflowNode,
        state: WorkflowState,
        params: Dict[str, Any]
    ) -> str:
        """
        Execute an MCP tool.

        If node.use_mcp_prompt is True, will attempt to auto-populate
        instruction with MCP prompt guidance from the server.

        Args:
            node: Node with MCP tool configuration
            state: Workflow state
            params: Workflow parameters

        Returns:
            MCP tool output
        """
        if not node.tool_name:
            raise ValueError(f"MCP tool node '{node.id}' missing tool_name")

        from utils.mcp_client import MCPClient
        from utils.mcp_registry import get_mcp_registry

        client = MCPClient()

        # Auto-populate instruction with MCP prompt if requested
        if node.use_mcp_prompt:
            registry = get_mcp_registry()

            # Try to get the tool to find associated prompt
            tool = await registry.get_tool(node.tool_name)
            if tool and tool.associated_prompt:
                prompt = await registry.get_prompt(tool.associated_prompt)
                if prompt and prompt.description:
                    logger.info(f"📋 Auto-populated instruction for '{node.id}' with MCP prompt")
                    # Enhance node instruction with prompt (non-destructive)
                    if node.instruction and not node.instruction.startswith("Execute MCP tool"):
                        # User provided custom instruction, append prompt
                        node.instruction = f"{node.instruction}\n\n## MCP Tool Guidance\n{prompt.description}"
                    else:
                        # Generic instruction, replace with prompt
                        node.instruction = prompt.description

        # Substitute variables in params
        tool_params = {}
        for key, value in node.params.items():
            if isinstance(value, str):
                tool_params[key] = self._substitute_variables(value, state, params)
            elif isinstance(value, dict):
                tool_params[key] = {
                    k: self._substitute_variables(v, state, params) if isinstance(v, str) else v
                    for k, v in value.items()
                }
            else:
                tool_params[key] = value

        logger.info(f"🔧 Calling MCP tool '{node.tool_name}' with params: {tool_params}")

        result = await client.call_tool(
            tool_name=node.tool_name,
            arguments=tool_params
        )

        return str(result)

    async def _execute_workflow(
        self,
        node: WorkflowNode,
        state: WorkflowState,
        params: Dict[str, Any]
    ) -> str:
        """
        Execute a sub-workflow from a workflow node.

        Args:
            node: Workflow node with agent="workflow"
            state: Current workflow state
            params: Workflow parameters

        Returns:
            Output from the sub-workflow execution
        """
        if not node.workflow_name:
            raise ValueError(f"Node {node.id} has agent='workflow' but no workflow_name specified")

        # Check recursion depth
        current_depth = state.recursion_depth
        max_depth = node.max_depth or 5

        if current_depth >= max_depth:
            raise ValueError(
                f"Maximum workflow recursion depth ({max_depth}) exceeded. "
                f"Current depth: {current_depth}, Stack: {state.parent_workflow_stack}"
            )

        # Check for circular dependencies
        if node.workflow_name in state.parent_workflow_stack:
            raise ValueError(
                f"Circular workflow dependency detected: {node.workflow_name} is already in the "
                f"execution stack: {state.parent_workflow_stack}"
            )

        logger.info(
            f"🔄 Executing sub-workflow '{node.workflow_name}' from node '{node.id}' "
            f"(depth: {current_depth + 1}/{max_depth})"
        )

        # Load the sub-workflow template
        from workflows.registry import get_workflow_registry
        registry = get_workflow_registry(settings.workflow_templates_dir)

        sub_template = registry.get(node.workflow_name)
        if not sub_template:
            raise ValueError(f"Workflow template '{node.workflow_name}' not found")

        # Prepare parameters for sub-workflow
        # Merge node params with substituted variables from state
        sub_params = {}

        # First, inherit parent workflow params
        sub_params.update(params)

        # Then add node-specific workflow_params
        for key, value in node.workflow_params.items():
            if isinstance(value, str):
                sub_params[key] = self._substitute_variables(value, state, params)
            else:
                sub_params[key] = value

        # Also make parent node outputs available
        for node_id, output in state.node_outputs.items():
            sub_params[f"{node_id}_output"] = output

        # Use the instruction as user input for the sub-workflow
        sub_user_input = self._substitute_variables(node.instruction, state, params)

        # Create a new engine instance for sub-workflow (preserves mode)
        sub_engine = WorkflowEngine(mode=self.mode)

        # Update recursion tracking in state
        state.recursion_depth = current_depth + 1
        state.parent_workflow_stack.append(state.workflow_name or "root")

        try:
            # Execute the sub-workflow
            result = await sub_engine.execute_workflow(
                template=sub_template,
                user_input=sub_user_input,
                params=sub_params
            )

            # Log sub-workflow completion
            execution_log_entry = WorkflowExecutionLog(
                timestamp=time.time(),
                node_id=node.id,
                agent="workflow",
                action="sub_workflow_completed",
                details={
                    "workflow_name": node.workflow_name,
                    "success": result.success,
                    "execution_time": result.total_execution_time
                }
            )
            state.workflow_history.append(execution_log_entry)

            if result.success:
                logger.info(
                    f"   ✓ Sub-workflow '{node.workflow_name}' completed successfully "
                    f"in {result.total_execution_time:.2f}s"
                )
                return result.final_output
            else:
                logger.error(f"   ✗ Sub-workflow '{node.workflow_name}' failed: {result.error}")
                raise RuntimeError(f"Sub-workflow '{node.workflow_name}' failed: {result.error}")

        finally:
            # Restore recursion tracking
            state.recursion_depth = current_depth
            if state.parent_workflow_stack:
                state.parent_workflow_stack.pop()

    async def _execute_library(
        self,
        node: WorkflowNode,
        state: WorkflowState,
        params: Dict[str, Any]
    ) -> str:
        """
        Execute a library function node.

        Args:
            node: Node with library configuration
            state: Current workflow state
            params: Workflow parameters

        Returns:
            Output from the library function
        """
        from libraries.executor import get_library_executor
        from libraries.registry import LibraryCapabilities

        logger.info(
            f"📚 Executing library function '{node.library_name}.{node.function_name}' "
            f"for node '{node.id}'"
        )

        # Configure capabilities (can be customized based on workflow settings)
        capabilities = LibraryCapabilities(
            filesystem_read=True,
            filesystem_write=True,
            network_access=True
        )

        # Get or create library executor
        executor = get_library_executor(capabilities=capabilities)

        try:
            # Execute library function
            output = await executor.execute_library_node(node, state, params)

            # Log success
            execution_log_entry = WorkflowExecutionLog(
                timestamp=time.time(),
                node_id=node.id,
                agent="library",
                action="library_function_completed",
                details={
                    "library": node.library_name,
                    "function": node.function_name,
                    "success": True
                }
            )
            state.workflow_history.append(execution_log_entry)

            return output

        except Exception as e:
            logger.error(
                f"Library function '{node.library_name}.{node.function_name}' "
                f"failed: {e}"
            )

            # Log failure
            execution_log_entry = WorkflowExecutionLog(
                timestamp=time.time(),
                node_id=node.id,
                agent="library",
                action="library_function_failed",
                details={
                    "library": node.library_name,
                    "function": node.function_name,
                    "error": str(e)
                }
            )
            state.workflow_history.append(execution_log_entry)

            raise

    def _substitute_variables(
        self,
        text: str,
        state: WorkflowState,
        params: Dict[str, Any]
    ) -> str:
        """
        Substitute variables in text.

        Supports:
        - {param_name} - from params
        - {node_id.output} - from previous node outputs
        - {user_input} - original user input
        """
        import re

        def replace_var(match):
            var_name = match.group(1)

            # Check params
            if var_name in params:
                return str(params[var_name])

            # Check workflow params
            if var_name in state.workflow_params:
                return str(state.workflow_params[var_name])

            # Check node outputs (format: node_id or node_id.output)
            if "." in var_name:
                node_id, _ = var_name.split(".", 1)
            else:
                node_id = var_name

            if node_id in state.node_outputs:
                return state.node_outputs[node_id]

            # Return unchanged if not found
            return match.group(0)

        return re.sub(r'\{([^}]+)\}', replace_var, text)

    def _build_execution_plan(self, template: WorkflowTemplate) -> List[Dict]:
        """
        Build execution plan respecting dependencies and parallel groups.

        Returns:
            List of execution steps (sequential or parallel)
        """
        # Group nodes by parallel_group
        parallel_groups = defaultdict(list)
        sequential_nodes = []

        for node in template.nodes:
            if node.parallel_group:
                parallel_groups[node.parallel_group].append(node)
            else:
                sequential_nodes.append(node)

        # Topological sort considering dependencies
        plan = []
        executed = set()

        # Add parallel groups
        for group_name, nodes in parallel_groups.items():
            # Check if all dependencies met
            all_deps_met = all(
                dep in executed or dep in [n.id for n in nodes]
                for node in nodes
                for dep in node.depends_on
            )

            if all_deps_met:
                plan.append({"type": "parallel", "nodes": nodes})
                for node in nodes:
                    executed.add(node.id)

        # Add sequential nodes in dependency order
        remaining = sequential_nodes.copy()
        while remaining:
            added = False
            for node in remaining[:]:
                if all(dep in executed for dep in node.depends_on):
                    plan.append({"type": "sequential", "node": node})
                    executed.add(node.id)
                    remaining.remove(node)
                    added = True

            if not added and remaining:
                # Circular dependency or unmet deps
                raise ValueError(
                    f"Cannot resolve dependencies for nodes: {[n.id for n in remaining]}"
                )

        return plan

    def _extract_metadata(self, output: str, state: WorkflowState):
        """Extract metadata from output for conditional routing"""
        # Extract sentiment score
        state.sentiment_score = extract_sentiment_score(output)

        # Extract content length
        state.content_length = len(output)

    def _evaluate_conditional_routing(
        self,
        template: WorkflowTemplate,
        current_node_id: str,
        state: WorkflowState
    ) -> Optional[str]:
        """Evaluate conditional edges for current node"""
        for edge in template.conditional_edges:
            if edge.from_node == current_node_id:
                return self.condition_evaluator.evaluate_edge(edge, state)
        return None

    def _get_next_node(self, plan: List[Dict], current_node_id: str) -> Optional[str]:
        """Get next node ID from execution plan"""
        for i, step in enumerate(plan):
            if step["type"] == "sequential" and step["node"].id == current_node_id:
                if i + 1 < len(plan):
                    next_step = plan[i + 1]
                    if next_step["type"] == "sequential":
                        return next_step["node"].id
        return None

    def _reroute_execution(
        self,
        plan: List[Dict],
        from_node: str,
        to_node: str
    ) -> List[Dict]:
        """Reroute execution plan based on conditional routing"""
        # Simple implementation: insert target node after current
        new_plan = []
        for step in plan:
            new_plan.append(step)
            if step["type"] == "sequential" and step["node"].id == from_node:
                # Find target node and insert
                for other_step in plan:
                    if (other_step["type"] == "sequential" and
                        other_step["node"].id == to_node):
                        new_plan.append(other_step)
                        break
        return new_plan
