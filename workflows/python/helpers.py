"""
Helper Functions for Python Workflow Definition

Provides shorthand functions to simplify workflow creation in Python.
Reduces boilerplate and makes workflow definitions more readable.
"""

from typing import List, Dict, Any, Optional
from schemas.workflow_schemas import (
    WorkflowNode,
    WorkflowCondition,
    ConditionalEdge,
    ConditionOperator,
    LLMConfig
)


# ============================================================================
# LLM Node Helpers
# ============================================================================

def llm_node(
    node_id: str,
    instruction: str,
    provider: str = "openrouter",
    model: str = "deepseek/deepseek-v3.2-exp",
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    system_prompt: Optional[str] = None,
    include_history: bool = False,
    history_nodes: Optional[List[str]] = None,
    depends_on: Optional[List[str]] = None,
    timeout: int = 120
) -> WorkflowNode:
    """
    Create an LLM node with sensible defaults.

    Args:
        node_id: Unique node identifier
        instruction: Instruction template (can use {variables})
        provider: LLM provider (openrouter, openai, anthropic, groq, google)
        model: Model identifier
        temperature: Sampling temperature (0.0-2.0)
        max_tokens: Maximum tokens in response
        system_prompt: System prompt to set context
        include_history: Include previous node outputs as context
        history_nodes: Specific node IDs to include in history
        depends_on: Node dependencies
        timeout: Timeout in seconds

    Returns:
        Configured WorkflowNode

    Example:
        node = llm_node(
            "analyze_data",
            "Analyze this data: {raw_data}",
            temperature=0.1,
            system_prompt="You are a data analyst",
            depends_on=["fetch_data"]
        )
    """
    return WorkflowNode(
        id=node_id,
        agent="llm",
        instruction=instruction,
        llm_config=LLMConfig(
            provider=provider,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=system_prompt,
            include_workflow_history=include_history,
            history_nodes=history_nodes
        ),
        depends_on=depends_on or [],
        timeout=timeout
    )


def llm_chain_node(
    node_id: str,
    instruction: str,
    history_nodes: List[str],
    provider: str = "openrouter",
    model: str = "deepseek/deepseek-v3.2-exp",
    temperature: float = 0.7,
    system_prompt: Optional[str] = None,
    depends_on: Optional[List[str]] = None,
    timeout: int = 120
) -> WorkflowNode:
    """
    Create an LLM node that includes specific previous nodes in context.
    Useful for multi-step reasoning where the LLM needs to see previous outputs.

    Args:
        node_id: Unique node identifier
        instruction: Instruction template
        history_nodes: List of node IDs to include in conversation history
        provider: LLM provider
        model: Model identifier
        temperature: Sampling temperature
        system_prompt: System prompt
        depends_on: Node dependencies
        timeout: Timeout in seconds

    Returns:
        Configured WorkflowNode with history context

    Example:
        node = llm_chain_node(
            "refine_answer",
            "Refine your previous answer",
            history_nodes=["draft_answer", "feedback"],
            depends_on=["feedback"]
        )
    """
    return llm_node(
        node_id=node_id,
        instruction=instruction,
        provider=provider,
        model=model,
        temperature=temperature,
        system_prompt=system_prompt,
        include_history=True,
        history_nodes=history_nodes,
        depends_on=depends_on,
        timeout=timeout
    )


# ============================================================================
# MCP Node Helpers
# ============================================================================

def mcp_tool_node(
    node_id: str,
    tool_name: str,
    instruction: str,
    server_name: Optional[str] = None,
    depends_on: Optional[List[str]] = None,
    timeout: int = 60
) -> WorkflowNode:
    """
    Create an MCP tool node.

    Args:
        node_id: Unique node identifier
        tool_name: MCP tool name (e.g., "execute_query")
        instruction: Tool arguments (can use {variables})
        server_name: MCP server name (optional, auto-detected if not provided)
        depends_on: Node dependencies
        timeout: Timeout in seconds

    Returns:
        Configured WorkflowNode

    Example:
        node = mcp_tool_node(
            "run_query",
            "execute_query",
            "{generated_query}",
            depends_on=["generate_query"]
        )
    """
    return WorkflowNode(
        id=node_id,
        agent="mcp_tool",
        tool_name=tool_name,
        server_name=server_name,
        instruction=instruction,
        depends_on=depends_on or [],
        timeout=timeout
    )


def mcp_resource_node(
    node_id: str,
    resource_uri: str,
    server_name: str,
    instruction: str = "Read resource",
    depends_on: Optional[List[str]] = None,
    timeout: int = 30
) -> WorkflowNode:
    """
    Create an MCP resource node.

    Args:
        node_id: Unique node identifier
        resource_uri: Resource URI (e.g., "welcome://message")
        server_name: MCP server name
        instruction: Description of what to read
        depends_on: Node dependencies
        timeout: Timeout in seconds

    Returns:
        Configured WorkflowNode

    Example:
        node = mcp_resource_node(
            "get_docs",
            "docs://api",
            "my-docs-server"
        )
    """
    return WorkflowNode(
        id=node_id,
        agent="mcp_resource",
        resource_uri=resource_uri,
        server_name=server_name,
        instruction=instruction,
        depends_on=depends_on or [],
        timeout=timeout
    )


# ============================================================================
# Conditional Routing Helpers
# ============================================================================

def conditional_edge(
    from_node: str,
    conditions: List[WorkflowCondition],
    default: str
) -> ConditionalEdge:
    """
    Create a conditional edge for routing.

    Args:
        from_node: Source node ID
        conditions: List of conditions to check
        default: Default node if no condition matches

    Returns:
        Configured ConditionalEdge

    Example:
        edge = conditional_edge(
            "check_result",
            [
                condition("custom_metadata.has_error", "equals", False, "success_handler"),
                condition("custom_metadata.has_error", "equals", True, "error_handler")
            ],
            default="error_handler"
        )
    """
    return ConditionalEdge(
        from_node=from_node,
        conditions=conditions,
        default=default
    )


def condition(
    field: str,
    operator: str,
    value: Any,
    next_node: str
) -> WorkflowCondition:
    """
    Create a workflow condition.

    Args:
        field: State field to check
        operator: Comparison operator (equals, >, <, contains, etc.)
        value: Value to compare against
        next_node: Node to route to if condition is true

    Returns:
        Configured WorkflowCondition

    Example:
        cond = condition(
            "custom_metadata.score",
            ">",
            0.8,
            "high_quality_path"
        )
    """
    # Convert string operator to ConditionOperator enum
    operator_map = {
        "equals": ConditionOperator.EQUALS,
        "not_equals": ConditionOperator.NOT_EQUALS,
        ">": ConditionOperator.GREATER_THAN,
        "<": ConditionOperator.LESS_THAN,
        ">=": ConditionOperator.GREATER_EQUAL,
        "<=": ConditionOperator.LESS_EQUAL,
        "contains": ConditionOperator.CONTAINS,
        "not_contains": ConditionOperator.NOT_CONTAINS,
        "in": ConditionOperator.IN,
        "not_in": ConditionOperator.NOT_IN,
    }

    return WorkflowCondition(
        field=field,
        operator=operator_map.get(operator, ConditionOperator.EQUALS),
        value=value,
        next_node=next_node
    )


def retry_on_error(
    check_node: str,
    retry_node: str,
    success_node: str,
    error_field: str = "custom_metadata.has_error"
) -> ConditionalEdge:
    """
    Create a retry pattern: if error detected, retry from a previous node.

    Args:
        check_node: Node that checks for errors
        retry_node: Node to retry from if error detected
        success_node: Node to route to on success
        error_field: State field that indicates error (default: custom_metadata.has_error)

    Returns:
        Configured ConditionalEdge for retry pattern

    Example:
        edge = retry_on_error(
            "check_result",
            "generate_query",  # Retry from here
            "format_output"    # Go here on success
        )
    """
    return conditional_edge(
        from_node=check_node,
        conditions=[
            condition(error_field, "equals", False, success_node)
        ],
        default=retry_node
    )


# ============================================================================
# Workflow Composition Helpers
# ============================================================================

def sub_workflow_node(
    node_id: str,
    workflow_name: str,
    instruction: str,
    params: Optional[Dict[str, Any]] = None,
    depends_on: Optional[List[str]] = None,
    max_depth: int = 5,
    timeout: int = 300
) -> WorkflowNode:
    """
    Create a node that executes a sub-workflow.

    Args:
        node_id: Unique node identifier
        workflow_name: Name of workflow to execute
        instruction: User input for the sub-workflow
        params: Parameters to pass to sub-workflow
        depends_on: Node dependencies
        max_depth: Maximum recursion depth
        timeout: Timeout in seconds

    Returns:
        Configured WorkflowNode

    Example:
        node = sub_workflow_node(
            "detailed_analysis",
            "data_analysis_workflow",
            "Analyze {raw_data}",
            params={"analysis_type": "deep"},
            depends_on=["fetch_data"]
        )
    """
    return WorkflowNode(
        id=node_id,
        agent="workflow",
        workflow_name=workflow_name,
        instruction=instruction,
        workflow_params=params or {},
        max_depth=max_depth,
        depends_on=depends_on or [],
        timeout=timeout
    )


# ============================================================================
# Common Patterns
# ============================================================================

def parallel_nodes(
    node_ids: List[str],
    group_name: str
) -> List[WorkflowNode]:
    """
    Mark multiple nodes to execute in parallel.

    Args:
        node_ids: List of node IDs to execute in parallel
        group_name: Name for the parallel group

    Returns:
        List of nodes with parallel_group set

    Note:
        This is a helper that modifies nodes after creation.
        Use it like:
            nodes = [node1, node2, node3]
            nodes = parallel_nodes([n.id for n in nodes], "batch_processing")

    Example:
        nodes = [
            llm_node("task1", "Do A"),
            llm_node("task2", "Do B"),
            llm_node("task3", "Do C")
        ]
        # Mark task1 and task2 to run in parallel
        for node in nodes:
            if node.id in ["task1", "task2"]:
                node.parallel_group = "batch_1"
    """
    # This is more of a documentation helper
    # In practice, set parallel_group directly on nodes
    pass


# ============================================================================
# Preset LLM Configs
# ============================================================================

DEEPSEEK_FAST = LLMConfig(
    provider="openrouter",
    model="deepseek/deepseek-v3.2-exp",
    temperature=0.1,
    max_tokens=2000
)

DEEPSEEK_CREATIVE = LLMConfig(
    provider="openrouter",
    model="deepseek/deepseek-v3.2-exp",
    temperature=0.8,
    max_tokens=4000
)

GPT4_TURBO = LLMConfig(
    provider="openai",
    model="gpt-4-turbo",
    temperature=0.7,
    max_tokens=4000
)

CLAUDE_SONNET = LLMConfig(
    provider="anthropic",
    model="claude-3.5-sonnet",
    temperature=0.7,
    max_tokens=4000
)
