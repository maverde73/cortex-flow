#!/usr/bin/env python3
"""
Test script for Python workflow loading
"""

import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(name)s - %(message)s'
)

from workflows.registry import WorkflowRegistry

def main():
    print("=" * 80)
    print("Testing Python Workflow Auto-Loading")
    print("=" * 80)
    print()

    # Create registry (will use default templates directory)
    registry = WorkflowRegistry()

    print("📂 Loading workflows from: workflows/templates")
    print()

    # Load all templates (JSON + Python)
    count = registry.load_templates()

    print()
    print(f"✅ Total templates loaded: {count}")
    print()

    # List all available templates
    templates = registry.list_templates()
    print(f"📋 Available templates ({len(templates)}):")
    for template_name in sorted(templates):
        template = registry.get(template_name)
        node_count = len(template.nodes)
        version = template.version if hasattr(template, 'version') else 'N/A'
        print(f"  • {template_name} (v{version}) - {node_count} nodes")
    print()

    # Test the Python workflow specifically
    python_workflow_name = "database_query_smart_v3_python"
    print(f"🔍 Testing Python workflow: {python_workflow_name}")

    python_wf = registry.get(python_workflow_name)
    if python_wf:
        print(f"   ✅ Found: {python_wf.name}")
        print(f"   Version: {python_wf.version}")
        print(f"   Description: {python_wf.description}")
        print(f"   Nodes: {len(python_wf.nodes)}")
        print(f"   Conditional Edges: {len(python_wf.conditional_edges)}")

        print()
        print("   Node Structure:")
        for node in python_wf.nodes:
            deps = f" (depends on: {', '.join(node.depends_on)})" if node.depends_on else ""
            print(f"     - {node.id} [{node.agent}]{deps}")

        print()
        print("   Conditional Routing:")
        for edge in python_wf.conditional_edges:
            print(f"     - {edge.from_node} →")
            for cond in edge.conditions:
                print(f"         if {cond.field} {cond.operator.value} {cond.value} → {cond.next_node}")
            print(f"         else → {edge.default}")
    else:
        print(f"   ❌ Python workflow not found!")
        return 1

    print()
    print("=" * 80)
    print("✅ All tests passed!")
    print("=" * 80)

    return 0

if __name__ == "__main__":
    sys.exit(main())
