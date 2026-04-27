#!/usr/bin/env python3
"""
Hexel SDK Generator

Reads OpenAPI specs + overrides → builds IR → generates Python SDK.

Usage:
    python generator/generate.py
"""
import json
import os
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from parser import build_from_files

SPECS_DIR = "specs"
OVERRIDES = "generator/overrides.json"
OUTPUT_DIR = "hexel/compute"
TEMPLATES_DIR = "generator/templates"

# Type mapping: OpenAPI → Python
TYPE_MAP = {
    "string": "str",
    "integer": "int",
    "number": "float",
    "boolean": "bool",
    "object": "dict",
    "any": "Any",
}


def python_type(t: str) -> str:
    """Convert IR type to Python type annotation."""
    if t.startswith("list["):
        inner = t[5:-1]
        return f"list[{python_type(inner)}]"
    if t.startswith("dict["):
        return t
    return TYPE_MAP.get(t, t)


def to_class_name(service_name: str) -> str:
    """sandbox → SandboxClient"""
    return service_name.capitalize() + "Client"


def generate():
    print("→ Parsing specs...")
    ir = build_from_files(SPECS_DIR, OVERRIDES)

    print(f"  Services: {list(ir['services'].keys())}")
    print(f"  Types: {len(ir['types'])}")

    # Setup Jinja
    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["python_type"] = python_type

    output = Path(OUTPUT_DIR)
    output.mkdir(parents=True, exist_ok=True)

    # Generate types.py
    print("→ Generating types.py...")
    types_tmpl = env.get_template("types.py.j2")
    types_code = types_tmpl.render(types=ir["types"])
    (output / "types.py").write_text(types_code)

    # Generate service clients
    service_tmpl = env.get_template("service.py.j2")
    output_dirs = set()
    for service_name, service_def in ir["services"].items():
        class_name = to_class_name(service_name)
        has_ws = service_name in ir.get("websocket", {})

        # Determine output directory
        svc_output = Path(service_def.get("output_dir", OUTPUT_DIR))
        svc_output.mkdir(parents=True, exist_ok=True)
        output_dirs.add(str(svc_output))

        print(f"→ Generating {svc_output}/_{service_name}.py ({class_name}, {len(service_def['methods'])} methods)...")
        code = service_tmpl.render(
            class_name=class_name,
            description=service_def["description"],
            methods=service_def["methods"],
            has_ws=has_ws,
        )
        (svc_output / f"_{service_name}.py").write_text(code)

    # Generate __init__.py
    print("→ Generating __init__.py...")
    init_tmpl = env.get_template("compute_init.py.j2")
    init_code = init_tmpl.render()
    (output / "__init__.py").write_text(init_code)

    # Write IR for debugging
    ir_path = Path("generator/ir.json")
    ir_path.write_text(json.dumps(ir, indent=2))
    print(f"→ IR written to {ir_path}")

    print(f"\n✅ Generated {len(ir['services'])} services + types in {OUTPUT_DIR}/")
    print("   Files:")
    for f in sorted(output.glob("*.py")):
        lines = len(f.read_text().splitlines())
        print(f"   {f.name:20s} {lines:4d} lines")


if __name__ == "__main__":
    os.chdir(Path(__file__).resolve().parent.parent)
    generate()
