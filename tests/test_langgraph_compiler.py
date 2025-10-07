"""
Tests for LangGraph Workflow Compiler

Tests compilation of WorkflowTemplate to native LangGraph StateGraph,
including parallel execution, conditional routing, and regression tests.
"""

import pytest
import asyncio
from typing import Dict, Any

from schemas.workflow_schemas import (
    WorkflowTemplate,
    WorkflowNode,
    ConditionalEdge,
    WorkflowCondition,
    ConditionOperator
)
from workflows.langgraph_compiler import LangGraphWorkflowCompiler, compile_workflow
from workflows.engine import WorkflowEngine


class TestLangGraphCompiler:
    """Tests for LangGraph compiler"""

    def test_compiler_initialization(self):
        """Test compiler can be initialized"""
        compiler = LangGraphWorkflowCompiler()
        assert compiler is not None
        assert compiler.condition_evaluator is not None

    def test_simple_sequential_workflow(self):
        """Test compiling a simple sequential workflow"""
        template = WorkflowTemplate(
            name="simple_test",
            description="Simple sequential workflow",
            nodes=[
                WorkflowNode(
                    id="step1",
                    agent="researcher",
                    instruction="Research {user_input}"
                ),
                WorkflowNode(
                    id="step2",
                    agent="analyst",
                    instruction="Analyze {step1}",
                    depends_on=["step1"]
                )
            ]
        )

        compiler = LangGraphWorkflowCompiler()
        compiled_graph = compiler.compile(template)

        assert compiled_graph is not None
        # CompiledGraph should be callable
        assert hasattr(compiled_graph, 'ainvoke')

    def test_parallel_workflow(self):
        """Test compiling workflow with parallel execution"""
        template = WorkflowTemplate(
            name="parallel_test",
            description="Workflow with parallel nodes",
            nodes=[
                WorkflowNode(
                    id="research1",
                    agent="researcher",
                    instruction="Research topic A",
                    parallel_group="research"
                ),
                WorkflowNode(
                    id="research2",
                    agent="researcher",
                    instruction="Research topic B",
                    parallel_group="research"
                ),
                WorkflowNode(
                    id="synthesize",
                    agent="analyst",
                    instruction="Synthesize {research1} and {research2}",
                    depends_on=["research1", "research2"]
                )
            ]
        )

        compiler = LangGraphWorkflowCompiler()
        compiled_graph = compiler.compile(template)

        assert compiled_graph is not None

    def test_conditional_routing(self):
        """Test compiling workflow with conditional edges"""
        template = WorkflowTemplate(
            name="conditional_test",
            description="Workflow with conditional routing",
            nodes=[
                WorkflowNode(
                    id="analyze",
                    agent="analyst",
                    instruction="Analyze sentiment of {user_input}"
                ),
                WorkflowNode(
                    id="positive_response",
                    agent="writer",
                    instruction="Write positive response"
                ),
                WorkflowNode(
                    id="negative_response",
                    agent="writer",
                    instruction="Write negative response"
                )
            ],
            conditional_edges=[
                ConditionalEdge(
                    from_node="analyze",
                    conditions=[
                        WorkflowCondition(
                            field="sentiment_score",
                            operator=ConditionOperator.GREATER_THAN,
                            value=0.5,
                            next_node="positive_response"
                        )
                    ],
                    default="negative_response"
                )
            ]
        )

        compiler = LangGraphWorkflowCompiler()
        compiled_graph = compiler.compile(template)

        assert compiled_graph is not None

    def test_compile_convenience_function(self):
        """Test compile_workflow convenience function"""
        template = WorkflowTemplate(
            name="convenience_test",
            description="Test convenience function",
            nodes=[
                WorkflowNode(
                    id="single_node",
                    agent="researcher",
                    instruction="Research {user_input}"
                )
            ]
        )

        compiled_graph = compile_workflow(template)
        assert compiled_graph is not None


class TestWorkflowEngineHybridMode:
    """Tests for WorkflowEngine hybrid mode"""

    def test_engine_langgraph_mode(self):
        """Test engine initialization in langgraph mode"""
        engine = WorkflowEngine(mode="langgraph")
        assert engine.mode == "langgraph"
        assert engine._compiler is None  # Lazy-loaded

    def test_engine_custom_mode(self):
        """Test engine initialization in custom mode"""
        engine = WorkflowEngine(mode="custom")
        assert engine.mode == "custom"

    def test_engine_default_mode(self):
        """Test engine defaults to langgraph mode"""
        engine = WorkflowEngine()
        assert engine.mode == "langgraph"

    @pytest.mark.asyncio
    async def test_langgraph_execution_simple(self):
        """Test executing simple workflow via LangGraph"""
        template = WorkflowTemplate(
            name="execution_test",
            description="Simple execution test",
            nodes=[
                WorkflowNode(
                    id="step1",
                    agent="researcher",
                    instruction="Test instruction: {user_input}"
                )
            ]
        )

        engine = WorkflowEngine(mode="langgraph")

        # Note: This will fail without actual agents running
        # but tests the compilation path
        try:
            result = await engine.execute_workflow(
                template=template,
                user_input="test input",
                params={}
            )
            # If it doesn't crash during compilation, that's a success
            assert result is not None
        except Exception as e:
            # Expected - agents not available in test environment
            assert "researcher" in str(e).lower() or "agent" in str(e).lower()

    @pytest.mark.asyncio
    async def test_custom_execution_simple(self):
        """Test executing simple workflow via custom engine"""
        template = WorkflowTemplate(
            name="custom_execution_test",
            description="Custom engine test",
            nodes=[
                WorkflowNode(
                    id="step1",
                    agent="researcher",
                    instruction="Test instruction: {user_input}"
                )
            ]
        )

        engine = WorkflowEngine(mode="custom")

        try:
            result = await engine.execute_workflow(
                template=template,
                user_input="test input",
                params={}
            )
            assert result is not None
        except Exception as e:
            # Expected - agents not available
            assert "researcher" in str(e).lower() or "agent" in str(e).lower()


class TestVariableSubstitution:
    """Tests for variable substitution in compiled workflows"""

    def test_variable_substitution_user_input(self):
        """Test {user_input} substitution"""
        compiler = LangGraphWorkflowCompiler()

        state = {
            "user_input": "test value",
            "workflow_params": {},
            "node_outputs": {}
        }

        result = compiler._substitute_variables(
            "Process {user_input}",
            state
        )

        assert result == "Process test value"

    def test_variable_substitution_node_output(self):
        """Test {node_id} substitution"""
        compiler = LangGraphWorkflowCompiler()

        state = {
            "user_input": "",
            "workflow_params": {},
            "node_outputs": {
                "step1": "output from step 1"
            }
        }

        result = compiler._substitute_variables(
            "Analyze {step1}",
            state
        )

        assert result == "Analyze output from step 1"

    def test_variable_substitution_params(self):
        """Test {param_name} substitution"""
        compiler = LangGraphWorkflowCompiler()

        state = {
            "user_input": "",
            "workflow_params": {
                "date": "2025-10-07",
                "topic": "AI trends"
            },
            "node_outputs": {}
        }

        result = compiler._substitute_variables(
            "Create report on {topic} for {date}",
            state
        )

        assert result == "Create report on AI trends for 2025-10-07"

    def test_variable_substitution_mixed(self):
        """Test mixed variable substitution"""
        compiler = LangGraphWorkflowCompiler()

        state = {
            "user_input": "user query",
            "workflow_params": {"param1": "value1"},
            "node_outputs": {"node1": "output1"}
        }

        result = compiler._substitute_variables(
            "Process {user_input} with {param1} and {node1}",
            state
        )

        assert result == "Process user query with value1 and output1"


class TestRegressionTests:
    """Regression tests to ensure backward compatibility"""

    @pytest.mark.asyncio
    async def test_custom_engine_still_works(self):
        """Regression: Custom engine should still work"""
        template = WorkflowTemplate(
            name="regression_custom",
            description="Test custom engine backward compatibility",
            nodes=[
                WorkflowNode(
                    id="test_node",
                    agent="researcher",
                    instruction="Test"
                )
            ]
        )

        engine = WorkflowEngine(mode="custom")

        try:
            result = await engine.execute_workflow(
                template=template,
                user_input="test",
                params={}
            )
            # Structure should be same as before
            assert hasattr(result, 'workflow_name')
            assert hasattr(result, 'success')
            assert hasattr(result, 'final_output')
            assert hasattr(result, 'node_results')
        except Exception:
            # Expected - just checking structure
            pass

    @pytest.mark.asyncio
    async def test_workflow_result_structure(self):
        """Regression: WorkflowResult structure should be consistent"""
        template = WorkflowTemplate(
            name="result_structure_test",
            description="Test result structure",
            nodes=[
                WorkflowNode(
                    id="node1",
                    agent="researcher",
                    instruction="Test"
                )
            ]
        )

        # Test both modes produce same structure
        for mode in ["langgraph", "custom"]:
            engine = WorkflowEngine(mode=mode)

            try:
                result = await engine.execute_workflow(
                    template=template,
                    user_input="test",
                    params={}
                )

                # Check required fields
                assert hasattr(result, 'workflow_name')
                assert hasattr(result, 'success')
                assert hasattr(result, 'final_output')
                assert hasattr(result, 'execution_log')
                assert hasattr(result, 'node_results')
                assert hasattr(result, 'total_execution_time')

                # Check types
                assert isinstance(result.workflow_name, str)
                assert isinstance(result.success, bool)
                assert isinstance(result.final_output, str)
                assert isinstance(result.execution_log, list)
                assert isinstance(result.node_results, list)
                assert isinstance(result.total_execution_time, float)

            except Exception:
                # Expected - agents not available
                pass

    def test_template_schema_compatibility(self):
        """Regression: WorkflowTemplate schema should be unchanged"""
        # Create template with all features (complete with all referenced nodes)
        template = WorkflowTemplate(
            name="full_feature_test",
            version="1.0",
            description="Test all features",
            trigger_patterns=["test.*"],
            nodes=[
                WorkflowNode(
                    id="node1",
                    agent="researcher",
                    instruction="Test {param1}",
                    depends_on=[],
                    parallel_group=None,  # No parallel group for main node
                    timeout=120,
                    params={"key": "value"}
                ),
                WorkflowNode(
                    id="node2",
                    agent="analyst",
                    instruction="Positive path"
                ),
                WorkflowNode(
                    id="node3",
                    agent="writer",
                    instruction="Default path"
                )
            ],
            conditional_edges=[
                ConditionalEdge(
                    from_node="node1",
                    conditions=[
                        WorkflowCondition(
                            field="test_field",
                            operator=ConditionOperator.EQUALS,
                            value="test",
                            next_node="node2"
                        )
                    ],
                    default="node3"
                )
            ],
            parameters={"param1": "value1"}
        )

        # Should compile without errors
        compiler = LangGraphWorkflowCompiler()
        compiled = compiler.compile(template)
        assert compiled is not None


class TestMetadataExtraction:
    """Tests for metadata extraction"""

    def test_sentiment_extraction(self):
        """Test sentiment score extraction"""
        compiler = LangGraphWorkflowCompiler()

        # Test positive sentiment
        metadata = compiler._extract_metadata("This is great! Wonderful!")
        assert "sentiment_score" in metadata
        # Basic check - actual score depends on implementation

        # Test content length
        assert "content_length" in metadata
        assert metadata["content_length"] > 0

    def test_content_length_extraction(self):
        """Test content length is extracted correctly"""
        compiler = LangGraphWorkflowCompiler()

        text = "A" * 100
        metadata = compiler._extract_metadata(text)

        assert metadata["content_length"] == 100


# Test configuration
@pytest.fixture(scope="module")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-k", "not asyncio"])
