# Hexel Python SDK

The official Python SDK for [Hexel Compute](https://hexelstudio.com) — deploy and run AI agents with sub-millisecond latency.

## Install

```bash
pip install hexel
```

## Quick Start

```python
from hexel import Hexel

client = Hexel(api_key="your_api_key")

# Create a sandbox and execute code
sandbox = client.compute.sandbox.create(tier="standard")
print(sandbox)  # {"vm_id": "...", "state": "allocated", ...}

# Register an agent
agent = client.compute.agent.register(
    name="my-agent",
    image="ghcr.io/org/agent:v1",
    capabilities=["chat", "streaming"],
)

# Deploy an agent
instance = client.compute.instance.deploy(agent["id"], env={"MODEL": "gpt-4"})
print(instance["endpoint"])  # https://zeal-isle-a620.compute.hexelstudio.com
```

## Authentication

Two authentication methods are supported:

```python
# API Key (recommended for development)
client = Hexel(api_key="studio_live_xxxx")

# OAuth Client Credentials (recommended for production)
client = Hexel(client_id="your_client_id", client_secret="your_client_secret")
```

Both methods exchange credentials for a short-lived STS token automatically. Tokens are cached and refreshed transparently.

## Sandboxes

Sandboxes are isolated execution environments allocated instantly.

```python
# Create
sandbox = client.compute.sandbox.create(tier="standard")

# Execute code (HTTP)
result = client.compute.sandbox.execute(sandbox["vm_id"], code="print(1+1)", language="python")

# List
sandboxes = client.compute.sandbox.list()

# Renew TTL
client.compute.sandbox.renew(sandbox["vm_id"], ttl_seconds=3600)

# Release
client.compute.sandbox.release(sandbox["vm_id"], recycle=True)

# Delete
client.compute.sandbox.delete(sandbox["vm_id"])
```

## Agents

Agents are Docker images registered in the Hexel registry.

```python
# Register
agent = client.compute.agent.register(
    name="fraud-detector",
    image="ghcr.io/org/fraud-agent:v1",
    capabilities=["fraud-detection"],
)

# List
agents = client.compute.agent.list()

# Get
agent = client.compute.agent.get("agent-id")

# Search
results = client.compute.agent.search(q="fraud")

# Delete
client.compute.agent.delete("agent-id")
```

## Instances

Instances are running deployments of agents with permanent endpoints.

```python
# Deploy
instance = client.compute.instance.deploy("agent-id", env={"MODEL": "gpt-4"})

# List
instances = client.compute.instance.list()

# Get
instance = client.compute.instance.get("deployment-id")

# Stop
client.compute.instance.stop("deployment-id")

# Redeploy
client.compute.instance.redeploy("deployment-id")

# Delete
client.compute.instance.delete("deployment-id")
```

## Configuration

```python
client = Hexel(
    api_key="...",
)
```

## Requirements

- Python 3.10+
- `httpx` for HTTP
- `websockets` for WebSocket connections

## License

MIT
