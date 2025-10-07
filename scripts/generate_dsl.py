#!/usr/bin/env python3
"""
Generate Workflow DSL from JSON

Converts WorkflowTemplate JSON to YAML/Python DSL scripts.

Usage:
    python scripts/generate_dsl.py workflows/templates/report_generation.json
    python scripts/generate_dsl.py workflows/templates/report_generation.json -o examples/dsl/report.yaml
    python scripts/generate_dsl.py workflows/templates/*.json --output-dir examples/dsl/
    python scripts/generate_dsl.py report_generation --from-registry -f yaml
"""

import sys
import argparse
import json
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from workflows.dsl.generator import WorkflowDSLGenerator
from workflows.registry import WorkflowRegistry
from schemas.workflow_schemas import WorkflowTemplate

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def generate_dsl(
    template: WorkflowTemplate,
    output_file: Path = None,
    format: str = "yaml"
):
    """
    Generate DSL from WorkflowTemplate.

    Args:
        template: WorkflowTemplate to convert
        output_file: Output file (optional, prints to stdout if not provided)
        format: Output format ("yaml", "python")
    """
    generator = WorkflowDSLGenerator()

    try:
        # Generate DSL
        logger.info(f"Generating {format.upper()} DSL for workflow '{template.name}'")
        dsl_content = generator.generate(template, format=format)

        # Output
        if output_file:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(dsl_content)
            logger.info(f"✅ Saved to: {output_file}")
        else:
            # Print to stdout
            print(dsl_content)

        return True

    except Exception as e:
        logger.error(f"❌ Generation failed: {e}", exc_info=True)
        return False


def load_template_from_json(json_file: Path) -> WorkflowTemplate:
    """Load WorkflowTemplate from JSON file"""
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return WorkflowTemplate(**data)


def load_template_from_registry(template_name: str) -> WorkflowTemplate:
    """Load WorkflowTemplate from registry"""
    registry = WorkflowRegistry()
    registry.load_templates()

    template = registry.get(template_name)
    if not template:
        raise ValueError(
            f"Template '{template_name}' not found in registry. "
            f"Available: {registry.list_templates()}"
        )

    return template


def main():
    """CLI entrypoint"""
    parser = argparse.ArgumentParser(
        description="Generate Workflow DSL from JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate from JSON file
  python scripts/generate_dsl.py workflows/templates/report_generation.json

  # Generate and save to file
  python scripts/generate_dsl.py workflows/templates/report_generation.json -o examples/dsl/report.yaml

  # Generate from registry
  python scripts/generate_dsl.py report_generation --from-registry

  # Generate Python DSL
  python scripts/generate_dsl.py report_generation --from-registry -f python -o examples/dsl/report.py

  # Generate multiple files
  python scripts/generate_dsl.py workflows/templates/*.json --output-dir examples/dsl/
        """
    )

    parser.add_argument(
        "input",
        nargs='+',
        help="Input: JSON file(s) or template name(s) if --from-registry"
    )

    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Output DSL file (prints to stdout if not specified)"
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Output directory for multiple files"
    )

    parser.add_argument(
        "-f", "--format",
        choices=["yaml", "python"],
        default="yaml",
        help="Output format (default: yaml)"
    )

    parser.add_argument(
        "--from-registry",
        action="store_true",
        help="Load template from registry by name instead of JSON file"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Process inputs
    success_count = 0
    fail_count = 0

    for input_item in args.input:
        try:
            # Load template
            if args.from_registry:
                template = load_template_from_registry(input_item)
            else:
                input_path = Path(input_item)
                if not input_path.exists():
                    logger.error(f"File not found: {input_path}")
                    fail_count += 1
                    continue
                template = load_template_from_json(input_path)

            # Determine output file
            output_file = None
            if args.output:
                output_file = args.output
            elif args.output_dir:
                # Generate output filename
                ext = ".yaml" if args.format == "yaml" else ".py"
                output_name = template.name + ext
                output_file = args.output_dir / output_name

            # Generate
            success = generate_dsl(template, output_file, args.format)

            if success:
                success_count += 1
            else:
                fail_count += 1

        except Exception as e:
            logger.error(f"Failed to process {input_item}: {e}")
            fail_count += 1

    # Summary
    if len(args.input) > 1:
        logger.info(f"\n📊 Summary: {success_count} succeeded, {fail_count} failed")

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
