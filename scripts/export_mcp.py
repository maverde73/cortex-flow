#!/usr/bin/env python3
"""
Export Workflow as MCP Server

CLI tool to export Cortex Flow workflows as standalone MCP servers.
"""

import sys
import json
import argparse
import logging
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.mcp_export import MCPWorkflowExporter, DependencyAnalyzer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def list_workflows(project: str):
    """List all available workflows in a project."""
    project_path = Path(f"projects/{project}/workflows")

    if not project_path.exists():
        print(f"Project '{project}' not found or has no workflows")
        return

    print(f"\nAvailable workflows in project '{project}':")
    print("-" * 50)

    for workflow_file in sorted(project_path.glob("*.json")):
        try:
            with open(workflow_file, 'r') as f:
                workflow = json.load(f)
                name = workflow.get("name", workflow_file.stem)
                description = workflow.get("description", "No description")
                print(f"  • {name}")
                print(f"    {description[:60]}{'...' if len(description) > 60 else ''}")
        except Exception as e:
            print(f"  • {workflow_file.stem} (error loading)")


def analyze_workflow(project: str, workflow_name: str):
    """Analyze and display workflow dependencies."""
    analyzer = DependencyAnalyzer(project)

    try:
        print(f"\nAnalyzing workflow '{workflow_name}'...")
        print("-" * 50)

        # Get dependencies
        deps = analyzer.analyze_deep(workflow_name)

        # Get workflow info
        info = analyzer.get_workflow_info(workflow_name)

        print(f"Name: {info['name']}")
        print(f"Version: {info['version']}")
        print(f"Description: {info['description']}")
        print(f"Nodes: {info['node_count']}")
        print()

        print("Parameters:")
        if info['parameters']:
            for param, default in info['parameters'].items():
                print(f"  • {param}: {default if default else 'Required'}")
        else:
            print("  • None")
        print()

        print("Dependencies:")
        print(f"  Agents: {', '.join(deps['agents']) if deps['agents'] else 'None'}")
        print(f"  Workflows: {', '.join(deps['workflows']) if deps['workflows'] else 'None'}")
        print(f"  MCP Tools: {', '.join(deps['mcp_tools']) if deps['mcp_tools'] else 'None (will be mocked)'}")

        # Validate
        issues = analyzer.validate_dependencies(deps)
        if issues:
            print("\nValidation Issues:")
            for issue_type, items in issues.items():
                if items:
                    print(f"  • {issue_type}: {', '.join(items)}")
        else:
            print("\n✅ All dependencies validated successfully")

    except FileNotFoundError:
        print(f"Workflow '{workflow_name}' not found in project '{project}'")
    except Exception as e:
        print(f"Error analyzing workflow: {e}")


def export_workflow(project: str, workflow_name: str, output_dir: str,
                   include_docker: bool, dry_run: bool):
    """Export a workflow as an MCP server."""

    if dry_run:
        print(f"\n[DRY RUN] Would export workflow '{workflow_name}' to {output_dir}")
        analyze_workflow(project, workflow_name)
        return

    exporter = MCPWorkflowExporter(project)

    print(f"\nExporting workflow '{workflow_name}'...")
    print(f"Output directory: {output_dir}")
    print(f"Include Docker: {include_docker}")
    print("-" * 50)

    result = exporter.export_workflow(workflow_name, output_dir, include_docker)

    if result['success']:
        print("\n✅ Export successful!")
        print(f"\nExported to: {result['output_dir']}")
        print("\nDependencies included:")
        print(f"  • {len(result['dependencies']['agents'])} agents")
        print(f"  • {len(result['dependencies']['workflows'])} workflows")
        print(f"  • {len(result['dependencies']['mcp_tools'])} MCP tools (mocked)")

        print(f"\nFiles created: {len(result['files_created'])}")

        # Show quick start instructions
        print("\n" + "=" * 50)
        print("Quick Start:")
        print("=" * 50)
        print(f"cd {result['output_dir']}")
        print("cp .env.example .env")
        print("# Edit .env and add your API keys")
        print("./run.sh  # For stdio mode")
        print("# OR")
        print("./run.sh http  # For HTTP mode (default port 8000, change MCP_PORT in .env if needed)")

        if include_docker:
            print("\n# Using Docker:")
            print("docker-compose up")

    else:
        print(f"\n❌ Export failed: {result['error']}")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Export Cortex Flow workflows as standalone MCP servers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all workflows in a project
  %(prog)s --list --project myproject

  # Analyze a workflow's dependencies
  %(prog)s --analyze research_workflow --project myproject

  # Export a workflow
  %(prog)s research_workflow ./export/research --project myproject

  # Export with Docker support
  %(prog)s research_workflow ./export/research --docker

  # Dry run to see what would be exported
  %(prog)s research_workflow ./export/research --dry-run
        """
    )

    parser.add_argument(
        "workflow",
        nargs="?",
        help="Name of the workflow to export"
    )

    parser.add_argument(
        "output",
        nargs="?",
        help="Output directory for the exported server"
    )

    parser.add_argument(
        "--project", "-p",
        default="default",
        help="Project name (default: default)"
    )

    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List all available workflows"
    )

    parser.add_argument(
        "--analyze", "-a",
        metavar="WORKFLOW",
        help="Analyze workflow dependencies"
    )

    parser.add_argument(
        "--docker", "-d",
        action="store_true",
        help="Include Docker files in export"
    )

    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Show what would be exported without actually exporting"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Handle different modes
    if args.list:
        list_workflows(args.project)
    elif args.analyze:
        analyze_workflow(args.project, args.analyze)
    elif args.workflow:
        if not args.output and not args.dry_run:
            parser.error("Output directory is required (unless using --dry-run)")

        output_dir = args.output or f"./export/{args.workflow}"
        export_workflow(
            args.project,
            args.workflow,
            output_dir,
            args.docker,
            args.dry_run
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()