"""
Workflow DSL Parser

Converts YAML/Python DSL scripts to WorkflowTemplate (JSON).

Supported formats:
- YAML (.yaml, .yml)
- Python (.py) - future

Example:
    parser = WorkflowDSLParser()
    template = parser.parse_file("examples/dsl/newsletter.yaml")
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

from schemas.workflow_schemas import (
    WorkflowTemplate,
    WorkflowNode,
    ConditionalEdge,
    WorkflowCondition,
    ConditionOperator
)

logger = logging.getLogger(__name__)


class WorkflowDSLParser:
    """Parse DSL scripts to WorkflowTemplate"""

    def __init__(self):
        self.supported_formats = [".yaml", ".yml"]

    def parse_file(self, file_path: str | Path) -> WorkflowTemplate:
        """
        Parse DSL file to WorkflowTemplate.

        Args:
            file_path: Path to DSL file (.yaml, .yml)

        Returns:
            WorkflowTemplate

        Raises:
            ValueError: If file format unsupported or parsing fails
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise ValueError(f"File not found: {file_path}")

        if file_path.suffix not in self.supported_formats:
            raise ValueError(
                f"Unsupported format: {file_path.suffix}. "
                f"Supported: {self.supported_formats}"
            )

        logger.info(f"Parsing DSL file: {file_path}")

        # Parse based on format
        if file_path.suffix in [".yaml", ".yml"]:
            return self._parse_yaml(file_path)
        else:
            raise ValueError(f"Unsupported format: {file_path.suffix}")

    def parse_string(self, content: str, format: str = "yaml") -> WorkflowTemplate:
        """
        Parse DSL string to WorkflowTemplate.

        Args:
            content: DSL content as string
            format: Format type ("yaml", "python")

        Returns:
            WorkflowTemplate
        """
        if format == "yaml":
            data = yaml.safe_load(content)
            return self._dict_to_template(data)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _parse_yaml(self, file_path: Path) -> WorkflowTemplate:
        """Parse YAML file to WorkflowTemplate"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        return self._dict_to_template(data)

    def _dict_to_template(self, data: Dict[str, Any]) -> WorkflowTemplate:
        """
        Convert parsed YAML dict to WorkflowTemplate.

        YAML Structure:
        workflow: name
        version: "1.0"
        description: "..."
        triggers: ["pattern1", "pattern2"]
        params:
          key: value
        nodes:
          - node_id:
              agent: researcher
              instruction: "..."
              depends_on: [other_node]
              timeout: 120
              params: {}
        conditions:
          - from: node1
            rules:
              - if: {field: sentiment_score, op: ">", value: 0.5}
                then: positive_branch
              - if: {field: sentiment_score, op: "<=", value: 0.5}
                then: negative_branch
            default: neutral_branch
        """
        # Extract basic fields
        workflow_name = data.get("workflow")
        if not workflow_name:
            raise ValueError("Missing required field: 'workflow'")

        version = data.get("version", "1.0")
        description = data.get("description", "")
        trigger_patterns = data.get("triggers", [])
        parameters = data.get("params", {})

        # Parse nodes
        nodes_data = data.get("nodes", [])
        nodes = self._parse_nodes(nodes_data)

        # Parse conditional edges
        conditions_data = data.get("conditions", [])
        conditional_edges = self._parse_conditional_edges(conditions_data)

        return WorkflowTemplate(
            name=workflow_name,
            version=version,
            description=description,
            trigger_patterns=trigger_patterns,
            nodes=nodes,
            conditional_edges=conditional_edges,
            parameters=parameters
        )

    def _parse_nodes(self, nodes_data: List[Dict]) -> List[WorkflowNode]:
        """
        Parse nodes from YAML structure.

        YAML node formats:
        1. Simple:
           - node_id:
               agent: researcher
               instruction: "..."

        2. With dependencies:
           - analyze:
               agent: analyst
               depends_on: [research]
               instruction: "..."

        3. Parallel group:
           - web_research:
               agent: researcher
               parallel_group: sources
               instruction: "..."

        4. MCP tool:
           - query_db:
               agent: mcp_tool
               tool_name: query_database
               params:
                 query_payload: {...}
        """
        nodes = []

        for node_dict in nodes_data:
            # Node dict has single key (node_id) → value (node config)
            if len(node_dict) != 1:
                raise ValueError(
                    f"Invalid node structure: {node_dict}. "
                    "Expected single key-value pair"
                )

            node_id = list(node_dict.keys())[0]
            node_config = node_dict[node_id]

            # Required fields
            agent = node_config.get("agent")
            if not agent:
                raise ValueError(f"Node '{node_id}' missing required field: 'agent'")

            instruction = node_config.get("instruction", "")

            # Optional fields
            depends_on = node_config.get("depends_on", [])
            parallel_group = node_config.get("parallel_group")
            timeout = node_config.get("timeout", 120)
            tool_name = node_config.get("tool_name")
            params = node_config.get("params", {})
            template = node_config.get("template")
            use_mcp_prompt = node_config.get("use_mcp_prompt", False)

            # Parse timeout (support "300s" format)
            if isinstance(timeout, str):
                timeout = self._parse_timeout(timeout)

            nodes.append(WorkflowNode(
                id=node_id,
                agent=agent,
                instruction=instruction,
                depends_on=depends_on,
                parallel_group=parallel_group,
                timeout=timeout,
                tool_name=tool_name,
                params=params,
                template=template,
                use_mcp_prompt=use_mcp_prompt
            ))

        return nodes

    def _parse_conditional_edges(
        self,
        conditions_data: List[Dict]
    ) -> List[ConditionalEdge]:
        """
        Parse conditional edges from YAML.

        YAML structure:
        conditions:
          - from: sentiment_analysis
            rules:
              - if: {field: sentiment_score, op: ">", value: 0.7}
                then: positive_content
              - if: {field: sentiment_score, op: "<", value: 0.3}
                then: negative_content
            default: neutral_content
        """
        edges = []

        for condition_dict in conditions_data:
            from_node = condition_dict.get("from")
            if not from_node:
                raise ValueError("Conditional edge missing 'from' field")

            rules = condition_dict.get("rules", [])
            default = condition_dict.get("default")

            if not default:
                raise ValueError(
                    f"Conditional edge from '{from_node}' missing 'default' field"
                )

            # Parse rules
            conditions = []
            for rule in rules:
                if_clause = rule.get("if")
                then_node = rule.get("then")

                if not if_clause or not then_node:
                    raise ValueError(
                        f"Invalid rule in conditional edge: {rule}. "
                        "Expected 'if' and 'then' fields"
                    )

                field = if_clause.get("field")
                op = if_clause.get("op")
                value = if_clause.get("value")

                if not field or not op:
                    raise ValueError(
                        f"Invalid condition: {if_clause}. "
                        "Expected 'field' and 'op'"
                    )

                # Map operator aliases
                op_mapping = {
                    ">": ConditionOperator.GREATER_THAN,
                    "<": ConditionOperator.LESS_THAN,
                    ">=": ConditionOperator.GREATER_EQUAL,
                    "<=": ConditionOperator.LESS_EQUAL,
                    "==": ConditionOperator.EQUALS,
                    "!=": ConditionOperator.NOT_EQUALS,
                    "equals": ConditionOperator.EQUALS,
                    "not_equals": ConditionOperator.NOT_EQUALS,
                    "contains": ConditionOperator.CONTAINS,
                    "not_contains": ConditionOperator.NOT_CONTAINS,
                    "in": ConditionOperator.IN,
                    "not_in": ConditionOperator.NOT_IN,
                }

                operator = op_mapping.get(op)
                if not operator:
                    raise ValueError(
                        f"Unknown operator: '{op}'. "
                        f"Supported: {list(op_mapping.keys())}"
                    )

                conditions.append(WorkflowCondition(
                    field=field,
                    operator=operator,
                    value=value,
                    next_node=then_node
                ))

            edges.append(ConditionalEdge(
                from_node=from_node,
                conditions=conditions,
                default=default
            ))

        return edges

    def _parse_timeout(self, timeout_str: str) -> int:
        """
        Parse timeout string to seconds.

        Supported formats:
        - "120s" → 120
        - "2m" → 120
        - "1h" → 3600
        """
        timeout_str = timeout_str.strip().lower()

        if timeout_str.endswith('s'):
            return int(timeout_str[:-1])
        elif timeout_str.endswith('m'):
            return int(timeout_str[:-1]) * 60
        elif timeout_str.endswith('h'):
            return int(timeout_str[:-1]) * 3600
        else:
            # Try parse as plain integer
            try:
                return int(timeout_str)
            except ValueError:
                raise ValueError(
                    f"Invalid timeout format: '{timeout_str}'. "
                    "Expected: '120s', '2m', '1h', or plain integer"
                )
