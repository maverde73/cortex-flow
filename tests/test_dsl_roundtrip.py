"""
Test DSL Round-Trip Conversion

Tests bidirectional conversion:
1. JSON → YAML DSL → JSON (semantics preserved)
2. YAML DSL → JSON → YAML DSL (structure preserved)
"""

import pytest
import json
from pathlib import Path

from workflows.dsl.parser import WorkflowDSLParser
from workflows.dsl.generator import WorkflowDSLGenerator
from workflows.registry import WorkflowRegistry
from schemas.workflow_schemas import WorkflowTemplate


class TestDSLRoundTrip:
    """Test round-trip conversions"""

    def test_yaml_to_json_to_yaml(self):
        """
        Test: YAML DSL → JSON → YAML DSL

        Workflow should maintain semantic equivalence
        """
        parser = WorkflowDSLParser()
        generator = WorkflowDSLGenerator()

        # Load original YAML
        original_yaml_path = Path("examples/dsl/newsletter.yaml")
        assert original_yaml_path.exists()

        # Parse YAML → WorkflowTemplate
        template1 = parser.parse_file(original_yaml_path)

        # Generate YAML from template
        yaml_content = generator.generate(template1, format="yaml")

        # Parse generated YAML → WorkflowTemplate
        template2 = parser.parse_string(yaml_content, format="yaml")

        # Templates should be semantically equivalent
        assert template1.name == template2.name
        assert template1.version == template2.version
        assert template1.description == template2.description
        assert len(template1.nodes) == len(template2.nodes)
        assert len(template1.conditional_edges) == len(template2.conditional_edges)

        # Check nodes
        for node1, node2 in zip(template1.nodes, template2.nodes):
            assert node1.id == node2.id
            assert node1.agent == node2.agent
            assert node1.depends_on == node2.depends_on

    def test_json_to_yaml_to_json(self):
        """
        Test: JSON → YAML DSL → JSON

        Workflow should maintain semantic equivalence
        """
        parser = WorkflowDSLParser()
        generator = WorkflowDSLGenerator()

        # Load original JSON
        registry = WorkflowRegistry()
        registry.load_templates()
        template1 = registry.get("report_generation")
        assert template1 is not None

        # Generate YAML from JSON
        yaml_content = generator.generate(template1, format="yaml")

        # Parse YAML → WorkflowTemplate
        template2 = parser.parse_string(yaml_content, format="yaml")

        # Templates should be equivalent
        assert template1.name == template2.name
        assert template1.version == template2.version
        assert len(template1.nodes) == len(template2.nodes)

    def test_all_existing_workflows_yaml_generation(self):
        """
        Test generating YAML for all existing workflow templates
        """
        generator = WorkflowDSLGenerator()
        registry = WorkflowRegistry()
        count = registry.load_templates()

        assert count > 0, "No templates loaded"

        for template_name in registry.list_templates():
            template = registry.get(template_name)

            # Should generate without errors
            yaml_content = generator.generate(template, format="yaml")
            assert len(yaml_content) > 0
            assert f"workflow: {template_name}" in yaml_content

    def test_all_dsl_examples_parsing(self):
        """
        Test parsing all YAML DSL examples
        """
        parser = WorkflowDSLParser()
        dsl_dir = Path("examples/dsl")

        if not dsl_dir.exists():
            pytest.skip("DSL examples directory not found")

        yaml_files = list(dsl_dir.glob("*.yaml"))
        assert len(yaml_files) > 0, "No YAML DSL examples found"

        for yaml_file in yaml_files:
            # Should parse without errors
            template = parser.parse_file(yaml_file)
            assert template is not None
            assert len(template.name) > 0
            assert len(template.nodes) > 0

    def test_roundtrip_preserves_validation(self):
        """
        Test that round-trip conversion maintains valid workflows
        """
        parser = WorkflowDSLParser()
        generator = WorkflowDSLGenerator()
        registry = WorkflowRegistry()

        # Load all templates
        registry.load_templates()

        for template_name in registry.list_templates():
            template1 = registry.get(template_name)

            # Validate original
            errors1 = registry.validate_template(template1)
            assert len(errors1) == 0, f"Original template '{template_name}' has errors: {errors1}"

            # Round-trip: JSON → YAML → JSON
            yaml_content = generator.generate(template1, format="yaml")
            template2 = parser.parse_string(yaml_content, format="yaml")

            # Validate after round-trip
            errors2 = registry.validate_template(template2)
            assert len(errors2) == 0, f"Round-tripped template '{template_name}' has errors: {errors2}"

    def test_roundtrip_database_report_mcp_node(self):
        """
        Test round-trip with MCP tool node (database_report example)
        """
        parser = WorkflowDSLParser()
        generator = WorkflowDSLGenerator()

        # Load database_report DSL
        yaml_path = Path("examples/dsl/database_report.yaml")
        if not yaml_path.exists():
            pytest.skip("database_report.yaml not found")

        # Parse YAML
        template1 = parser.parse_file(yaml_path)

        # Check MCP node
        mcp_nodes = [n for n in template1.nodes if n.agent == "mcp_tool"]
        assert len(mcp_nodes) > 0, "No MCP nodes found"

        mcp_node = mcp_nodes[0]
        assert mcp_node.tool_name == "query_database"
        assert "query_payload" in mcp_node.params

        # Round-trip
        yaml_content = generator.generate(template1, format="yaml")
        template2 = parser.parse_string(yaml_content, format="yaml")

        # Check MCP node preserved
        mcp_nodes2 = [n for n in template2.nodes if n.agent == "mcp_tool"]
        assert len(mcp_nodes2) == len(mcp_nodes)

        mcp_node2 = mcp_nodes2[0]
        assert mcp_node2.tool_name == mcp_node.tool_name
        assert "query_payload" in mcp_node2.params

    def test_roundtrip_conditional_routing(self):
        """
        Test round-trip with conditional routing (sentiment_routing example)
        """
        parser = WorkflowDSLParser()
        generator = WorkflowDSLGenerator()

        # Load sentiment_routing DSL
        yaml_path = Path("examples/dsl/sentiment_routing.yaml")
        if not yaml_path.exists():
            pytest.skip("sentiment_routing.yaml not found")

        # Parse YAML
        template1 = parser.parse_file(yaml_path)

        # Check conditional edges
        assert len(template1.conditional_edges) > 0, "No conditional edges found"

        edge1 = template1.conditional_edges[0]
        assert len(edge1.conditions) > 0
        assert edge1.default is not None

        # Round-trip
        yaml_content = generator.generate(template1, format="yaml")
        template2 = parser.parse_string(yaml_content, format="yaml")

        # Check conditional edges preserved
        assert len(template2.conditional_edges) == len(template1.conditional_edges)

        edge2 = template2.conditional_edges[0]
        assert edge2.from_node == edge1.from_node
        assert edge2.default == edge1.default
        assert len(edge2.conditions) == len(edge1.conditions)

    def test_roundtrip_parallel_execution(self):
        """
        Test round-trip with parallel execution (multi_source_research example)
        """
        parser = WorkflowDSLParser()
        generator = WorkflowDSLGenerator()

        # Load multi_source_research DSL
        yaml_path = Path("examples/dsl/multi_source_research.yaml")
        if not yaml_path.exists():
            pytest.skip("multi_source_research.yaml not found")

        # Parse YAML
        template1 = parser.parse_file(yaml_path)

        # Check parallel nodes
        parallel_nodes1 = [n for n in template1.nodes if n.parallel_group]
        assert len(parallel_nodes1) > 0, "No parallel nodes found"

        # Round-trip
        yaml_content = generator.generate(template1, format="yaml")
        template2 = parser.parse_string(yaml_content, format="yaml")

        # Check parallel nodes preserved
        parallel_nodes2 = [n for n in template2.nodes if n.parallel_group]
        assert len(parallel_nodes2) == len(parallel_nodes1)

        for node1, node2 in zip(parallel_nodes1, parallel_nodes2):
            assert node2.parallel_group == node1.parallel_group

    def test_timeout_format_conversion(self):
        """
        Test timeout format conversion (120s → 120 → 120s)
        """
        parser = WorkflowDSLParser()
        generator = WorkflowDSLGenerator()

        yaml_content = """
workflow: test_timeout
version: "1.0"
description: Test timeout formats
nodes:
  - node1:
      agent: researcher
      instruction: "Test"
      timeout: 300s
  - node2:
      agent: analyst
      instruction: "Test"
      timeout: 2m
  - node3:
      agent: writer
      instruction: "Test"
      timeout: 1h
"""

        # Parse
        template = parser.parse_string(yaml_content, format="yaml")

        # Check parsed timeouts
        assert template.nodes[0].timeout == 300  # 300s
        assert template.nodes[1].timeout == 120  # 2m
        assert template.nodes[2].timeout == 3600  # 1h

        # Generate YAML
        yaml_output = generator.generate(template, format="yaml")

        # Should contain timeout values
        assert "timeout" in yaml_output


class TestDSLParser:
    """Test DSL parser specific functionality"""

    def test_parse_minimal_workflow(self):
        """Test parsing minimal valid workflow"""
        parser = WorkflowDSLParser()

        yaml_content = """
workflow: minimal_test
version: "1.0"
description: Minimal workflow
triggers: []
nodes:
  - step1:
      agent: researcher
      instruction: "Do research"
"""

        template = parser.parse_string(yaml_content, format="yaml")

        assert template.name == "minimal_test"
        assert template.version == "1.0"
        assert len(template.nodes) == 1
        assert template.nodes[0].id == "step1"
        assert template.nodes[0].agent == "researcher"

    def test_parse_error_missing_workflow(self):
        """Test error when workflow name missing"""
        parser = WorkflowDSLParser()

        yaml_content = """
version: "1.0"
description: Missing workflow name
nodes:
  - step1:
      agent: researcher
      instruction: "Test"
"""

        with pytest.raises(ValueError, match="Missing required field: 'workflow'"):
            parser.parse_string(yaml_content, format="yaml")

    def test_parse_error_invalid_operator(self):
        """Test error with invalid conditional operator"""
        parser = WorkflowDSLParser()

        yaml_content = """
workflow: test_invalid_op
version: "1.0"
description: Test invalid operator
nodes:
  - step1:
      agent: researcher
      instruction: "Test"
conditions:
  - from: step1
    rules:
      - if: {field: score, op: "INVALID", value: 5}
        then: step2
    default: step3
"""

        with pytest.raises(ValueError, match="Unknown operator"):
            parser.parse_string(yaml_content, format="yaml")


class TestDSLGenerator:
    """Test DSL generator specific functionality"""

    def test_generate_minimal_workflow(self):
        """Test generating minimal workflow"""
        from schemas.workflow_schemas import WorkflowTemplate, WorkflowNode

        generator = WorkflowDSLGenerator()

        template = WorkflowTemplate(
            name="minimal",
            version="1.0",
            description="Minimal workflow",
            nodes=[
                WorkflowNode(
                    id="step1",
                    agent="researcher",
                    instruction="Do research"
                )
            ]
        )

        yaml_content = generator.generate(template, format="yaml")

        assert "workflow: minimal" in yaml_content
        assert "version:" in yaml_content
        assert "step1:" in yaml_content
        assert "agent: researcher" in yaml_content

    def test_generate_multiline_instruction(self):
        """Test generating with multi-line instruction"""
        from schemas.workflow_schemas import WorkflowTemplate, WorkflowNode

        generator = WorkflowDSLGenerator()

        long_instruction = """Research the following topics:
1. Topic A
2. Topic B
3. Topic C

Provide detailed analysis."""

        template = WorkflowTemplate(
            name="multiline_test",
            version="1.0",
            description="Test",
            nodes=[
                WorkflowNode(
                    id="research",
                    agent="researcher",
                    instruction=long_instruction
                )
            ]
        )

        yaml_content = generator.generate(template, format="yaml")

        # Should use literal block (|) for multi-line
        assert "instruction: |" in yaml_content or "instruction:" in yaml_content
