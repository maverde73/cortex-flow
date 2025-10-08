"""
Workflow System - Pydantic Schemas

Defines the schema for workflow templates, execution state, and results.
Supports parallel execution, conditional routing, and MCP tool integration.
"""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from enum import Enum


class ConditionOperator(str, Enum):
    """Supported operators for conditional routing"""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    IN = "in"
    NOT_IN = "not_in"


class WorkflowCondition(BaseModel):
    """Condition for conditional routing"""
    field: str = Field(..., description="State field to check")
    operator: ConditionOperator = Field(..., description="Comparison operator")
    value: Any = Field(..., description="Value to compare against")
    next_node: str = Field(..., description="Node to route to if condition true")


class ConditionalEdge(BaseModel):
    """Conditional edge definition"""
    from_node: str = Field(..., description="Source node")
    conditions: List[WorkflowCondition] = Field(..., description="List of conditions")
    default: str = Field(..., description="Default node if no condition matches")


class WorkflowNode(BaseModel):
    """Workflow node definition"""
    id: str = Field(..., description="Unique node identifier")
    agent: str = Field(..., description="Agent to execute (researcher, analyst, writer, mcp_tool, workflow)")
    instruction: str = Field(..., description="Instruction template (can use {variables})")
    depends_on: List[str] = Field(default_factory=list, description="Node dependencies")
    parallel_group: Optional[str] = Field(None, description="Parallel execution group")
    timeout: int = Field(120, description="Timeout in seconds")
    tool_name: Optional[str] = Field(None, description="MCP tool name (if agent=mcp_tool)")
    params: Dict[str, Any] = Field(default_factory=dict, description="Additional parameters")
    template: Optional[str] = Field(None, description="Template name for writer")
    use_mcp_prompt: bool = Field(
        default=False,
        description=(
            "If True, automatically populate instruction with MCP prompt guidance. "
            "Only applies when agent='mcp_tool' and MCP server provides prompts"
        )
    )
    # New fields for workflow composition
    workflow_name: Optional[str] = Field(None, description="Workflow name to execute (if agent=workflow)")
    workflow_params: Dict[str, Any] = Field(default_factory=dict, description="Parameters to pass to sub-workflow")
    max_depth: int = Field(5, description="Maximum recursion depth for nested workflows")


class WorkflowTemplate(BaseModel):
    """Complete workflow template"""
    name: str = Field(..., description="Workflow name")
    version: str = Field("1.0", description="Template version")
    description: str = Field(..., description="Workflow description")
    trigger_patterns: List[str] = Field(
        default_factory=list,
        description="Regex patterns to auto-match this workflow"
    )
    nodes: List[WorkflowNode] = Field(..., description="Workflow nodes")
    conditional_edges: List[ConditionalEdge] = Field(
        default_factory=list,
        description="Conditional routing rules"
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Workflow-level parameters"
    )


class NodeExecutionResult(BaseModel):
    """Result of a single node execution"""
    node_id: str
    agent: str
    output: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    execution_time: float
    success: bool
    error: Optional[str] = None


class WorkflowExecutionLog(BaseModel):
    """Log entry for workflow execution"""
    timestamp: float
    node_id: str
    agent: str
    action: str
    details: Dict[str, Any] = Field(default_factory=dict)


class WorkflowResult(BaseModel):
    """Final result of workflow execution"""
    workflow_name: str
    success: bool
    final_output: str
    execution_log: List[WorkflowExecutionLog]
    node_results: List[NodeExecutionResult]
    total_execution_time: float
    error: Optional[str] = None


class WorkflowState(BaseModel):
    """Extended state for workflow execution"""
    workflow_name: Optional[str] = None
    workflow_params: Dict[str, Any] = Field(default_factory=dict)
    current_node: Optional[str] = None
    completed_nodes: List[str] = Field(default_factory=list)
    node_outputs: Dict[str, str] = Field(default_factory=dict)
    workflow_history: List[WorkflowExecutionLog] = Field(default_factory=list)

    # Metadata for conditional routing
    sentiment_score: Optional[float] = None
    content_length: Optional[int] = None
    custom_metadata: Dict[str, Any] = Field(default_factory=dict)

    # Recursion tracking for nested workflows
    recursion_depth: int = Field(0, description="Current recursion depth for nested workflows")
    parent_workflow_stack: List[str] = Field(default_factory=list, description="Stack of parent workflow names")

    class Config:
        arbitrary_types_allowed = True
