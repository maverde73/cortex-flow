"""
Workflow System for Cortex Flow

Enables predefined workflow templates with:
- Parallel execution
- Conditional routing
- MCP tool integration
- Fallback to ReAct
"""

from workflows.engine import WorkflowEngine
from workflows.registry import WorkflowRegistry
from workflows.conditions import ConditionEvaluator

__all__ = [
    "WorkflowEngine",
    "WorkflowRegistry",
    "ConditionEvaluator"
]
