from __future__ import annotations
from hexel._internal.auth import AuthManager
from hexel._internal.http import HttpClient
from hexel.compute import ComputeClient
from hexel.orchestrator import OrchestratorClient


class Hexel:
    """
    Hexel SDK client.

    Usage:
        from hexel import Hexel

        client = Hexel(api_key="studio_live_xxxx")

        # Compute — deploy agents and run sandboxes
        sandbox = client.compute.sandbox.create(tier="standard")

        # Orchestrator — manage fleets and execute tasks
        task = client.orchestrator.task.submit(
            fleet_id="...", goal="Research AI trends",
            environment_id="...", workspace_id="..."
        )
        for event in client.orchestrator.task.stream(task.id):
            print(f"{event.type}: {event.data}")
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        base_url: str = "https://api.hexelstudio.com",
        compute_url: str = "https://compute.hexelstudio.com",
        registry_url: str = "https://api.hexelstudio.com",
        sts_url: str = "https://sts.hexelstudio.com",
        timeout: float = 30.0,
    ):
        self._auth = AuthManager(
            api_key=api_key,
            client_id=client_id,
            client_secret=client_secret,
            sts_url=sts_url,
        )
        api_http = HttpClient(base_url=base_url, auth=self._auth, timeout=timeout)
        compute_http = HttpClient(base_url=compute_url, auth=self._auth, timeout=timeout)
        registry_http = HttpClient(base_url=registry_url, auth=self._auth, timeout=timeout)
        self.compute = ComputeClient(compute_http, registry_http)
        self.orchestrator = OrchestratorClient(api_http)
