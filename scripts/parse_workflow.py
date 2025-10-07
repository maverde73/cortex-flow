#!/usr/bin/env python3
"""
Parse Workflow DSL to JSON

Converts YAML DSL scripts to WorkflowTemplate JSON format.

Usage:
    python scripts/parse_workflow.py examples/dsl/newsletter.yaml
    python scripts/parse_workflow.py examples/dsl/newsletter.yaml -o workflows/templates/newsletter.json
    python scripts/parse_workflow.py examples/dsl/*.yaml --validate-only
"""

import sys
import argparse
import json
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from workflows.dsl.parser import WorkflowDSLParser
from workflows.registry import WorkflowRegistry

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def parse_workflow(input_file: Path, output_file: Path = None, validate_only: bool = False):
    """
    Parse DSL workflow file.

    Args:
        input_file: Input DSL file (.yaml, .yml)
        output_file: Output JSON file (optional, prints to stdout if not provided)
        validate_only: Only validate, don't output
    """
    parser = WorkflowDSLParser()

    try:
        # Parse DSL to WorkflowTemplate
        logger.info(f"Parsing DSL file: {input_file}")
        template = parser.parse_file(input_file)

        # Validate template
        registry = WorkflowRegistry()
        errors = registry.validate_template(template)

        if errors:
            logger.error(f"❌ Validation errors in '{input_file}':")
            for error in errors:
                logger.error(f"   - {error}")
            return False

        logger.info(f"✅ Successfully parsed workflow '{template.name}'")
        logger.info(f"   - Version: {template.version}")
        logger.info(f"   - Nodes: {len(template.nodes)}")
        logger.info(f"   - Conditional edges: {len(template.conditional_edges)}")

        if validate_only:
            logger.info("✅ Validation successful (validate-only mode)")
            return True

        # Convert to JSON
        template_json = template.model_dump(exclude_none=True)
        json_output = json.dumps(template_json, indent=2, ensure_ascii=False)

        # Output
        if output_file:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(json_output)
            logger.info(f"✅ Saved to: {output_file}")
        else:
            # Print to stdout
            print(json_output)

        return True

    except Exception as e:
        logger.error(f"❌ Parsing failed: {e}", exc_info=True)
        return False


def main():
    """CLI entrypoint"""
    parser = argparse.ArgumentParser(
        description="Parse Workflow DSL to JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Parse and print to stdout
  python scripts/parse_workflow.py examples/dsl/newsletter.yaml

  # Parse and save to file
  python scripts/parse_workflow.py examples/dsl/newsletter.yaml -o workflows/templates/newsletter.json

  # Validate only (no output)
  python scripts/parse_workflow.py examples/dsl/*.yaml --validate-only

  # Parse multiple files
  python scripts/parse_workflow.py examples/dsl/*.yaml --output-dir workflows/templates/
        """
    )

    parser.add_argument(
        "input",
        type=Path,
        nargs='+',
        help="Input DSL file(s) (.yaml, .yml)"
    )

    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Output JSON file (prints to stdout if not specified)"
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Output directory for multiple files"
    )

    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate, don't generate output"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Handle multiple input files
    input_files = []
    for input_pattern in args.input:
        if '*' in str(input_pattern):
            # Glob pattern
            input_files.extend(input_pattern.parent.glob(input_pattern.name))
        else:
            input_files.append(input_pattern)

    if not input_files:
        logger.error("No input files found")
        return 1

    # Process files
    success_count = 0
    fail_count = 0

    for input_file in input_files:
        if not input_file.exists():
            logger.error(f"File not found: {input_file}")
            fail_count += 1
            continue

        # Determine output file
        output_file = None
        if args.output:
            output_file = args.output
        elif args.output_dir:
            # Generate output filename
            output_name = input_file.stem + ".json"
            output_file = args.output_dir / output_name

        # Parse
        success = parse_workflow(input_file, output_file, args.validate_only)

        if success:
            success_count += 1
        else:
            fail_count += 1

    # Summary
    if len(input_files) > 1:
        logger.info(f"\n📊 Summary: {success_count} succeeded, {fail_count} failed")

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
