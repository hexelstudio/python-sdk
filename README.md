# Hexel Python SDK

## Structure

```
hexel/                  ← published package (pip install hexel)
  __init__.py           ← from hexel import Hexel
  _internal/            ← hand-written runtime
    auth.py             ← token management
    http.py             ← request pipeline (retries, auth)
    ws.py               ← WebSocket client
  compute/              ← GENERATED from specs
    __init__.py
    sandbox.py
    agent.py
    instance.py
    types.py

generator/              ← the SDK generator
  generate.py           ← main entry point
  parser.py             ← OpenAPI spec → IR
  overrides.json        ← DX decisions (naming, grouping)
  templates/            ← Jinja2 templates
    service.py.j2
    types.py.j2
    __init__.py.j2

specs/                  ← source OpenAPI specs (copied from product repos)
  compute-api.json
  agentd-api.json
  agent-registry-api.json
```

## Generate

```bash
python generator/generate.py
```

## Usage

```python
from hexel import Hexel

client = Hexel(api_key="studio_live_xxxx")

# Sandbox
sandbox = client.compute.sandbox.create(tier="standard")
result = sandbox.execute("print(1 + 1)")
print(result.output)
sandbox.close()

# Agent
agent = client.compute.agent.register(name="my-agent", image="ghcr.io/org/agent:v1")
instance = client.compute.instance.deploy(agent["id"], env={"MODEL": "gpt-4"})
for chunk in instance.stream("Hello"):
    print(chunk, end="")
```
