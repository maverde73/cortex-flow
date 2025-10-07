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

        # Create StateGraph
        graph = StateGraph(WorkflowStateGraph)

        # Analyze workflow structure
        parallel_groups = self._identify_parallel_groups(template)
        entry_nodes = self._identify_entry_nodes(template)

        # Add nodes
        for node in template.nodes:
            node_function = self._create_node_function(node, template)
            graph.add_node(node.id, node_function)

        # Add entry point
        if len(entry_nodes) == 1:
            # Single entry node
            graph.set_entry_point(entry_nodes[0])
        else:
            # Multiple entry nodes - create router
            graph.add_node("__entry_router__", self._create_entry_router(entry_nodes))
            graph.set_entry_point("__entry_router__")

            for entry_node in entry_nodes:
                graph.add_edge("__entry_router__", entry_node)

        # Add edges (dependencies and flow)
        self._add_edges(graph, template, parallel_groups)

        # Add conditional edges
        self._add_conditional_edges(graph, template)

        # Compile
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

        Returns:
            List of node IDs that can be entry points
        """
        all_dependencies = set()
        for node in template.nodes:
            all_dependencies.update(node.depends_on)

        entry_nodes = [
            node.id for node in template.nodes
            if node.id not in all_dependencies
        ]

        return entry_nodes or [template.nodes[0].id]  # Fallback to first node

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
            start_time = time.time()

            try:
                # Substitute variables in instruction
                instruction = self._substitute_variables(
                    node.instruction,
                    state
                )

                logger.info(f"📍 Executing node '{node.id}' (agent: {node.agent})")

                # Execute agent
                output = await self._execute_agent(
                    agent_type=node.agent,
                    instruction=instruction,
                    node=node,
                    state=state
                )

                execution_time = time.time() - start_time

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
                new_outputs = dict(state.get("node_outputs", {}))
                new_outputs[node.id] = output

                new_completed = list(state.get("completed_nodes", []))
                new_completed.append(node.id)

                new_history = list(state.get("workflow_history", []))
                new_history.append(log_entry)

                # Extract metadata for conditional routing
                metadata_updates = self._extract_metadata(output)

                return {
                    "node_outputs": new_outputs,
                    "completed_nodes": new_completed,
                    "current_node": node.id,
                    "workflow_history": new_history,
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

                new_history = list(state.get("workflow_history", []))
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
            if not state.get("execution_start_time"):
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
        """
        # Build dependency map
        dependency_map = {}
        for node in template.nodes:
            if node.depends_on:
                for dep in node.depends_on:
                    if dep not in dependency_map:
                        dependency_map[dep] = []
                    dependency_map[dep].append(node.id)

        # Add edges for dependencies
        for from_node, to_nodes in dependency_map.items():
            if len(to_nodes) == 1:
                # Single dependency - simple edge
                graph.add_edge(from_node, to_nodes[0])
            else:
                # Multiple dependencies - create router for parallel execution
                router_name = f"__router_{from_node}__"
                graph.add_node(router_name, self._create_parallel_router(to_nodes))
                graph.add_edge(from_node, router_name)

        # Handle nodes with no dependents (terminal nodes)
        all_nodes = {node.id for node in template.nodes}
        nodes_with_dependents = set(dependency_map.keys())
        terminal_nodes = all_nodes - nodes_with_dependents

        for terminal_node in terminal_nodes:
            # Check if this node has explicit dependencies
            node = next(n for n in template.nodes if n.id == terminal_node)
            if node.depends_on:
                continue  # Will be connected via dependency

            # Terminal node - connect to END
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
        for cond_edge in template.conditional_edges:
            condition_func = self._create_condition_function(cond_edge)

            # Build routing map
            routing_map = {
                cond.next_node: cond.next_node
                for cond in cond_edge.conditions
            }
            routing_map[cond_edge.default] = cond_edge.default

            graph.add_conditional_edges(
                cond_edge.from_node,
                condition_func,
                routing_map
            )

            logger.debug(
                f"Added conditional edge from {cond_edge.from_node} "
                f"with {len(cond_edge.conditions)} conditions"
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
                if self.condition_evaluator.evaluate(condition, state):
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
        if agent_type == "researcher":
            from agents.researcher import get_researcher_agent
            agent = await get_researcher_agent()

        elif agent_type == "analyst":
            from agents.analyst import get_analyst_agent
            agent = await get_analyst_agent()

        elif agent_type == "writer":
            from agents.writer import get_writer_agent
            agent = await get_writer_agent()

        elif agent_type == "mcp_tool":
            # MCP tool execution
            from utils.mcp_client import MCPClient

            tool_name = node.tool_name
            if not tool_name:
                raise ValueError(f"Node {node.id}: mcp_tool requires tool_name")

            mcp_client = MCPClient()
            result = await mcp_client.call_tool(tool_name, {"query": instruction})
            return result

        else:
            raise ValueError(f"Unknown agent type: {agent_type}")

        # Invoke agent
        messages = [HumanMessage(content=instruction)]
        result = await agent.ainvoke({"messages": messages})

        # Extract output
        if "messages" in result:
            last_message = result["messages"][-1]
            if hasattr(last_message, "content"):
                return last_message.content

        return str(result)

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
            user_input = state.get("user_input", "")
            result = result.replace("{user_input}", user_input)

        # Substitute node outputs
        node_outputs = state.get("node_outputs", {})
        for node_id, output in node_outputs.items():
            placeholder = f"{{{node_id}}}"
            if placeholder in result:
                result = result.replace(placeholder, output)

        # Substitute workflow parameters
        workflow_params = state.get("workflow_params", {})
        for param_name, param_value in workflow_params.items():
            placeholder = f"{{{param_name}}}"
            if placeholder in result:
                result = result.replace(placeholder, str(param_value))

        return result

    def _extract_metadata(self, output: str) -> Dict[str, Any]:
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
