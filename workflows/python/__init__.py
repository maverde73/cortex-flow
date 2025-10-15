"""
Python Workflow Definitions

This package contains workflow definitions written in Python instead of JSON.

Benefits of Python workflows:
- Type safety and IDE autocomplete
- Code reuse with helper functions
- Dynamic workflow generation
- Inline documentation
- Easier testing and validation

To create a new workflow:
1. Create a new .py file in this directory
2. Import the schema classes from schemas.workflow_schemas
3. Define your workflow as a WorkflowTemplate instance
4. Export it as a module-level variable named 'workflow'

Example:
    from schemas.workflow_schemas import WorkflowTemplate, WorkflowNode
    from workflows.python.helpers import llm_node

    workflow = WorkflowTemplate(
        name="my_workflow",
        description="My custom workflow",
        nodes=[
            llm_node("step1", "Do something"),
        ]
    )

The workflow will be automatically loaded by the registry on startup.
"""

__all__ = ['helpers']
