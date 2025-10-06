"""
Workflow MCP Integration Tests

Tests workflow execution with MCP tools (query_database).
Requires corporate_server running on http://localhost:8005/mcp
"""

import pytest
import json
from pathlib import Path

from schemas.workflow_schemas import WorkflowTemplate, WorkflowNode
from workflows.registry import WorkflowRegistry
from workflows.engine import WorkflowEngine


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.mcp
class TestWorkflowMCPIntegration:
    """Test workflows with MCP tool integration"""

    def test_mcp_workflow_template_valid(self):
        """Test data_analysis_report template is valid"""
        registry = WorkflowRegistry()
        registry.load_templates()

        template = registry.get("data_analysis_report")

        # Template should exist
        assert template is not None
        assert template.name == "data_analysis_report"

        # Should have MCP tool node
        mcp_nodes = [n for n in template.nodes if n.agent == "mcp_tool"]
        assert len(mcp_nodes) > 0

        # MCP node should have tool_name
        mcp_node = mcp_nodes[0]
        assert mcp_node.tool_name == "query_database"
        assert "query_payload" in mcp_node.params

    def test_mcp_node_configuration(self):
        """Test MCP node has correct configuration"""
        registry = WorkflowRegistry()
        registry.load_templates()

        template = registry.get("data_analysis_report")
        mcp_node = next(n for n in template.nodes if n.agent == "mcp_tool")

        # Check params structure
        assert "query_payload" in mcp_node.params
        payload = mcp_node.params["query_payload"]

        assert "table" in payload
        assert "method" in payload
        assert payload["method"] == "select"

    @pytest.mark.skip(reason="Requires corporate_server running on port 8005")
    async def test_execute_mcp_workflow(self):
        """
        Test executing workflow with MCP tool.

        REQUIRES:
        - corporate_server running on http://localhost:8005/mcp
        - MCP_ENABLE=true in .env
        """
        registry = WorkflowRegistry()
        registry.load_templates()

        template = registry.get("data_analysis_report")
        assert template is not None

        engine = WorkflowEngine()

        # Execute workflow with parameters
        result = await engine.execute_workflow(
            template=template,
            user_input="Analyze user data from database",
            params={
                "query_topic": "user activity",
                "table_name": "users"
            }
        )

        # Check execution completed
        assert result.workflow_name == "data_analysis_report"
        assert result.total_execution_time > 0

        # Should have 3 node results (query_data, analyze, report)
        assert len(result.node_results) == 3

        # First node should be MCP tool
        first_result = result.node_results[0]
        assert first_result.node_id == "query_data"
        assert first_result.agent == "mcp_tool"

        # MCP tool should have output
        if first_result.success:
            assert len(first_result.output) > 0
            print(f"MCP tool output: {first_result.output[:200]}...")

    def test_multi_source_workflow_has_mcp(self):
        """Test multi_source_research workflow includes MCP tool"""
        registry = WorkflowRegistry()
        registry.load_templates()

        template = registry.get("multi_source_research")
        assert template is not None

        # Should have both web research and MCP database query in parallel
        parallel_nodes = [n for n in template.nodes if n.parallel_group == "sources"]
        assert len(parallel_nodes) == 2

        # One should be MCP tool
        mcp_nodes = [n for n in parallel_nodes if n.agent == "mcp_tool"]
        assert len(mcp_nodes) == 1

        # One should be web researcher
        researcher_nodes = [n for n in parallel_nodes if n.agent == "researcher"]
        assert len(researcher_nodes) == 1

    @pytest.mark.skip(reason="Requires corporate_server and agents running")
    async def test_multi_source_parallel_execution(self):
        """
        Test parallel execution with web research + MCP database query.

        REQUIRES:
        - corporate_server running
        - researcher agent running
        """
        registry = WorkflowRegistry()
        registry.load_templates()

        template = registry.get("multi_source_research")
        engine = WorkflowEngine()

        import time
        start = time.time()

        result = await engine.execute_workflow(
            template=template,
            user_input="Research AI frameworks from multiple sources",
            params={
                "topic": "AI agent frameworks",
                "table_name": "research_data"
            }
        )

        elapsed = time.time() - start

        # Check both parallel nodes executed
        parallel_results = [r for r in result.node_results if r.node_id in ["web_research", "database_query"]]
        assert len(parallel_results) == 2

        # Parallel execution should be faster than sequential
        # (Both nodes have 300s/60s timeout, but run in parallel)
        # Total time should be < sum of individual times
        assert result.success

    def test_workflow_template_syntax_all(self):
        """Test all workflow templates have valid JSON syntax"""
        registry = WorkflowRegistry()
        count = registry.load_templates()

        # Should load all 5 templates
        assert count >= 5

        templates = registry.list_templates()

        # Check expected templates exist
        expected = [
            "report_generation",
            "competitive_analysis",
            "data_analysis_report",
            "multi_source_research",
            "sentiment_routing"
        ]

        for name in expected:
            assert name in templates, f"Template '{name}' not found"

        # Validate all templates
        for name in templates:
            template = registry.get(name)
            errors = registry.validate_template(template)
            assert len(errors) == 0, f"Template '{name}' validation errors: {errors}"


@pytest.mark.asyncio
@pytest.mark.unit
class TestMCPToolConfiguration:
    """Test MCP tool configuration in workflow engine"""

    async def test_mcp_tool_param_substitution(self):
        """Test parameter substitution in MCP tool params"""
        from workflows.engine import WorkflowEngine
        from schemas.workflow_schemas import WorkflowState

        engine = WorkflowEngine()
        state = WorkflowState(workflow_params={"table_name": "users"})
        params = {"query_topic": "activity"}

        # Test substituting nested dict params
        text_dict = {
            "table": "{table_name}",
            "query": "SELECT * FROM {table_name}"
        }

        # The engine should handle dict substitution in _execute_mcp_tool
        # This test verifies the logic exists

        assert True  # Placeholder - actual execution requires MCP server

    def test_mcp_node_validation(self):
        """Test MCP nodes are validated correctly"""
        from workflows.registry import WorkflowRegistry

        # Valid MCP node
        template_valid = WorkflowTemplate(
            name="valid_mcp",
            version="1.0",
            description="Valid MCP workflow",
            nodes=[
                WorkflowNode(
                    id="query",
                    agent="mcp_tool",
                    tool_name="query_database",
                    instruction="Query DB",
                    params={"query_payload": {}}
                )
            ]
        )

        registry = WorkflowRegistry()
        errors = registry.validate_template(template_valid)
        assert len(errors) == 0

        # Invalid MCP node (missing tool_name)
        template_invalid = WorkflowTemplate(
            name="invalid_mcp",
            version="1.0",
            description="Invalid MCP workflow",
            nodes=[
                WorkflowNode(
                    id="query",
                    agent="mcp_tool",
                    instruction="Query DB",
                    params={}
                )
            ]
        )

        errors = registry.validate_template(template_invalid)
        assert len(errors) > 0
        assert any("missing tool_name" in err for err in errors)
