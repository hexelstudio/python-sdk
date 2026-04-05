from __future__ import annotations
from hexel._internal.auth import AuthManager
from hexel._internal.http import HttpClient
from hexel.compute import ComputeClient


class Hexel:
    """
    Hexel SDK client.

    Usage:
        from hexel import Hexel

        client = Hexel(api_key="studio_live_xxxx")
        sandbox = client.compute.sandbox.create(tier="standard")
        result = sandbox.execute("print(1 + 1)")
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        base_url: str = "https://compute.hexelstudio.com",
        sts_url: str = "https://sts.hexelstudio.com",
        timeout: float = 30.0,
    ):
        self._auth = AuthManager(
            api_key=api_key,
            client_id=client_id,
            client_secret=client_secret,
            sts_url=sts_url,
        )
        self._http = HttpClient(base_url=base_url, auth=self._auth, timeout=timeout)
        self.compute = ComputeClient(self._http)
