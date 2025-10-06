"""
Workflow System Tests

Tests for workflow templates, engine, registry, and conditional routing.
"""

import pytest
import json
from pathlib import Path

from schemas.workflow_schemas import (
    WorkflowTemplate,
    WorkflowNode,
    ConditionalEdge,
    WorkflowCondition,
    ConditionOperator,
    WorkflowState
)
from workflows.registry import WorkflowRegistry
from workflows.conditions import ConditionEvaluator, extract_sentiment_score
from workflows.engine import WorkflowEngine


# ============================================================================
# REGISTRY TESTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.unit
class TestWorkflowRegistry:
    """Test workflow registry functionality"""

    def test_registry_initialization(self):
        """Test registry initializes correctly"""
        registry = WorkflowRegistry()
        assert registry.templates_dir.name == "templates"
        assert registry._loaded == False

    def test_load_templates_from_directory(self, tmp_path):
        """Test loading templates from JSON files"""
        # Create test template
        template_data = {
            "name": "test_workflow",
            "version": "1.0",
            "description": "Test workflow",
            "trigger_patterns": ["test.*"],
            "nodes": [
                {
                    "id": "node1",
                    "agent": "researcher",
                    "instruction": "Test instruction",
                    "depends_on": []
                }
            ]
        }

        template_file = tmp_path / "test_workflow.json"
        with open(template_file, 'w') as f:
            json.dump(template_data, f)

        registry = WorkflowRegistry(str(tmp_path))
        count = registry.load_templates()

        assert count == 1
        assert "test_workflow" in registry.list_templates()

    def test_validate_template_valid(self):
        """Test template validation accepts valid template"""
        template = WorkflowTemplate(
            name="valid",
            version="1.0",
            description="Valid template",
            nodes=[
                WorkflowNode(
                    id="node1",
                    agent="researcher",
                    instruction="Test"
                )
            ]
        )

        registry = WorkflowRegistry()
        errors = registry.validate_template(template)

        assert len(errors) == 0

    def test_validate_template_duplicate_nodes(self):
        """Test validation detects duplicate node IDs"""
        template = WorkflowTemplate(
            name="invalid",
            version="1.0",
            description="Invalid template",
            nodes=[
                WorkflowNode(id="node1", agent="researcher", instruction="Test 1"),
                WorkflowNode(id="node1", agent="analyst", instruction="Test 2")
            ]
        )

        registry = WorkflowRegistry()
        errors = registry.validate_template(template)

        assert len(errors) > 0
        assert any("Duplicate node IDs" in err for err in errors)

    def test_validate_template_missing_dependency(self):
        """Test validation detects missing dependencies"""
        template = WorkflowTemplate(
            name="invalid",
            version="1.0",
            description="Invalid template",
            nodes=[
                WorkflowNode(
                    id="node1",
                    agent="researcher",
                    instruction="Test",
                    depends_on=["nonexistent"]
                )
            ]
        )

        registry = WorkflowRegistry()
        errors = registry.validate_template(template)

        assert len(errors) > 0
        assert any("non-existent node" in err for err in errors)

    @pytest.mark.asyncio
    async def test_auto_match_template(self, tmp_path):
        """Test auto-matching template from user input"""
        template_data = {
            "name": "report",
            "version": "1.0",
            "description": "Report generation",
            "trigger_patterns": [".*report.*", "create.*document.*"],
            "nodes": [{"id": "n1", "agent": "researcher", "instruction": "test"}]
        }

        template_file = tmp_path / "report.json"
        with open(template_file, 'w') as f:
            json.dump(template_data, f)

        registry = WorkflowRegistry(str(tmp_path))
        registry.load_templates()

        # Should match
        matched = await registry.match_template("Please create a report on AI")
        assert matched is not None
        assert matched.name == "report"

        # Should not match
        not_matched = await registry.match_template("What is the weather?")
        assert not_matched is None


# ============================================================================
# CONDITIONAL ROUTING TESTS
# ============================================================================

@pytest.mark.unit
class TestConditionalRouting:
    """Test conditional routing logic"""

    def test_evaluate_greater_than(self):
        """Test > operator"""
        evaluator = ConditionEvaluator()
        state = WorkflowState(sentiment_score=0.8)

        condition = WorkflowCondition(
            field="sentiment_score",
            operator=ConditionOperator.GREATER_THAN,
            value=0.7,
            next_node="positive"
        )

        edge = ConditionalEdge(
            from_node="analyze",
            conditions=[condition],
            default="neutral"
        )

        next_node = evaluator.evaluate_edge(edge, state)
        assert next_node == "positive"

    def test_evaluate_less_than(self):
        """Test < operator"""
        evaluator = ConditionEvaluator()
        state = WorkflowState(sentiment_score=0.2)

        condition = WorkflowCondition(
            field="sentiment_score",
            operator=ConditionOperator.LESS_THAN,
            value=0.3,
            next_node="negative"
        )

        edge = ConditionalEdge(
            from_node="analyze",
            conditions=[condition],
            default="neutral"
        )

        next_node = evaluator.evaluate_edge(edge, state)
        assert next_node == "negative"

    def test_evaluate_contains(self):
        """Test contains operator"""
        evaluator = ConditionEvaluator()
        state = WorkflowState(
            node_outputs={"analyze": "This is a great success!"}
        )

        # Use nested field access
        state.custom_metadata = {"text": "This is a great success!"}

        condition = WorkflowCondition(
            field="custom_metadata.text",
            operator=ConditionOperator.CONTAINS,
            value="success",
            next_node="positive"
        )

        edge = ConditionalEdge(
            from_node="analyze",
            conditions=[condition],
            default="neutral"
        )

        next_node = evaluator.evaluate_edge(edge, state)
        assert next_node == "positive"

    def test_evaluate_default_fallback(self):
        """Test fallback to default when no condition matches"""
        evaluator = ConditionEvaluator()
        state = WorkflowState(sentiment_score=0.5)

        condition1 = WorkflowCondition(
            field="sentiment_score",
            operator=ConditionOperator.GREATER_THAN,
            value=0.7,
            next_node="positive"
        )

        condition2 = WorkflowCondition(
            field="sentiment_score",
            operator=ConditionOperator.LESS_THAN,
            value=0.3,
            next_node="negative"
        )

        edge = ConditionalEdge(
            from_node="analyze",
            conditions=[condition1, condition2],
            default="neutral"
        )

        next_node = evaluator.evaluate_edge(edge, state)
        assert next_node == "neutral"

    def test_sentiment_extraction(self):
        """Test sentiment score extraction"""
        positive_text = "This is great, excellent work with strong benefits"
        negative_text = "This is bad, poor performance with major risks"
        neutral_text = "This is a normal situation"

        pos_score = extract_sentiment_score(positive_text)
        neg_score = extract_sentiment_score(negative_text)
        neu_score = extract_sentiment_score(neutral_text)

        assert pos_score > 0.5
        assert neg_score < 0.5
        assert neu_score == 0.5


# ============================================================================
# WORKFLOW ENGINE TESTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.unit
class TestWorkflowEngine:
    """Test workflow execution engine"""

    def test_build_execution_plan_sequential(self):
        """Test building execution plan for sequential nodes"""
        template = WorkflowTemplate(
            name="sequential",
            version="1.0",
            description="Sequential workflow",
            nodes=[
                WorkflowNode(id="n1", agent="researcher", instruction="Step 1"),
                WorkflowNode(id="n2", agent="analyst", instruction="Step 2", depends_on=["n1"]),
                WorkflowNode(id="n3", agent="writer", instruction="Step 3", depends_on=["n2"])
            ]
        )

        engine = WorkflowEngine()
        plan = engine._build_execution_plan(template)

        assert len(plan) == 3
        assert all(step["type"] == "sequential" for step in plan)

    def test_build_execution_plan_parallel(self):
        """Test building execution plan with parallel nodes"""
        template = WorkflowTemplate(
            name="parallel",
            version="1.0",
            description="Parallel workflow",
            nodes=[
                WorkflowNode(
                    id="n1",
                    agent="researcher",
                    instruction="Research A",
                    parallel_group="research"
                ),
                WorkflowNode(
                    id="n2",
                    agent="researcher",
                    instruction="Research B",
                    parallel_group="research"
                )
            ]
        )

        engine = WorkflowEngine()
        plan = engine._build_execution_plan(template)

        assert len(plan) == 1
        assert plan[0]["type"] == "parallel"
        assert len(plan[0]["nodes"]) == 2

    def test_substitute_variables(self):
        """Test variable substitution in instructions"""
        engine = WorkflowEngine()
        state = WorkflowState(
            node_outputs={"research": "AI is growing"},
            workflow_params={"topic": "AI trends"}
        )

        params = {"topic": "AI trends", "year": "2025"}

        text = "Analyze {research} for {topic} in {year}"
        result = engine._substitute_variables(text, state, params)

        assert result == "Analyze AI is growing for AI trends in 2025"


# ============================================================================
# INTEGRATION TEST
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
class TestWorkflowIntegration:
    """Integration tests for complete workflow execution"""

    @pytest.mark.skip(reason="Requires running agents")
    async def test_simple_workflow_execution(self):
        """Test executing a simple workflow (requires agents running)"""
        template = WorkflowTemplate(
            name="simple_test",
            version="1.0",
            description="Simple test workflow",
            nodes=[
                WorkflowNode(
                    id="research",
                    agent="researcher",
                    instruction="Research {topic}",
                    timeout=60
                )
            ]
        )

        engine = WorkflowEngine()
        result = await engine.execute_workflow(
            template=template,
            user_input="Tell me about LangGraph",
            params={"topic": "LangGraph"}
        )

        # Note: This will fail if agents not running
        # Just checking the structure
        assert result.workflow_name == "simple_test"
        assert result.total_execution_time > 0
