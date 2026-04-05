"""WebSocket client for sandbox execution."""
from __future__ import annotations
import json
from websockets.sync.client import connect


class WSConnection:
    """Persistent WebSocket connection to a sandbox's agentd."""

    def __init__(self, ws_url: str, token: str):
        self._ws = connect(ws_url, additional_headers={"Authorization": f"Bearer {token}"})
        msg = json.loads(self._ws.recv())
        self.context_id = msg.get("data", "")

    def execute(self, code: str, language: str = "python") -> dict:
        """Execute code on the pre-warmed kernel."""
        self._ws.send(json.dumps({
            "type": "execute",
            "code": code,
            "language": language,
            "context_id": self.context_id,
        }))
        return self._collect()

    def command(self, cmd: str) -> dict:
        """Run a shell command."""
        self._ws.send(json.dumps({"type": "command", "command": cmd}))
        return self._collect()

    def _collect(self) -> dict:
        output_lines = []
        status = "ok"
        while True:
            raw = self._ws.recv()
            msg = json.loads(raw)
            t = msg.get("type", "")
            d = msg.get("data", "")
            if t in ("stdout", "output"):
                output_lines.append(d)
            elif t == "stderr":
                output_lines.append(d)
            elif t == "started":
                continue
            elif t == "error":
                status = "error"
                output_lines.append(d)
                break
            elif t in ("done", "execution_complete"):
                break
        return {"output": "\n".join(output_lines), "status": status}

    def close(self):
        try:
            self._ws.close()
        except Exception:
            pass
