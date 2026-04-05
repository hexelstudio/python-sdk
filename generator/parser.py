"""
Spec parser — reads OpenAPI specs + overrides → produces IR (intermediate representation).

The IR is a clean, normalized model that the code generator reads.
"""
import json
import re
from pathlib import Path


def load_spec(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def resolve_ref(spec: dict, ref: str) -> dict:
    """Resolve a $ref like #/components/schemas/models.Agent"""
    parts = ref.lstrip("#/").split("/")
    node = spec
    for p in parts:
        node = node.get(p, {})
    return node


def extract_schema_fields(spec: dict, schema: dict) -> list[dict]:
    """Extract fields from a schema, resolving $ref."""
    if "$ref" in schema:
        schema = resolve_ref(spec, schema["$ref"])
    props = schema.get("properties", {})
    required = set(schema.get("required", []))
    fields = []
    for name, prop in props.items():
        typ = prop.get("type", "any")
        if "$ref" in prop:
            typ = prop["$ref"].split("/")[-1]
        if typ == "array" and "items" in prop:
            item_type = prop["items"].get("type", "any")
            if "$ref" in prop["items"]:
                item_type = prop["items"]["$ref"].split("/")[-1]
            typ = f"list[{item_type}]"
        if prop.get("additionalProperties") and isinstance(prop["additionalProperties"], dict):
            val_type = prop["additionalProperties"].get("type", "any")
            typ = f"dict[str, {val_type}]"
        elif prop.get("additionalProperties") is True:
            typ = "dict"
        fields.append({
            "name": name,
            "type": typ,
            "required": name in required,
            "description": prop.get("description", ""),
        })
    return fields


def parse_path_params(path: str) -> list[str]:
    """Extract path parameters like {id}, {agent_id}."""
    return re.findall(r"\{(\w+)\}", path)


def build_ir(specs: dict[str, dict], overrides: dict) -> dict:
    """
    Build IR from multiple OpenAPI specs + overrides.

    specs: {"compute": spec_dict, "registry": spec_dict, "agentd": spec_dict}
    overrides: the overrides.json content
    """
    ir = {
        "services": {},
        "types": {},
    }

    # Collect all schemas from all specs
    for spec_name, spec in specs.items():
        for schema_name, schema_def in spec.get("components", {}).get("schemas", {}).items():
            type_name = overrides.get("type_renames", {}).get(schema_name, schema_name)
            # Clean up Go-style names
            type_name = type_name.replace("models.", "").replace("iamclient.", "").replace("registryclient.", "")
            ir["types"][type_name] = {
                "original": schema_name,
                "fields": extract_schema_fields(spec, schema_def),
            }

    # Build services from overrides
    exclude = overrides.get("exclude_paths", [])
    for service_name, service_def in overrides.get("services", {}).items():
        methods = {}
        for endpoint_key, method_name in service_def.get("endpoints", {}).items():
            # Parse "POST /compute/v1/vms/allocate"
            parts = endpoint_key.split(" ", 1)
            http_method = parts[0]
            path = parts[1]

            # Find this endpoint in any spec
            endpoint_spec = None
            source_spec = None
            for spec_name, spec in specs.items():
                if path in spec.get("paths", {}):
                    ep = spec["paths"][path].get(http_method.lower(), {})
                    if ep:
                        endpoint_spec = ep
                        source_spec = spec
                        break

            if not endpoint_spec:
                continue

            # Extract request/response types
            request_type = None
            request_body = endpoint_spec.get("requestBody", {})
            if request_body:
                content = request_body.get("content", {}).get("application/json", {})
                schema = content.get("schema", {})
                if "$ref" in schema:
                    request_type = schema["$ref"].split("/")[-1]
                    request_type = overrides.get("type_renames", {}).get(request_type, request_type)
                    request_type = request_type.replace("models.", "")

            response_type = None
            resp_200 = endpoint_spec.get("responses", {}).get("200", endpoint_spec.get("responses", {}).get("201", {}))
            if resp_200:
                content = resp_200.get("content", {}).get("application/json", {})
                schema = content.get("schema", {})
                if "$ref" in schema:
                    response_type = schema["$ref"].split("/")[-1]
                    response_type = overrides.get("type_renames", {}).get(response_type, response_type)
                    response_type = response_type.replace("models.", "")
                elif schema.get("type") == "array":
                    items = schema.get("items", {})
                    if "$ref" in items:
                        item_type = items["$ref"].split("/")[-1].replace("models.", "")
                        response_type = f"list[{item_type}]"

            path_params = parse_path_params(path)

            methods[method_name] = {
                "http_method": http_method,
                "path": path,
                "path_params": path_params,
                "request_type": request_type,
                "response_type": response_type,
                "description": endpoint_spec.get("description", endpoint_spec.get("summary", "")),
                "tags": endpoint_spec.get("tags", []),
            }

        ir["services"][service_name] = {
            "description": service_def.get("description", ""),
            "methods": methods,
        }

    # Add WebSocket info
    ir["websocket"] = overrides.get("websocket", {})

    return ir


def build_from_files(specs_dir: str, overrides_path: str) -> dict:
    """Convenience: load specs from directory + overrides file → IR."""
    specs_dir = Path(specs_dir)
    specs = {}

    spec_map = {
        "compute-api.json": "compute",
        "agent-registry-api.json": "registry",
        "agentd-api.json": "agentd",
    }

    for filename, key in spec_map.items():
        path = specs_dir / filename
        if path.exists():
            specs[key] = load_spec(str(path))

    with open(overrides_path) as f:
        overrides = json.load(f)

    return build_ir(specs, overrides)


if __name__ == "__main__":
    ir = build_from_files("specs", "generator/overrides.json")
    print(json.dumps(ir, indent=2))
