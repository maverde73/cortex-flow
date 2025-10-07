"""
Workflow DSL System

Bidirectional transformation between:
- YAML/Python DSL scripts ↔ WorkflowTemplate (JSON)

Components:
- parser.py: DSL → WorkflowTemplate
- generator.py: WorkflowTemplate → DSL
- validator.py: DSL validation and linting
"""

from workflows.dsl.parser import WorkflowDSLParser
from workflows.dsl.generator import WorkflowDSLGenerator

__all__ = [
    "WorkflowDSLParser",
    "WorkflowDSLGenerator",
]
