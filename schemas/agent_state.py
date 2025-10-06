"""
State schemas for LangGraph agents.

These TypedDicts define the state structure that flows through
each agent's graph execution.
"""

from typing import TypedDict, Annotated, Sequence, List, Dict, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class BaseAgentState(TypedDict, total=False):
    """
    Base state structure shared by all agents.

    The messages list is the core of the ReAct pattern, containing:
    - HumanMessage: User input or task description
    - AIMessage: LLM responses (thoughts and action decisions)
    - ToolMessage: Results from tool executions (observations)

    ReAct metadata fields track execution progress and enable advanced control.
    """

    # Core message history (required)
    messages: Annotated[Sequence[BaseMessage], add_messages]

    # ReAct execution metadata (optional - for advanced control)
    iteration_count: int  # Number of Thought→Action→Observation cycles
    error_count: int  # Number of consecutive errors
    start_time: float  # Timestamp when execution started (time.time())

    # ReAct history for logging and debugging
    react_history: List[Dict]  # Structured log of each cycle
    # Each entry: {"iteration": 1, "thought": "...", "action": "...", "observation": "..."}

    # Control flags
    should_stop: bool  # Manual stop signal
    early_stop_reason: Optional[str]  # Reason for early termination

    # Human-in-the-Loop (HITL) - FASE 5
    pending_approval: Optional[Dict]  # Current approval request (if any)
    approval_decision: Optional[Dict]  # Human decision on approval
    hitl_enabled: bool  # HITL active for this task


class ResearcherState(BaseAgentState):
    """State for the Web Researcher agent."""
    pass  # Uses base state, can add specialized fields if needed


class RedditState(BaseAgentState):
    """State for the Reddit agent."""
    pass


class AnalystState(BaseAgentState):
    """
    State for the Analyst agent.

    May include additional fields for structured analysis output.
    """
    pass


class WriterState(BaseAgentState):
    """
    State for the Writer agent.

    May include fields for document structure, style preferences, etc.
    """
    pass


class SupervisorState(BaseAgentState):
    """
    State for the Supervisor agent.

    This agent orchestrates the workflow and delegates to other agents.
    """
    # Could add fields like:
    # - task_plan: List of steps to execute
    # - completed_steps: List of completed subtasks
    # - next_agent: Which agent to delegate to next
    pass
