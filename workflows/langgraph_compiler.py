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
import operator
from typing import Dict, Any, List, Callable, Literal, Optional, Annotated
from collections import defaultdict

from langgraph.graph import StateGraph, START, END
from langgraph.constants import Send
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from pydantic import Field
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


def merge_dicts(left: Dict, right: Dict) -> Dict:
    """Merge two dictionaries for parallel state updates."""
    return {**left, **right}


def keep_last_value(left: Any, right: Any) -> Any:
    """Keep the last non-None value for single-value fields."""
    return right if right is not None else left


class WorkflowStateGraph(WorkflowState):
    """
    Extended WorkflowState for LangGraph compatibility.

    Adds LangGraph-specific fields while maintaining backward compatibility.
    Uses Annotated types with reducers for parallel execution support.
    """
    # Override fields from WorkflowState with Annotated reducers for parallel execution
    workflow_params: Annotated[Dict[str, Any], merge_dicts] = Field(default_factory=dict)
    current_node: Annotated[Optional[str], keep_last_value] = None
    completed_nodes: Annotated[List[str], operator.add] = Field(default_factory=list)
    node_outputs: Annotated[Dict[str, str], merge_dicts] = Field(default_factory=dict)
    workflow_history: Annotated[List[WorkflowExecutionLog], operator.add] = Field(default_factory=list)
    sentiment_score: Annotated[Optional[float], keep_last_value] = None
    content_length: Annotated[Optional[int], keep_last_value] = None
    custom_metadata: Annotated[Dict[str, Any], merge_dicts] = Field(default_factory=dict)
    parent_workflow_stack: Annotated[List[str], operator.add] = Field(default_factory=list)

    # Loop context tracking (for @latest, @first, @previous alias resolution)
    loop_context: Annotated[Dict[str, Any], merge_dicts] = Field(default_factory=dict)
    # Structure: {"pattern_name": {"outputs": ["node1", "node2", "node3"]}}
    # Example: {"review_code": {"outputs": ["review_code", "review_refactored_code"]}}

    # User input (for node execution)
    user_input: Optional[str] = None

    # Execution metadata
    execution_start_time: Optional[float] = None
    error: Annotated[Optional[str], keep_last_value] = None

    # Retry tracking (per-node)
    node_retry_counts: Annotated[Dict[str, int], merge_dicts] = Field(default_factory=dict)
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
        self.loop_patterns = {}  # Loop patterns detected during compilation

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

        # Detect loop patterns for alias resolution
        self.loop_patterns = self._detect_loop_patterns(template)

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
            # Multiple entry nodes - add parallel edges from START
            # LangGraph will automatically execute all nodes in parallel
            logger.info(f"🎯 Adding {len(entry_nodes)} parallel entry edges from START")
            for entry_node in entry_nodes:
                logger.debug(f"   ✓ START → {entry_node}")
                graph.add_edge(START, entry_node)

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

    def _detect_loop_patterns(self, template: WorkflowTemplate) -> Dict[str, List[str]]:
        """
        Detect loop patterns in workflow nodes.

        Identifies nodes that represent iterations of the same concept,
        such as "review_code" and "review_refactored_code".

        Pattern detection rules:
        - If node B's name contains node A's name as prefix/substring,
          they belong to the same pattern family
        - Example: "review_code" and "review_refactored_code" → pattern "review_code"

        Returns:
            Dict mapping pattern_name -> [node_ids in execution order]
            Example: {"review_code": ["review_code", "review_refactored_code"]}
        """
        patterns = {}
        node_ids = [n.id for n in template.nodes]

        # Find base patterns by looking for common prefixes
        # Split node names by "_" and check for shared prefixes
        # Example: "review_code" and "review_refactored_code" share "review" prefix
        for base_node in node_ids:
            related_nodes = [base_node]
            base_parts = base_node.split("_")

            # Find nodes that share common prefix parts with base_node
            for other_node in node_ids:
                if other_node == base_node:
                    continue

                other_parts = other_node.split("_")

                # Check if they share a significant common prefix (at least 2 parts)
                # or if other_node starts with base_node as prefix
                if other_node.startswith(base_node + "_"):
                    related_nodes.append(other_node)
                    logger.debug(f"      Pattern match: '{other_node}' starts with '{base_node}_'")
                elif len(base_parts) >= 2 and len(other_parts) >= 2:
                    # Check if first 2 parts match (e.g., "review_code" and "review_refactored")
                    if base_parts[0] == other_parts[0] and "refactored" in other_node:
                        # Special case for refactored versions
                        related_nodes.append(other_node)
                        logger.debug(f"      Pattern match: '{base_node}' and '{other_node}' share prefix and refactored")

            # Only consider it a pattern if there are multiple related nodes
            if len(related_nodes) > 1:
                patterns[base_node] = related_nodes
                logger.debug(f"   Pattern detected: '{base_node}' → {related_nodes}")

        if patterns:
            logger.info(f"🔄 Loop patterns detected: {list(patterns.keys())}")
        else:
            logger.debug("   No loop patterns detected")

        return patterns

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

                # Track loop context for alias resolution
                new_loop_context = dict(getattr(state, "loop_context", {}) or {})

                # Check if this node belongs to any detected pattern
                for pattern, pattern_nodes in self.loop_patterns.items():
                    if node.id in pattern_nodes:
                        # Initialize pattern context if needed
                        if pattern not in new_loop_context:
                            new_loop_context[pattern] = {"outputs": []}

                        # Add this node to the pattern's execution history
                        if node.id not in new_loop_context[pattern]["outputs"]:
                            new_loop_context[pattern]["outputs"].append(node.id)
                            logger.debug(f"   🔄 Loop tracking: {pattern} → {new_loop_context[pattern]['outputs']}")

                logger.debug(f"   State update: completed_nodes={new_completed}, retry_count={new_retry_counts.get(node.id)}, metadata={list(metadata_updates.keys())}")

                return {
                    "node_outputs": new_outputs,
                    "completed_nodes": new_completed,
                    "current_node": node.id,
                    "workflow_history": new_history,
                    "node_retry_counts": new_retry_counts,
                    "loop_context": new_loop_context,
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
                # Multiple dependencies - use conditional edge with Send() for parallel execution
                logger.info(f"   ✓ Parallel conditional edge: {from_node} → {to_nodes}")
                graph.add_conditional_edges(
                    from_node,
                    self._create_parallel_router(to_nodes),
                    # LangGraph expects path_map but ignores it for Send() returns
                    {}
                )

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
        - {@latest:pattern} - Latest output in loop pattern
        - {@first:pattern} - First output in loop pattern
        - {@previous:pattern} - Previous iteration output
        """
        import re

        result = template_str

        # Substitute aliases FIRST (before regular variables)
        # Pattern: {@alias:pattern_name}
        alias_pattern = r'\{@(\w+):(\w+)\}'
        alias_matches = re.findall(alias_pattern, result)

        node_outputs = getattr(state, "node_outputs", {}) or {}

        for alias, pattern in alias_matches:
            placeholder = f"{{@{alias}:{pattern}}}"

            # Resolve alias to actual node_id
            resolved_node_id = self._resolve_alias(alias, pattern, state, self.loop_patterns)

            # Get output from resolved node
            if resolved_node_id in node_outputs:
                resolved_output = node_outputs[resolved_node_id]
                result = result.replace(placeholder, resolved_output)
                logger.info(f"   ✨ Alias {placeholder} → output from '{resolved_node_id}'")
            else:
                # Node not executed yet, leave placeholder or warn
                logger.warning(
                    f"   ⚠️ Alias {placeholder} resolved to '{resolved_node_id}' "
                    f"but no output available (node not executed yet)"
                )
                # Leave placeholder as-is for now
                # result = result.replace(placeholder, f"<{resolved_node_id} not executed>")

        # Substitute user input
        if "{user_input}" in result:
            user_input = getattr(state, "user_input", "") or ""
            result = result.replace("{user_input}", user_input)

        # Substitute node outputs
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

        # Validate: Check for unresolved placeholders
        # First, remove code blocks (```json...```, ```python...```) to avoid false positives
        cleaned_result = re.sub(r'```[a-z]*.*?```', '', result, flags=re.DOTALL)

        # Find potential placeholders
        # Match {word_with_underscores} but NOT JSON-like structures
        # Valid placeholders: {user_input}, {node_id}, {@latest:pattern}
        # Invalid (JSON): {"key": "value"}, {a, b, c}
        potential_placeholders = re.findall(r'\{([^}]+)\}', cleaned_result)

        # Filter to keep only legitimate placeholders (not JSON)
        remaining_placeholders = []
        for p in potential_placeholders:
            # Skip if it looks like JSON (contains quotes, colons outside of @alias:, commas)
            if ('"' in p or
                "'" in p or
                ',' in p or
                (':' in p and not p.startswith('@'))):
                # This looks like JSON, skip validation
                continue

            # Skip very short placeholders (1-2 chars) - likely part of JSON examples
            # Real placeholders are longer: {user_input}, {define_requirements}, etc.
            if len(p.strip()) <= 2:
                continue

            # Keep for validation
            remaining_placeholders.append(p)

        if remaining_placeholders:
            # Filter out alias placeholders (start with @) - they're handled separately
            unresolved = [p for p in remaining_placeholders if not p.startswith('@')]

            if unresolved:
                # Build helpful error message
                valid_placeholders = [
                    "user_input",
                    "<node_id> (any executed node)",
                    "<param_name> (workflow parameters)",
                    "@latest:<pattern>",
                    "@first:<pattern>",
                    "@previous:<pattern>"
                ]

                logger.error(
                    f"❌ Unresolved placeholder(s) found: {unresolved}\n"
                    f"   Available placeholders: {', '.join(valid_placeholders)}\n"
                    f"   Node outputs available: {list(node_outputs.keys())}\n"
                    f"   Workflow params available: {list(workflow_params.keys())}"
                )

                raise ValueError(
                    f"Unresolved placeholder(s) in instruction: {unresolved}\n"
                    f"Available placeholders:\n"
                    f"  - {{user_input}} - Original user input\n"
                    f"  - {{<node_id>}} - Output from any executed node: {list(node_outputs.keys())}\n"
                    f"  - {{<param_name>}} - Workflow parameters: {list(workflow_params.keys())}\n"
                    f"  - {{@latest:<pattern>}} - Latest output in loop pattern\n"
                    f"  - {{@first:<pattern>}} - First output in loop pattern\n"
                    f"  - {{@previous:<pattern>}} - Previous iteration output"
                )

        return result

    def _resolve_alias(
        self,
        alias: str,
        pattern: str,
        state: WorkflowStateGraph,
        loop_patterns: Dict[str, List[str]]
    ) -> str:
        """
        Resolve alias (@latest, @first, @previous) to actual node_id.

        Args:
            alias: "latest", "first", or "previous"
            pattern: Base pattern name (e.g., "review_code")
            state: Current workflow state
            loop_patterns: Detected loop patterns from _detect_loop_patterns()

        Returns:
            node_id to read output from

        Examples:
            _resolve_alias("latest", "review_code", state, patterns)
            → "review_refactored_code" (if executed) or "review_code"
        """
        # Get loop context for this pattern
        loop_ctx = getattr(state, "loop_context", {}) or {}
        pattern_ctx = loop_ctx.get(pattern, {"outputs": []})
        executed_nodes = pattern_ctx.get("outputs", [])

        # Get node outputs to check what's available
        node_outputs = getattr(state, "node_outputs", {}) or {}

        # Get pattern nodes from detected patterns
        pattern_nodes = loop_patterns.get(pattern, [pattern])

        if alias == "latest":
            # Return the most recently executed node in the pattern
            # Check in reverse order (most recent first)
            for node_id in reversed(executed_nodes):
                if node_id in node_outputs:
                    logger.debug(f"   🔗 Alias @latest:{pattern} → {node_id}")
                    return node_id

            # Fallback: check if any pattern node has output
            for node_id in reversed(pattern_nodes):
                if node_id in node_outputs:
                    logger.debug(f"   🔗 Alias @latest:{pattern} → {node_id} (fallback)")
                    return node_id

            # Ultimate fallback: return base pattern
            logger.debug(f"   🔗 Alias @latest:{pattern} → {pattern} (base)")
            return pattern

        elif alias == "first":
            # Always return the first node in the pattern (base pattern name)
            logger.debug(f"   🔗 Alias @first:{pattern} → {pattern}")
            return pattern

        elif alias == "previous":
            # Return the node from previous iteration
            if len(executed_nodes) >= 2:
                # Get second-to-last executed node
                prev_node = executed_nodes[-2]
                logger.debug(f"   🔗 Alias @previous:{pattern} → {prev_node}")
                return prev_node
            elif len(executed_nodes) == 1:
                # Only one node executed, return it
                logger.debug(f"   🔗 Alias @previous:{pattern} → {executed_nodes[0]}")
                return executed_nodes[0]
            else:
                # No nodes executed yet, return base pattern
                logger.debug(f"   🔗 Alias @previous:{pattern} → {pattern} (base)")
                return pattern

        else:
            logger.warning(f"   ⚠️ Unknown alias '{alias}', falling back to pattern: {pattern}")
            return pattern

    def _extract_metadata(self, output: str, node_id: str = None) -> Dict[str, Any]:
        """
        Extract metadata from output for conditional routing.

        Returns:
            Dictionary with extracted metadata fields
        """
        from workflows.conditions import extract_sentiment_score
        import json
        import re

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

        # Special handling for quality_gate and review_refactored_code - parse JSON with quality metrics
        elif node_id in ("quality_gate", "review_refactored_code"):
            custom_metadata = {}

            # Extract JSON from output (supports markdown code blocks)
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', output, re.DOTALL)
            if not json_match:
                # Fallback: search for JSON object directly
                json_match = re.search(r'(\{[^{}]*"quality_score"[^{}]*\})', output, re.DOTALL)

            if json_match:
                try:
                    data = json.loads(json_match.group(1))
                    custom_metadata["quality_score"] = float(data.get("quality_score", 0.0))
                    custom_metadata["iteration_count"] = int(data.get("iteration_count", 0))
                    logger.info(
                        f"   🔍 Extracted metadata from {node_id}: "
                        f"quality_score={custom_metadata['quality_score']}, "
                        f"iteration_count={custom_metadata['iteration_count']}"
                    )
                except (json.JSONDecodeError, ValueError, KeyError) as e:
                    logger.warning(f"   ⚠️ Failed to parse JSON from {node_id} output: {e}")
                    # Fallback to defaults to prevent infinite loop
                    custom_metadata["quality_score"] = 0.0
                    custom_metadata["iteration_count"] = 0
            else:
                logger.warning(f"   ⚠️ No JSON found in {node_id} output")
                # Fallback to defaults
                custom_metadata["quality_score"] = 0.0
                custom_metadata["iteration_count"] = 0

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
