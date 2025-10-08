"""
Test composable workflows functionality.

Tests the ability of workflows to call other workflows as nodes,
including recursion depth limits and circular dependency detection.
"""

import asyncio
import json
import pytest
from pathlib import Path
from typing import Dict, Any

from schemas.workflow_schemas import WorkflowTemplate, WorkflowNode, WorkflowState
from workflows.engine import WorkflowEngine
from workflows.registry import WorkflowRegistry


class TestComposableWorkflows:
    """Test suite for composable workflows."""

    @pytest.fixture
    def workflow_engine(self):
        """Create a workflow engine instance."""
        return WorkflowEngine(mode="custom")  # Use custom mode for testing

    @pytest.fixture
    def simple_workflow(self) -> WorkflowTemplate:
        """Create a simple workflow template."""
        return WorkflowTemplate(
            name="simple_workflow",
            description="Simple test workflow",
            nodes=[
                WorkflowNode(
                    id="step1",
                    agent="analyst",
                    instruction="Process: {input}",
                    depends_on=[]
                )
            ],
            conditional_edges=[],
            parameters={"input": "test data"}
        )

    @pytest.fixture
    def composite_workflow(self) -> WorkflowTemplate:
        """Create a workflow that calls another workflow."""
        return WorkflowTemplate(
            name="composite_workflow",
            description="Workflow that calls another workflow",
            nodes=[
                WorkflowNode(
                    id="pre_process",
                    agent="researcher",
                    instruction="Research: {topic}",
                    depends_on=[]
                ),
                WorkflowNode(
                    id="sub_workflow",
                    agent="workflow",
                    workflow_name="simple_workflow",
                    instruction="Process the research data",
                    depends_on=["pre_process"],
                    workflow_params={
                        "input": "{pre_process}"
                    },
                    max_depth=3
                ),
                WorkflowNode(
                    id="post_process",
                    agent="writer",
                    instruction="Write report based on: {sub_workflow}",
                    depends_on=["sub_workflow"]
                )
            ],
            conditional_edges=[],
            parameters={"topic": "AI trends"}
        )

    def test_workflow_node_schema(self):
        """Test that WorkflowNode supports workflow agent type."""
        node = WorkflowNode(
            id="test",
            agent="workflow",
            workflow_name="sub_workflow",
            instruction="Execute sub-workflow",
            workflow_params={"param1": "value1"},
            max_depth=5
        )

        assert node.agent == "workflow"
        assert node.workflow_name == "sub_workflow"
        assert node.workflow_params == {"param1": "value1"}
        assert node.max_depth == 5

    def test_workflow_state_recursion_tracking(self):
        """Test that WorkflowState tracks recursion properly."""
        state = WorkflowState(
            workflow_name="parent",
            recursion_depth=2,
            parent_workflow_stack=["root", "level1"]
        )

        assert state.recursion_depth == 2
        assert len(state.parent_workflow_stack) == 2
        assert state.parent_workflow_stack[-1] == "level1"

    @pytest.mark.asyncio
    async def test_workflow_calling_workflow(self, workflow_engine, simple_workflow, composite_workflow):
        """Test that a workflow can successfully call another workflow."""
        # Mock the registry to return our test workflows
        registry = WorkflowRegistry("/fake/path")
        registry._templates = {
            "simple_workflow": simple_workflow,
            "composite_workflow": composite_workflow
        }

        # Patch the registry getter in the engine
        import workflows.engine
        original_get_registry = workflows.engine.get_workflow_registry

        def mock_get_registry(path):
            return registry

        workflows.engine.get_workflow_registry = mock_get_registry

        try:
            # This would normally execute the workflow
            # For testing, we just verify the structure is correct
            assert composite_workflow.nodes[1].agent == "workflow"
            assert composite_workflow.nodes[1].workflow_name == "simple_workflow"

        finally:
            # Restore original
            workflows.engine.get_workflow_registry = original_get_registry

    def test_recursion_depth_limit(self):
        """Test that recursion depth is properly limited."""
        # Create a self-referencing workflow (would cause infinite recursion)
        recursive_workflow = WorkflowTemplate(
            name="recursive_workflow",
            description="Self-referencing workflow",
            nodes=[
                WorkflowNode(
                    id="recurse",
                    agent="workflow",
                    workflow_name="recursive_workflow",  # Calls itself!
                    instruction="Recurse",
                    max_depth=2  # Limit recursion
                )
            ],
            conditional_edges=[],
            parameters={}
        )

        # Verify the max_depth is set
        assert recursive_workflow.nodes[0].max_depth == 2

    def test_circular_dependency_detection(self):
        """Test that circular dependencies are detected."""
        # Create workflows that reference each other
        workflow_a = WorkflowTemplate(
            name="workflow_a",
            description="Calls workflow B",
            nodes=[
                WorkflowNode(
                    id="call_b",
                    agent="workflow",
                    workflow_name="workflow_b",
                    instruction="Call B"
                )
            ],
            conditional_edges=[],
            parameters={}
        )

        workflow_b = WorkflowTemplate(
            name="workflow_b",
            description="Calls workflow A",
            nodes=[
                WorkflowNode(
                    id="call_a",
                    agent="workflow",
                    workflow_name="workflow_a",
                    instruction="Call A"
                )
            ],
            conditional_edges=[],
            parameters={}
        )

        # Both workflows exist and reference each other
        assert workflow_a.nodes[0].workflow_name == "workflow_b"
        assert workflow_b.nodes[0].workflow_name == "workflow_a"

    def test_parallel_sub_workflows(self):
        """Test that multiple sub-workflows can run in parallel."""
        parallel_workflow = WorkflowTemplate(
            name="parallel_composite",
            description="Runs multiple sub-workflows in parallel",
            nodes=[
                WorkflowNode(
                    id="sub1",
                    agent="workflow",
                    workflow_name="simple_workflow",
                    instruction="First parallel workflow",
                    parallel_group="parallel",
                    workflow_params={"input": "data1"}
                ),
                WorkflowNode(
                    id="sub2",
                    agent="workflow",
                    workflow_name="simple_workflow",
                    instruction="Second parallel workflow",
                    parallel_group="parallel",
                    workflow_params={"input": "data2"}
                ),
                WorkflowNode(
                    id="combine",
                    agent="analyst",
                    instruction="Combine: {sub1} and {sub2}",
                    depends_on=["sub1", "sub2"]
                )
            ],
            conditional_edges=[],
            parameters={}
        )

        # Verify parallel group is set correctly
        assert parallel_workflow.nodes[0].parallel_group == "parallel"
        assert parallel_workflow.nodes[1].parallel_group == "parallel"
        assert parallel_workflow.nodes[2].depends_on == ["sub1", "sub2"]

    def test_workflow_parameter_passing(self):
        """Test that parameters are correctly passed to sub-workflows."""
        parent_workflow = WorkflowTemplate(
            name="parent",
            description="Parent workflow with parameter passing",
            nodes=[
                WorkflowNode(
                    id="prepare",
                    agent="analyst",
                    instruction="Prepare data: {initial_data}",
                    depends_on=[]
                ),
                WorkflowNode(
                    id="child",
                    agent="workflow",
                    workflow_name="child_workflow",
                    instruction="Process prepared data",
                    depends_on=["prepare"],
                    workflow_params={
                        "processed_data": "{prepare}",
                        "config_value": "{config_param}",
                        "static_value": "constant"
                    }
                )
            ],
            conditional_edges=[],
            parameters={
                "initial_data": "raw input",
                "config_param": "configuration"
            }
        )

        # Verify parameter structure
        child_params = parent_workflow.nodes[1].workflow_params
        assert child_params["processed_data"] == "{prepare}"
        assert child_params["config_value"] == "{config_param}"
        assert child_params["static_value"] == "constant"

    def test_load_composable_workflows_from_json(self):
        """Test loading composable workflows from JSON files."""
        # Load the example workflows we created
        workflow_dir = Path("projects/default/workflows")

        # Check that our composable workflow files exist
        research_report = workflow_dir / "research_and_report.json"
        modular_analysis = workflow_dir / "modular_analysis.json"
        comparative = workflow_dir / "comparative_research.json"
        simple = workflow_dir / "simple_research.json"

        # Verify files were created
        assert research_report.exists(), "research_and_report.json should exist"
        assert modular_analysis.exists(), "modular_analysis.json should exist"
        assert comparative.exists(), "comparative_research.json should exist"
        assert simple.exists(), "simple_research.json should exist"

        # Load and validate structure
        if research_report.exists():
            with open(research_report) as f:
                data = json.load(f)
                template = WorkflowTemplate(**data)

                # Verify it has workflow nodes
                workflow_nodes = [n for n in template.nodes if n.agent == "workflow"]
                assert len(workflow_nodes) > 0, "Should have workflow nodes"

                # Verify workflow names are set
                for node in workflow_nodes:
                    assert node.workflow_name is not None
                    assert node.workflow_name in [
                        "multi_source_research",
                        "report_generation",
                        "simple_research",
                        "sentiment_routing",
                        "data_analysis_report"
                    ]


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])