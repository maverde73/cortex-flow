"""
Lark-based Workflow DSL Parser

Custom text-based DSL with Lark parser for more expressive syntax.

Example DSL:
    workflow newsletter {
        version: "1.0"
        description: "Weekly newsletter generation"
        triggers: [".*newsletter.*", ".*weekly.*"]

        params {
            topic = "AI",
            audience = "tech professionals"
        }

        nodes {
            research = researcher()
                instruction: "Research {topic} trends"
                timeout: 300s

            analyze = analyst()
                depends_on: [research]
                instruction: "Analyze {research}"

            write = writer()
                depends_on: [analyze]
                instruction: "Write newsletter"
        }
    }
"""

import logging
from pathlib import Path
from typing import Dict, Any, List

try:
    from lark import Lark, Transformer
except ImportError:
    raise ImportError(
        "Lark parser not installed. Install with: pip install lark"
    )

from schemas.workflow_schemas import (
    WorkflowTemplate,
    WorkflowNode,
    ConditionalEdge,
    WorkflowCondition,
    ConditionOperator
)

logger = logging.getLogger(__name__)


class WorkflowTransformer(Transformer):
    """Transform Lark parse tree to WorkflowTemplate"""

    def start(self, children):
        """Process start rule - return the workflow dict"""
        return children[0] if children else {}

    def item(self, children):
        """Process item - unwrap the child"""
        return children[0] if children else None

    def workflow(self, children):
        """Process workflow definition"""
        workflow_data = {
            "name": None,
            "version": "1.0",
            "description": "",
            "trigger_patterns": [],
            "nodes": [],
            "parameters": {}
        }

        # First child is name
        if children:
            workflow_data["name"] = str(children[0])

        # Process other children
        for child in children[1:]:
            if isinstance(child, dict):
                # Merge dicts from items
                for key, value in child.items():
                    if key in workflow_data:
                        if isinstance(workflow_data[key], list):
                            workflow_data[key].extend(value if isinstance(value, list) else [value])
                        elif isinstance(workflow_data[key], dict):
                            workflow_data[key].update(value)
                        else:
                            workflow_data[key] = value

        return workflow_data

    def name(self, children):
        """Process workflow name"""
        return str(children[0])

    def version(self, children):
        """Process version"""
        return {"version": self._unquote(str(children[0]))}

    def description(self, children):
        """Process description"""
        return {"description": self._unquote(str(children[0]))}

    def triggers(self, children):
        """Process trigger patterns"""
        # children[0] is the string_list result (already a list)
        return {"trigger_patterns": children[0] if children else []}

    def string_list(self, children):
        """Process string list"""
        return [self._unquote(str(c)) for c in children]

    def params(self, children):
        """Process parameters"""
        params = {}
        for child in children:
            if isinstance(child, tuple) and len(child) == 2:
                params[child[0]] = child[1]
        return {"parameters": params}

    def param_item(self, children):
        """Process parameter item"""
        if len(children) >= 2:
            key = str(children[0])
            value = children[1]
            return (key, value)
        return None

    def nodes(self, children):
        """Process nodes"""
        return {"nodes": [c for c in children if c is not None]}

    def node(self, children):
        """Process single node"""
        node_data = {
            "id": str(children[0]),
            "agent": str(children[1]),
            "instruction": "",
            "depends_on": [],
            "parallel_group": None,
            "timeout": 120,
            "params": {},
            "tool_name": None
        }

        # Process node attributes
        for child in children[2:]:
            if isinstance(child, dict):
                node_data.update(child)

        return node_data

    def node_attr(self, children):
        """Process node attribute - unwrap the child"""
        return children[0] if children else None

    def depends_on(self, children):
        """Process dependencies"""
        # children[0] is the identifier_list result (already a list)
        return {"depends_on": children[0] if children else []}

    def identifier_list(self, children):
        """Process identifier list"""
        return [str(c) for c in children]

    def parallel_group(self, children):
        """Process parallel group"""
        return {"parallel_group": self._unquote(str(children[0]))}

    def timeout(self, children):
        """Process timeout"""
        timeout_str = str(children[0]).strip()

        # Parse format like "300s", "2m", "1h", or "120"
        if timeout_str.endswith('s'):
            return {"timeout": int(timeout_str[:-1])}
        elif timeout_str.endswith('m'):
            return {"timeout": int(timeout_str[:-1]) * 60}
        elif timeout_str.endswith('h'):
            return {"timeout": int(timeout_str[:-1]) * 3600}
        else:
            return {"timeout": int(timeout_str)}

    def instruction(self, children):
        """Process instruction"""
        return {"instruction": self._unquote(str(children[0]))}

    def value(self, children):
        """Process value"""
        if not children:
            return None

        child = children[0]
        child_str = str(child)

        # Boolean
        if child_str in ('true', 'false'):
            return child_str == 'true'

        # Number
        if child_str.isdigit():
            return int(child_str)

        # String
        return self._unquote(child_str)

    def string(self, children):
        """Process string"""
        return self._unquote(str(children[0]))

    def _unquote(self, s: str) -> str:
        """Remove quotes from string"""
        s = s.strip()
        if (s.startswith('"') and s.endswith('"')) or \
           (s.startswith("'") and s.endswith("'")):
            return s[1:-1]
        return s


class WorkflowLarkParser:
    """Lark-based DSL parser for workflow definitions"""

    def __init__(self):
        grammar_path = Path(__file__).parent / "grammar.lark"

        if not grammar_path.exists():
            raise FileNotFoundError(f"Grammar file not found: {grammar_path}")

        with open(grammar_path, 'r') as f:
            grammar = f.read()

        self.parser = Lark(
            grammar,
            parser='lalr',  # Fast LALR parser
        )
        self.transformer = WorkflowTransformer()

        logger.info("Lark parser initialized")

    def parse_file(self, file_path: str | Path) -> WorkflowTemplate:
        """
        Parse DSL file to WorkflowTemplate.

        Args:
            file_path: Path to DSL file (.cflow, .wf)

        Returns:
            WorkflowTemplate
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise ValueError(f"File not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return self.parse_string(content)

    def parse_string(self, content: str) -> WorkflowTemplate:
        """
        Parse DSL string to WorkflowTemplate.

        Args:
            content: DSL content as string

        Returns:
            WorkflowTemplate
        """
        try:
            # Parse with Lark to get parse tree
            tree = self.parser.parse(content)

            # Apply transformer to convert tree to dict
            workflow_data = self.transformer.transform(tree)

            # Convert to WorkflowTemplate
            nodes = []
            for node_data in workflow_data.get("nodes", []):
                nodes.append(WorkflowNode(
                    id=node_data["id"],
                    agent=node_data["agent"],
                    instruction=node_data["instruction"],
                    depends_on=node_data.get("depends_on", []),
                    parallel_group=node_data.get("parallel_group"),
                    timeout=node_data.get("timeout", 120),
                    tool_name=node_data.get("tool_name"),
                    params=node_data.get("params", {})
                ))

            template = WorkflowTemplate(
                name=workflow_data["name"],
                version=workflow_data.get("version", "1.0"),
                description=workflow_data.get("description", ""),
                trigger_patterns=workflow_data.get("trigger_patterns", []),
                nodes=nodes,
                parameters=workflow_data.get("parameters", {})
            )

            logger.info(f"Parsed workflow '{template.name}' with {len(template.nodes)} nodes")

            return template

        except Exception as e:
            logger.error(f"Parse error: {e}")
            raise ValueError(f"Failed to parse DSL: {e}")


class WorkflowLarkGenerator:
    """Generate Lark DSL from WorkflowTemplate"""

    def generate(self, template: WorkflowTemplate) -> str:
        """
        Generate Lark DSL from WorkflowTemplate.

        Args:
            template: WorkflowTemplate to convert

        Returns:
            Lark DSL script as string
        """
        lines = []

        # Workflow header
        lines.append(f'workflow {template.name} {{')

        # Metadata
        lines.append(f'    version: "{template.version}"')

        if template.description:
            desc = template.description.replace('"', '\\"')
            lines.append(f'    description: "{desc}"')

        # Triggers
        if template.trigger_patterns:
            triggers_str = ', '.join(f'"{p}"' for p in template.trigger_patterns)
            lines.append(f'    triggers: [{triggers_str}]')

        # Parameters
        if template.parameters:
            lines.append('    params {')
            for key, value in template.parameters.items():
                if isinstance(value, str):
                    lines.append(f'        {key} = "{value}",')
                else:
                    lines.append(f'        {key} = {value},')
            lines.append('    }')

        # Nodes
        lines.append('    ')
        lines.append('    nodes {')

        for node in template.nodes:
            # Node definition
            lines.append(f'        {node.id} = {node.agent}()')

            # Dependencies
            if node.depends_on:
                deps = ', '.join(node.depends_on)
                lines.append(f'            depends_on: [{deps}]')

            # Parallel group
            if node.parallel_group:
                lines.append(f'            parallel_group: "{node.parallel_group}"')

            # Timeout
            if node.timeout != 120:
                lines.append(f'            timeout: {node.timeout}s')

            # Instruction
            if node.instruction:
                inst = node.instruction.replace('"', '\\"').replace('\n', '\\n')
                lines.append(f'            instruction: "{inst}"')

            lines.append('')

        lines.append('    }')
        lines.append('}')

        return '\n'.join(lines)

    def generate_file(
        self,
        template: WorkflowTemplate,
        output_path: str | Path
    ):
        """
        Generate Lark DSL file from WorkflowTemplate.

        Args:
            template: WorkflowTemplate to convert
            output_path: Output file path
        """
        output_path = Path(output_path)
        content = self.generate(template)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"Generated Lark DSL file: {output_path}")
