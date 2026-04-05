"""WebSocket client for sandbox execution."""
from __future__ import annotations
import json
from websockets.sync.client import connect
from hexel._internal.auth import AuthManager


class WSConnection:
    """Persistent WebSocket connection to a sandbox's agentd."""

    def __init__(self, url: str, auth: AuthManager):
        self._ws = connect(url, additional_headers={"Authorization": f"Bearer {auth.token}"})
        msg = json.loads(self._ws.recv())
        self.context_id = msg.get("data", "")

    def send(self, msg: dict) -> list[dict]:
        self._ws.send(json.dumps(msg))
        results = []
        while True:
            data = json.loads(self._ws.recv())
            results.append(data)
            if data.get("type") in ("done", "execution_complete", "error"):
                break
        return results

    def close(self):
        try:
            self._ws.close()
        except Exception:
            pass
