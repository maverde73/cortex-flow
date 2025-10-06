#!/usr/bin/env python3
"""
Test script for database_query_with_retry workflow
"""
import asyncio
import json
from workflows.registry import get_workflow_registry
from workflows.engine import WorkflowEngine

async def test_workflow():
    """Test the database query workflow with retry loop"""

    print("🧪 Testing database_query_with_retry workflow...")
    print()

    # Load workflow from project-specific directory
    templates_dir = "projects/database_query/workflows"
    registry = get_workflow_registry(templates_dir=templates_dir)
    workflow = registry.get("database_query_with_retry")

    if not workflow:
        print("❌ Workflow 'database_query_with_retry' not found!")
        return

    print(f"✅ Loaded workflow: {workflow.name}")
    print(f"   Description: {workflow.description}")
    print(f"   Nodes: {len(workflow.nodes)}")
    print()

    # Test 1: Correct query
    print("=" * 60)
    print("TEST 1: Correct Query - List all employees")
    print("=" * 60)

    engine = WorkflowEngine()

    try:
        result = await engine.execute_workflow(
            template=workflow,
            user_input="Mostra tutti i dipendenti della tabella employees",
            params={}
        )

        print(f"\n✅ Workflow completed!")
        print(f"   Status: {result.status}")
        print(f"   Nodes executed: {len(result.completed_nodes)}")
        print(f"   Completed nodes: {result.completed_nodes}")
        print(f"\n📊 Final output:\n{result.final_output[:500] if result.final_output else 'No output'}...")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print()

if __name__ == "__main__":
    asyncio.run(test_workflow())
