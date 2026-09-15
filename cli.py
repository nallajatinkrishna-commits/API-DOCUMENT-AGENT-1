"""
CLI interface for the API Documentation Agent.
Usage:
    python -m backend.cli parse <file_or_directory>
    python -m backend.cli generate <file_or_directory> [-o OUTPUT_FILE] [--ai]
"""

import argparse
import asyncio
import json
import os
import sys
from typing import Dict

from backend.parsers.manager import ParserManager
from backend.generator.template_gen import TemplateDocGenerator
from backend.generator.ai_gen import AIDocGenerator
from backend.generator.exporter import DocExporter


def load_sources(target_path: str) -> Dict[str, str]:
    sources: Dict[str, str] = {}
    if os.path.isfile(target_path):
        with open(target_path, "r", encoding="utf-8", errors="ignore") as f:
            sources[target_path] = f.read()
    elif os.path.isdir(target_path):
        for root, _, files in os.walk(target_path):
            for file in files:
                if file.endswith((".py", ".js", ".ts", ".jsx", ".tsx")):
                    full_p = os.path.join(root, file)
                    rel_p = os.path.relpath(full_p, target_path)
                    with open(full_p, "r", encoding="utf-8", errors="ignore") as f:
                        sources[rel_p] = f.read()
    else:
        print(f"Error: Path '{target_path}' does not exist.", file=sys.stderr)
        sys.exit(1)
    return sources


async def run_cli():
    parser = argparse.ArgumentParser(description="API Documentation Agent CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Command: parse
    parse_cmd = subparsers.add_parser("parse", help="Parse source code and print detected endpoints JSON")
    parse_cmd.add_argument("path", help="Path to source file or directory")
    parse_cmd.add_argument("--framework", help="Framework hint (fastapi, flask, express)", default="auto")

    # Command: generate
    gen_cmd = subparsers.add_parser("generate", help="Generate API documentation Markdown or HTML")
    gen_cmd.add_argument("path", help="Path to source file or directory")
    gen_cmd.add_argument("-o", "--output", help="Output file path (default: stdout)", default=None)
    gen_cmd.add_argument("--format", choices=["md", "html"], default="md", help="Output format")
    gen_cmd.add_argument("--ai", action="store_true", help="Use Anthropic Claude for AI generation")

    args = parser.parse_args()

    manager = ParserManager()
    sources = load_sources(args.path)
    endpoints, frameworks = manager.parse_project(sources, framework_hint=getattr(args, "framework", "auto"))

    if args.command == "parse":
        output_data = {
            "total_endpoints": len(endpoints),
            "frameworks": frameworks,
            "endpoints": [ep.model_dump() for ep in endpoints],
        }
        print(json.dumps(output_data, indent=2))

    elif args.command == "generate":
        if not endpoints:
            print("No endpoints detected in source path.", file=sys.stderr)
            sys.exit(1)

        exporter = DocExporter()
        if args.ai:
            ai_gen = AIDocGenerator()
            if not ai_gen.is_available:
                print("Warning: ANTHROPIC_API_KEY not set. Falling back to template mode.", file=sys.stderr)
            docs = await ai_gen.generate_batch_docs(endpoints)
        else:
            tpl_gen = TemplateDocGenerator()
            docs = [tpl_gen.generate_endpoint_doc(ep) for ep in endpoints]

        combined_md = exporter.combine_markdown(docs, endpoints)

        if args.format == "html":
            result = exporter.render_html(combined_md)
        else:
            result = combined_md

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(result)
            print(f"Documentation successfully generated: {args.output}")
        else:
            print(result)


def main():
    asyncio.run(run_cli())


if __name__ == "__main__":
    main()
