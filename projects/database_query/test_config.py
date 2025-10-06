#!/usr/bin/env python3
"""
Test script to verify database_query project configuration
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from config import load_config
from pathlib import Path

def test_configuration():
    """Test that the database_query project configuration loads correctly"""

    print("=" * 60)
    print("Testing database_query Project Configuration")
    print("=" * 60)
    print()

    # Load configuration
    print("📋 Loading configuration...")
    config = load_config(project_name="database_query")
    print(f"✓ Project loaded: {config.name}")
    print()

    # Test project settings
    print("🔧 Project Settings:")
    print(f"  - Name: {config.project.name}")
    print(f"  - Version: {config.project.version}")
    print(f"  - Description: {config.project.description}")
    print(f"  - Checkpoint backend: {config.project.settings.checkpoint_backend}")
    print(f"  - HTTP timeout: {config.project.settings.http_timeout}s")
    print()

    # Test agents configuration
    print("🤖 Agents Configuration:")
    enabled_agents = config.get_enabled_agents()
    print(f"  - Enabled agents: {', '.join(enabled_agents)}")

    for agent_name in enabled_agents:
        agent = config.get_agent_config(agent_name)
        print(f"  - {agent_name}:")
        print(f"      Model: {agent.model}")
        print(f"      Strategy: {agent.react_strategy}")
        print(f"      Port: {agent.port}")
        print(f"      Reflection: {agent.enable_reflection}")
    print()

    # Test MCP configuration
    print("🔌 MCP Configuration:")
    print(f"  - MCP enabled: {config.mcp.enabled}")
    if config.mcp.enabled:
        servers = config.get_enabled_mcp_servers()
        print(f"  - Enabled servers: {len(servers)}")
        for name, server in servers.items():
            print(f"  - {name}:")
            print(f"      URL: {server.url}")
            print(f"      Transport: {server.transport}")
            print(f"      Timeout: {server.timeout}s")
            print(f"      Prompts file: {server.prompts_file}")
            print(f"      Tool association: {server.prompt_tool_association}")
    print()

    # Test ReAct configuration
    print("⚡ ReAct Configuration:")
    print(f"  - Timeout: {config.react.execution.timeout_seconds}s")
    print(f"  - Early stopping: {config.react.execution.enable_early_stopping}")
    print(f"  - Verbose logging: {config.react.logging.enable_verbose}")
    print(f"  - Reflection enabled: {config.react.reflection.enabled}")
    if config.react.reflection.enabled:
        print(f"      Threshold: {config.react.reflection.quality_threshold}")
        print(f"      Max iterations: {config.react.reflection.max_iterations}")
    print()

    # Test workflows
    print("📊 Workflows:")
    workflow_dir = Path(f"projects/{config.name}/workflows")
    if workflow_dir.exists():
        workflows = list(workflow_dir.glob("*.json"))
        print(f"  - Total workflows: {len(workflows)}")
        for wf in workflows:
            print(f"      • {wf.stem}")
    print()

    # Test custom files
    print("📄 Custom Files:")
    project_dir = Path(f"projects/{config.name}")

    supervisor_prompt = project_dir / "SUPERVISOR_PROMPT.md"
    if supervisor_prompt.exists():
        print(f"  ✓ SUPERVISOR_PROMPT.md: {supervisor_prompt.stat().st_size} bytes")

    readme = project_dir / "README.md"
    if readme.exists():
        print(f"  ✓ README.md: {readme.stat().st_size} bytes")
    print()

    # Summary
    print("=" * 60)
    print("✅ All configuration tests passed!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Ensure MCP server is running: http://localhost:8005/mcp")
    print("  2. Start agents: ./scripts/start_all.sh")
    print("  3. Test with query: See README.md for examples")
    print()

if __name__ == "__main__":
    try:
        test_configuration()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
