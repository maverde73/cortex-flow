"""
LangGraph Workflow Compiler

Compiles WorkflowTemplate (from DSL or JSON) into native LangGraph StateGraph.

This enables:
- Native LangGraph checkpointing (PostgreSQL/Redis)
- Streaming responses via .astream()
- Human-in-the-loop via interrupt()
- LangSmith tracing
- Unified execution with agent graphs

Architecture:
    WorkflowTemplate (Pydantic) → StateGraph (LangGraph) → CompiledGraph
"""

import logging
import time
from typing import Dict, Any, List, Callable, Literal, Optional
from collections import defaultdict

from langgraph.graph import StateGraph, END
from langgraph.constants import Send
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from schemas.workflow_schemas import (
    WorkflowTemplate,
    WorkflowNode,
    WorkflowCondition,
    ConditionalEdge,
    WorkflowState,
    NodeExecutionResult,
    WorkflowExecutionLog
)
from workflows.conditions import ConditionEvaluator
from config_legacy import settings

logger = logging.getLogger(__name__)


class WorkflowStateGraph(WorkflowState):
    """
    Extended WorkflowState for LangGraph compatibility.

    Adds LangGraph-specific fields while maintaining backward compatibility.
    """
    # User input (for node execution)
    user_input: Optional[str] = None

    # Execution metadata
    execution_start_time: Optional[float] = None
    error: Optional[str] = None

    # Retry tracking (per-node)
    node_retry_counts: Optional[Dict[str, int]] = None
    max_retries: int = 3  # Maximum retry attempts per node

    class Config:
        arbitrary_types_allowed = True


class LangGraphWorkflowCompiler:
    """
    Compiles WorkflowTemplate into LangGraph StateGraph.

    Features:
    - Parallel execution via Send() API
    - Conditional routing via add_conditional_edges()
    - Dependency resolution via add_edge()
    - Node function generation
    - State management

    Example:
        compiler = LangGraphWorkflowCompiler()
        compiled_graph = compiler.compile(template)
        result = await compiled_graph.ainvoke({"user_input": "..."})
    """

    def __init__(self):
        self.condition_evaluator = ConditionEvaluator()
        self._agent_executors = {}  # Cache for agent executors

    def compile(self, template: WorkflowTemplate) -> Any:
        """
        Compile WorkflowTemplate to LangGraph StateGraph.

        Args:
            template: Workflow template to compile

        Returns:
            CompiledGraph ready for execution
        """
        logger.info(
            f"🔨 Compiling workflow '{template.name}' to LangGraph "
            f"({len(template.nodes)} nodes)"
        )
        logger.info(f"📋 Node list: {[n.id for n in template.nodes]}")

        # Create StateGraph
        graph = StateGraph(WorkflowStateGraph)

        # Analyze workflow structure
        parallel_groups = self._identify_parallel_groups(template)
        logger.info(f"🔗 Parallel groups identified: {parallel_groups}")

        entry_nodes = self._identify_entry_nodes(template)
        logger.info(f"🚪 Entry nodes identified: {entry_nodes}")

        # Add nodes
        logger.info("➕ Adding nodes to graph...")
        for node in template.nodes:
            node_function = self._create_node_function(node, template)
            graph.add_node(node.id, node_function)
            logger.debug(f"   ✓ Added node '{node.id}' (agent: {node.agent})")

        # Add entry point
        if len(entry_nodes) == 1:
            # Single entry node
            logger.info(f"🎯 Setting single entry point: {entry_nodes[0]}")
            graph.set_entry_point(entry_nodes[0])
        else:
            # Multiple entry nodes - create router
            logger.info(f"🎯 Creating entry router for {len(entry_nodes)} entry nodes")
            graph.add_node("__entry_router__", self._create_entry_router(entry_nodes))
            graph.set_entry_point("__entry_router__")

            for entry_node in entry_nodes:
                logger.debug(f"   ✓ Router → {entry_node}")
                graph.add_edge("__entry_router__", entry_node)

        # Add edges (dependencies and flow)
        logger.info("🔗 Adding edges (dependencies)...")
        self._add_edges(graph, template, parallel_groups)

        # Add conditional edges
        logger.info("🔀 Adding conditional edges...")
        self._add_conditional_edges(graph, template)

        # Compile
        logger.info("⚙️ Compiling graph...")
        compiled = graph.compile()

        logger.info(f"✅ Workflow '{template.name}' compiled successfully")

        return compiled

    def _identify_parallel_groups(self, template: WorkflowTemplate) -> Dict[str, List[str]]:
        """
        Identify parallel execution groups.

        Returns:
            Dict mapping group_name -> [node_ids]
        """
        groups = defaultdict(list)

        for node in template.nodes:
            if node.parallel_group:
                groups[node.parallel_group].append(node.id)

        return dict(groups)

    def _identify_entry_nodes(self, template: WorkflowTemplate) -> List[str]:
        """
        Identify entry nodes (nodes with no dependencies).

        Entry nodes are nodes that DON'T DEPEND ON any other node (i.e., depends_on is empty).
        This is different from terminal nodes (nodes that no one depends on).

        Returns:
            List of node IDs that can be entry points
        """
        logger.debug("🔍 Analyzing node dependencies to find entry nodes...")

        entry_nodes = []
        for node in template.nodes:
            if not node.depends_on or len(node.depends_on) == 0:
                logger.debug(f"   ✓ Node '{node.id}' has NO dependencies → ENTRY NODE")
                entry_nodes.append(node.id)
            else:
                logger.debug(f"   Node '{node.id}' depends on: {node.depends_on}")

        if not entry_nodes:
            logger.warning(f"⚠️ No entry nodes found! Using fallback: {template.nodes[0].id}")
            return [template.nodes[0].id]

        logger.debug(f"✅ Found {len(entry_nodes)} entry node(s): {entry_nodes}")
        return entry_nodes

    def _create_node_function(
        self,
        node: WorkflowNode,
        template: WorkflowTemplate
    ) -> Callable:
        """
        Create a node function for LangGraph.

        Args:
            node: WorkflowNode to convert
            template: Parent template (for context)

        Returns:
            Async function compatible with LangGraph
        """
        async def node_function(state: WorkflowStateGraph) -> Dict[str, Any]:
            """Generated node function for LangGraph execution."""
            from utils.workflow_logger import log_node_start, log_node_complete, log_node_error

            start_time = time.time()

            try:
                # Track retry count for this node
                retry_counts = getattr(state, "node_retry_counts", {}) or {}
                current_retry = retry_counts.get(node.id, 0)
                max_retries = getattr(state, "max_retries", 3)

                logger.info(f"📍 Executing node '{node.id}' (agent: {node.agent}, retry: {current_retry}/{max_retries})")

                # Check if we've exceeded max retries
                if current_retry >= max_retries:
                    logger.error(f"❌ Node '{node.id}' exceeded max retries ({max_retries})")
                    return {
                        "error": f"Node {node.id} exceeded maximum retry attempts ({max_retries})",
                        "workflow_history": list(getattr(state, "workflow_history", []) or [])
                    }

                # Substitute variables in instruction
                instruction = self._substitute_variables(
                    node.instruction,
                    state
                )

                # Log to file
                log_node_start(node.id, node.agent, current_retry, max_retries, instruction)

                logger.debug(f"   Instruction (first 150 chars): {instruction[:150]}...")
                completed = getattr(state, "completed_nodes", []) or []
                logger.debug(f"   Nodes completed so far: {completed}")

                # Execute agent
                output = await self._execute_agent(
                    agent_type=node.agent,
                    instruction=instruction,
                    node=node,
                    state=state
                )

                execution_time = time.time() - start_time

                # Log to file
                log_node_complete(node.id, execution_time, output)

                logger.info(f"✅ Node '{node.id}' completed in {execution_time:.2f}s (output: {len(output)} chars)")
                logger.debug(f"   Output preview: {output[:200]}...")

                # Create execution result
                result = NodeExecutionResult(
                    node_id=node.id,
                    agent=node.agent,
                    output=output,
                    execution_time=execution_time,
                    success=True
                )

                # Log execution
                log_entry = WorkflowExecutionLog(
                    timestamp=time.time(),
                    node_id=node.id,
                    agent=node.agent,
                    action="executed",
                    details={
                        "instruction": instruction[:200],
                        "output_length": len(output),
                        "execution_time": execution_time
                    }
                )

                # Update state
                new_outputs = dict(getattr(state, "node_outputs", {}) or {})
                new_outputs[node.id] = output

                new_completed = list(getattr(state, "completed_nodes", []) or [])
                new_completed.append(node.id)

                new_history = list(getattr(state, "workflow_history", []) or [])
                new_history.append(log_entry)

                # Increment retry counter for this node
                new_retry_counts = dict(getattr(state, "node_retry_counts", {}) or {})
                new_retry_counts[node.id] = new_retry_counts.get(node.id, 0) + 1

                # Extract metadata for conditional routing
                metadata_updates = self._extract_metadata(output, node.id)

                logger.debug(f"   State update: completed_nodes={new_completed}, retry_count={new_retry_counts.get(node.id)}, metadata={list(metadata_updates.keys())}")

                return {
                    "node_outputs": new_outputs,
                    "completed_nodes": new_completed,
                    "current_node": node.id,
                    "workflow_history": new_history,
                    "node_retry_counts": new_retry_counts,
                    **metadata_updates
                }

            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"❌ Node '{node.id}' failed: {e}")

                # Log error
                log_entry = WorkflowExecutionLog(
                    timestamp=time.time(),
                    node_id=node.id,
                    agent=node.agent,
                    action="error",
                    details={"error": str(e), "execution_time": execution_time}
                )

                new_history = list(getattr(state, "workflow_history", []) or [])
                new_history.append(log_entry)

                return {
                    "workflow_history": new_history,
                    "error": f"Node {node.id} failed: {str(e)}"
                }

        return node_function

    def _create_entry_router(self, entry_nodes: List[str]) -> Callable:
        """
        Create entry router for multiple entry points.

        Uses Send() API to fan-out to multiple parallel entry nodes.
        """
        async def entry_router(state: WorkflowStateGraph) -> List[Send]:
            """Route to all entry nodes in parallel."""
            logger.info(f"🔀 Routing to {len(entry_nodes)} entry nodes")

            # Initialize state if needed
            if not getattr(state, "execution_start_time", None):
                state["execution_start_time"] = time.time()

            # Send to all entry nodes
            return [Send(node_id, state) for node_id in entry_nodes]

        return entry_router

    def _add_edges(
        self,
        graph: StateGraph,
        template: WorkflowTemplate,
        parallel_groups: Dict[str, List[str]]
    ):
        """
        Add edges (dependencies) to graph.

        Handles:
        - Sequential dependencies (add_edge)
        - Parallel groups (Send API via router)
        - Terminal nodes (END)
        - Skips nodes with conditional edges (handled separately)
        """
        # Identify nodes with conditional edges (these should NOT get normal edges)
        conditional_source_nodes = {ce.from_node for ce in template.conditional_edges}
        logger.debug(f"   Nodes with conditional edges (will skip normal edges): {conditional_source_nodes}")

        # Build dependency map
        dependency_map = {}
        for node in template.nodes:
            if node.depends_on:
                for dep in node.depends_on:
                    if dep not in dependency_map:
                        dependency_map[dep] = []
                    dependency_map[dep].append(node.id)

        logger.debug(f"   Dependency map: {dependency_map}")

        # Add edges for dependencies (skip conditional sources)
        for from_node, to_nodes in dependency_map.items():
            # Skip if this node has a conditional edge - will be handled by _add_conditional_edges
            if from_node in conditional_source_nodes:
                logger.info(f"   ⏭️ Skipping edge from '{from_node}' (has conditional edge)")
                continue

            if len(to_nodes) == 1:
                # Single dependency - simple edge
                logger.info(f"   ✓ Edge: {from_node} → {to_nodes[0]}")
                graph.add_edge(from_node, to_nodes[0])
            else:
                # Multiple dependencies - create router for parallel execution
                router_name = f"__router_{from_node}__"
                logger.info(f"   ✓ Parallel edge: {from_node} → {router_name} → {to_nodes}")
                graph.add_node(router_name, self._create_parallel_router(to_nodes))
                graph.add_edge(from_node, router_name)

        # Handle nodes with no dependents (terminal nodes)
        all_nodes = {node.id for node in template.nodes}
        nodes_with_dependents = set(dependency_map.keys())
        terminal_nodes = all_nodes - nodes_with_dependents

        logger.debug(f"   Terminal nodes (no dependents): {terminal_nodes}")

        for terminal_node in terminal_nodes:
            # Skip if this terminal node is a conditional source
            if terminal_node in conditional_source_nodes:
                logger.info(f"   ⏭️ Skipping END edge for '{terminal_node}' (has conditional edge)")
                continue

            # Terminal node - connect to END
            logger.info(f"   ✓ Terminal edge: {terminal_node} → END")
            graph.add_edge(terminal_node, END)

    def _create_parallel_router(self, target_nodes: List[str]) -> Callable:
        """
        Create parallel router using Send() API.

        Args:
            target_nodes: List of nodes to execute in parallel

        Returns:
            Router function
        """
        async def parallel_router(state: WorkflowStateGraph) -> List[Send]:
            """Route to multiple nodes in parallel."""
            logger.info(
                f"🔀 Parallel routing to {len(target_nodes)} nodes: "
                f"{', '.join(target_nodes)}"
            )
            return [Send(node_id, state) for node_id in target_nodes]

        return parallel_router

    def _add_conditional_edges(
        self,
        graph: StateGraph,
        template: WorkflowTemplate
    ):
        """
        Add conditional routing edges.

        Converts ConditionalEdge to LangGraph add_conditional_edges().
        """
        if not template.conditional_edges:
            logger.info("   No conditional edges to add")
            return

        for cond_edge in template.conditional_edges:
            condition_func = self._create_condition_function(cond_edge)

            # Build routing map
            routing_map = {
                cond.next_node: cond.next_node
                for cond in cond_edge.conditions
            }
            routing_map[cond_edge.default] = cond_edge.default

            logger.info(
                f"   ✓ Conditional edge from '{cond_edge.from_node}' "
                f"({len(cond_edge.conditions)} conditions, default: {cond_edge.default})"
            )
            for cond in cond_edge.conditions:
                logger.debug(
                    f"      - If {cond.field} {cond.operator} {cond.value} → {cond.next_node}"
                )

            graph.add_conditional_edges(
                cond_edge.from_node,
                condition_func,
                routing_map
            )

    def _create_condition_function(self, cond_edge: ConditionalEdge) -> Callable:
        """
        Create condition evaluation function for LangGraph.

        Args:
            cond_edge: ConditionalEdge definition

        Returns:
            Function that returns next node ID
        """
        def condition_function(state: WorkflowStateGraph) -> str:
            """Evaluate conditions and return next node."""
            for condition in cond_edge.conditions:
                if self.condition_evaluator._evaluate_condition(condition, state):
                    logger.info(
                        f"🔀 Condition matched: {condition.field} {condition.operator} "
                        f"{condition.value} → {condition.next_node}"
                    )
                    return condition.next_node

            # No condition matched - use default
            logger.info(f"🔀 No condition matched → {cond_edge.default}")
            return cond_edge.default

        return condition_function

    async def _execute_agent(
        self,
        agent_type: str,
        instruction: str,
        node: WorkflowNode,
        state: WorkflowStateGraph
    ) -> str:
        """
        Execute an agent and return output.

        Args:
            agent_type: Type of agent (researcher, analyst, writer, mcp_tool)
            instruction: Instruction to execute
            node: WorkflowNode for additional parameters
            state: Current state

        Returns:
            Agent output as string
        """
        # Import agents dynamically to avoid circular imports
        if agent_type == "supervisor":
            from agents.supervisor import get_supervisor_agent
            agent = await get_supervisor_agent()

        elif agent_type == "researcher":
            from agents.researcher import get_researcher_agent
            agent = get_researcher_agent()

        elif agent_type == "analyst":
            from agents.analyst import get_analyst_agent
            agent = get_analyst_agent()

        elif agent_type == "writer":
            from agents.writer import get_writer_agent
            agent = get_writer_agent()

        elif agent_type == "mcp_tool":
            # MCP tool execution
            from utils.mcp_client import MCPClient
            from utils.workflow_logger import log_mcp_call, log_mcp_response
            import json

            tool_name = node.tool_name
            if not tool_name:
                raise ValueError(f"Node {node.id}: mcp_tool requires tool_name")

            mcp_client = MCPClient()

            # Try to parse instruction as JSON
            cleaned_instruction = instruction.strip()
            try:
                # Parse JSON string to object and pass directly (no wrapper)
                # The agent's instructions should generate the complete JSON structure
                # required by the MCP tool (e.g., {"query_payload": {...}})
                arguments = json.loads(cleaned_instruction)
                logger.debug(f"   Parsed JSON successfully, passing directly to MCP")
            except json.JSONDecodeError:
                # If not valid JSON, pass as string in a basic wrapper
                arguments = {"query": cleaned_instruction}
                logger.warning(f"   Could not parse as JSON, passing as string in wrapper")

            # Log MCP call
            log_mcp_call(tool_name, arguments)

            result = await mcp_client.call_tool(tool_name, arguments)

            # Log MCP response
            log_mcp_response(tool_name, result)

            return result

        elif agent_type == "workflow":
            # Execute sub-workflow
            from workflows.registry import get_workflow_registry
            from workflows.engine import WorkflowEngine

            if not node.workflow_name:
                raise ValueError(f"Node {node.id}: workflow requires workflow_name")

            registry = get_workflow_registry(settings.workflow_templates_dir)
            sub_template = registry.get(node.workflow_name)

            if not sub_template:
                raise ValueError(f"Workflow template '{node.workflow_name}' not found")

            # Execute sub-workflow with nested state
            sub_engine = WorkflowEngine(mode="langgraph")
            sub_params = {**state.workflow_params, **node.workflow_params}

            # Substitute variables in sub_params
            for key, value in sub_params.items():
                if isinstance(value, str) and "{" in value and "}" in value:
                    sub_params[key] = self._substitute_variables(value, state)

            sub_result = await sub_engine.execute_workflow(
                template=sub_template,
                user_input=instruction,
                params=sub_params
            )

            if sub_result.success:
                return sub_result.final_output
            else:
                raise RuntimeError(f"Sub-workflow failed: {sub_result.error}")

        elif agent_type == "library":
            # Execute library function
            from libraries.executor import get_library_executor
            from libraries.registry import LibraryCapabilities

            if not node.library_name or not node.function_name:
                raise ValueError(
                    f"Node {node.id}: library requires library_name and function_name"
                )

            logger.debug(f"   Executing library: {node.library_name}.{node.function_name}")

            # Configure capabilities
            capabilities = LibraryCapabilities(
                filesystem_read=True,
                filesystem_write=True,
                network_access=True
            )

            # Get executor and execute
            executor = get_library_executor(capabilities=capabilities)
            output = await executor.execute_library_node(
                node,
                state,
                state.workflow_params
            )

            return output

        else:
            raise ValueError(f"Unknown agent type: {agent_type}")

        # Log agent invocation
        from utils.workflow_logger import log_agent_invocation, log_agent_response
        log_agent_invocation(agent_type, instruction)

        # Invoke agent
        messages = [HumanMessage(content=instruction)]
        result = await agent.ainvoke({"messages": messages})

        # Extract output
        if "messages" in result:
            last_message = result["messages"][-1]
            if hasattr(last_message, "content"):
                output = last_message.content
                log_agent_response(agent_type, output)
                return output

        output = str(result)
        log_agent_response(agent_type, output)
        return output

    def _substitute_variables(
        self,
        template_str: str,
        state: WorkflowStateGraph
    ) -> str:
        """
        Substitute variables in instruction template.

        Supports:
        - {user_input} - Original user input
        - {node_id} - Output from specific node
        - {param_name} - Workflow parameters
        """
        result = template_str

        # Substitute user input
        if "{user_input}" in result:
            user_input = getattr(state, "user_input", "") or ""
            result = result.replace("{user_input}", user_input)

        # Substitute node outputs
        node_outputs = getattr(state, "node_outputs", {}) or {}
        for node_id, output in node_outputs.items():
            placeholder = f"{{{node_id}}}"
            if placeholder in result:
                result = result.replace(placeholder, output)

        # Substitute workflow parameters
        workflow_params = getattr(state, "workflow_params", {}) or {}
        for param_name, param_value in workflow_params.items():
            placeholder = f"{{{param_name}}}"
            if placeholder in result:
                result = result.replace(placeholder, str(param_value))

        return result

    def _extract_metadata(self, output: str, node_id: str = None) -> Dict[str, Any]:
        """
        Extract metadata from output for conditional routing.

        Returns:
            Dictionary with extracted metadata fields
        """
        from workflows.conditions import extract_sentiment_score

        metadata = {}

        # Extract sentiment
        sentiment = extract_sentiment_score(output)
        if sentiment is not None:
            metadata["sentiment_score"] = sentiment

        # Extract content length
        metadata["content_length"] = len(output)

        # Special handling for check_result node - parse has_error field
        if node_id == "check_result":
            custom_metadata = {}

            # Parse the structured output from analyst
            if "has_error: true" in output.lower() or "has_error:true" in output.lower():
                custom_metadata["has_error"] = True
                logger.info(f"   🔍 Extracted metadata: has_error=True (error detected)")
            elif "has_error: false" in output.lower() or "has_error:false" in output.lower():
                custom_metadata["has_error"] = False
                logger.info(f"   🔍 Extracted metadata: has_error=False (success)")
            else:
                # Default to error if we can't parse (safer)
                custom_metadata["has_error"] = True
                logger.warning(f"   ⚠️ Could not parse has_error from output, defaulting to True")

            metadata["custom_metadata"] = custom_metadata

        return metadata


def compile_workflow(template: WorkflowTemplate) -> Any:
    """
    Convenience function to compile a workflow template.

    Args:
        template: WorkflowTemplate to compile

    Returns:
        CompiledGraph ready for execution
    """
    compiler = LangGraphWorkflowCompiler()
    return compiler.compile(template)
