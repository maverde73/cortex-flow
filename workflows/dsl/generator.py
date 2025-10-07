"""
Workflow DSL Generator

Converts WorkflowTemplate (JSON) to YAML/Python DSL scripts.

Example:
    generator = WorkflowDSLGenerator()
    yaml_content = generator.generate(template, format="yaml")
    generator.generate_file(template, "output.yaml")
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List
from io import StringIO

from schemas.workflow_schemas import (
    WorkflowTemplate,
    WorkflowNode,
    ConditionalEdge,
    ConditionOperator
)

logger = logging.getLogger(__name__)


# Custom YAML types
class LiteralString(str):
    """String that will be dumped as YAML literal block (|)"""
    pass


def literal_presenter(dumper, data):
    """Present long strings as literal blocks"""
    if '\n' in data or len(data) > 60:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)


yaml.add_representer(LiteralString, literal_presenter)


class WorkflowDSLGenerator:
    """Generate DSL scripts from WorkflowTemplate"""

    def __init__(self):
        self.supported_formats = ["yaml", "python"]

    def generate(
        self,
        template: WorkflowTemplate,
        format: str = "yaml"
    ) -> str:
        """
        Generate DSL script from WorkflowTemplate.

        Args:
            template: WorkflowTemplate to convert
            format: Output format ("yaml", "python")

        Returns:
            DSL script as string
        """
        if format not in self.supported_formats:
            raise ValueError(
                f"Unsupported format: {format}. "
                f"Supported: {self.supported_formats}"
            )

        logger.info(f"Generating {format.upper()} DSL for workflow '{template.name}'")

        if format == "yaml":
            return self._generate_yaml(template)
        elif format == "python":
            return self._generate_python(template)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def generate_file(
        self,
        template: WorkflowTemplate,
        output_path: str | Path,
        format: str = "yaml"
    ):
        """
        Generate DSL file from WorkflowTemplate.

        Args:
            template: WorkflowTemplate to convert
            output_path: Output file path
            format: Output format (auto-detected from extension if not specified)
        """
        output_path = Path(output_path)

        # Auto-detect format from extension
        if output_path.suffix in [".yaml", ".yml"]:
            format = "yaml"
        elif output_path.suffix == ".py":
            format = "python"

        content = self.generate(template, format=format)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"Generated DSL file: {output_path}")

    def _generate_yaml(self, template: WorkflowTemplate) -> str:
        """
        Generate YAML DSL from WorkflowTemplate.

        Output structure:
        workflow: name
        version: "1.0"
        description: |
          Multi-line description
        triggers:
          - "pattern1"
          - "pattern2"
        params:
          key: value
        nodes:
          - node_id:
              agent: researcher
              instruction: |
                Multi-line instruction
              depends_on: [other_node]
              timeout: 120
        conditions:
          - from: node1
            rules:
              - if: {field: sentiment_score, op: ">", value: 0.5}
                then: positive
            default: neutral
        """
        data = {
            "workflow": template.name,
            "version": template.version,
            "description": template.description,
        }

        # Add trigger patterns
        if template.trigger_patterns:
            data["triggers"] = template.trigger_patterns

        # Add parameters
        if template.parameters:
            data["params"] = template.parameters

        # Add nodes
        data["nodes"] = self._nodes_to_yaml(template.nodes)

        # Add conditional edges
        if template.conditional_edges:
            data["conditions"] = self._conditions_to_yaml(template.conditional_edges)

        # Use custom YAML dumper for better formatting
        return self._dump_yaml_custom(data)

    def _nodes_to_yaml(self, nodes: List[WorkflowNode]) -> List[Dict]:
        """
        Convert nodes to YAML-friendly structure.

        Format:
        - node_id:
            agent: researcher
            instruction: "..."
            depends_on: [...]
            parallel_group: "group1"
            timeout: 120
            tool_name: "query_database"
            params: {...}
        """
        nodes_list = []

        for node in nodes:
            node_dict = {
                "agent": node.agent,
            }

            # Add instruction (use literal block for multi-line)
            if node.instruction:
                node_dict["instruction"] = node.instruction

            # Add optional fields only if set
            if node.depends_on:
                node_dict["depends_on"] = node.depends_on

            if node.parallel_group:
                node_dict["parallel_group"] = node.parallel_group

            if node.timeout != 120:  # Only if non-default
                node_dict["timeout"] = f"{node.timeout}s"

            if node.tool_name:
                node_dict["tool_name"] = node.tool_name

            if node.params:
                node_dict["params"] = node.params

            if node.template:
                node_dict["template"] = node.template

            if node.use_mcp_prompt:
                node_dict["use_mcp_prompt"] = True

            # Wrap in dict with node ID as key
            nodes_list.append({node.id: node_dict})

        return nodes_list

    def _conditions_to_yaml(
        self,
        edges: List[ConditionalEdge]
    ) -> List[Dict]:
        """
        Convert conditional edges to YAML structure.

        Format:
        - from: node1
          rules:
            - if: {field: sentiment_score, op: ">", value: 0.5}
              then: positive_node
          default: neutral_node
        """
        conditions_list = []

        for edge in edges:
            rules = []

            for condition in edge.conditions:
                # Map operator enum to string
                op_str = self._operator_to_string(condition.operator)

                rules.append({
                    "if": {
                        "field": condition.field,
                        "op": op_str,
                        "value": condition.value
                    },
                    "then": condition.next_node
                })

            conditions_list.append({
                "from": edge.from_node,
                "rules": rules,
                "default": edge.default
            })

        return conditions_list

    def _operator_to_string(self, operator: ConditionOperator) -> str:
        """Convert ConditionOperator enum to string"""
        mapping = {
            ConditionOperator.GREATER_THAN: ">",
            ConditionOperator.LESS_THAN: "<",
            ConditionOperator.GREATER_EQUAL: ">=",
            ConditionOperator.LESS_EQUAL: "<=",
            ConditionOperator.EQUALS: "==",
            ConditionOperator.NOT_EQUALS: "!=",
            ConditionOperator.CONTAINS: "contains",
            ConditionOperator.NOT_CONTAINS: "not_contains",
            ConditionOperator.IN: "in",
            ConditionOperator.NOT_IN: "not_in",
        }
        return mapping.get(operator, str(operator.value))

    def _dump_yaml_custom(self, data: Dict) -> str:
        """
        Dump YAML with custom formatting.

        Features:
        - Multi-line strings use literal block (|)
        - Preserve order
        - Readable indentation
        """
        # Convert long strings to LiteralString
        data = self._mark_multiline_strings(data)

        # Dump with custom options
        stream = StringIO()
        yaml.dump(
            data,
            stream,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
            indent=2,
            width=80
        )

        return stream.getvalue()

    def _mark_multiline_strings(self, obj):
        """Recursively mark long strings as literal blocks"""
        if isinstance(obj, dict):
            return {k: self._mark_multiline_strings(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._mark_multiline_strings(item) for item in obj]
        elif isinstance(obj, str) and ('\n' in obj or len(obj) > 60):
            return LiteralString(obj)
        else:
            return obj

    def _generate_python(self, template: WorkflowTemplate) -> str:
        """
        Generate Python DSL from WorkflowTemplate.

        Output format:
        from cortexflow.dsl import Workflow, Node

        workflow = Workflow(
            name="workflow_name",
            version="1.0",
            description="...",
            triggers=["pattern1", "pattern2"],
            params={"key": "value"}
        )

        with workflow:
            research = Node.researcher(
                id="research_trends",
                instruction="...",
                timeout=300
            )

            analyze = Node.analyst(
                id="analyze_relevance",
                depends_on=[research],
                instruction="..."
            )
        """
        lines = []

        # Header
        lines.append("# Auto-generated Cortex Flow workflow")
        lines.append("# Generated from WorkflowTemplate\n")
        lines.append("from cortexflow.dsl import Workflow, Node\n")

        # Workflow definition
        lines.append(f'workflow = Workflow(')
        lines.append(f'    name="{template.name}",')
        lines.append(f'    version="{template.version}",')
        lines.append(f'    description="""{template.description}""",')

        if template.trigger_patterns:
            triggers_str = ', '.join(f'"{p}"' for p in template.trigger_patterns)
            lines.append(f'    triggers=[{triggers_str}],')

        if template.parameters:
            lines.append(f'    params={template.parameters}')

        lines.append(')\n')

        # Nodes
        lines.append('with workflow:')

        for node in template.nodes:
            lines.append(f'    {node.id} = Node.{node.agent}(')
            lines.append(f'        id="{node.id}",')

            if node.instruction:
                inst = node.instruction.replace('"', '\\"')
                lines.append(f'        instruction="{inst}",')

            if node.depends_on:
                deps = ', '.join(node.depends_on)
                lines.append(f'        depends_on=[{deps}],')

            if node.timeout != 120:
                lines.append(f'        timeout={node.timeout},')

            if node.tool_name:
                lines.append(f'        tool_name="{node.tool_name}",')

            if node.params:
                lines.append(f'        params={node.params},')

            lines.append('    )')

        return '\n'.join(lines)
