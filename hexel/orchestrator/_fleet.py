"""Fleet management — create fleets, add agents."""
from __future__ import annotations
from hexel._internal.http import HttpClient


class FleetClient:
    """Manage agent fleets."""

    def __init__(self, http: HttpClient):
        self._http = http

    def create(self, *, name: str, environment_id: str, workspace_id: str, description: str = "", config: str = "{}") -> dict:
        """Create a new fleet."""
        resp = self._http.post("/orchestrator/v1/fleets", json={
            "name": name, "environment_id": environment_id,
            "workspace_id": workspace_id, "description": description, "config": config,
        })
        resp.raise_for_status()
        return resp.json()

    def list(self, *, environment_id: str) -> list[dict]:
        """List fleets in an environment."""
        resp = self._http.get("/orchestrator/v1/fleets", params={"environment_id": environment_id})
        resp.raise_for_status()
        return resp.json().get("fleets", [])

    def get(self, fleet_id: str) -> dict:
        """Get fleet details."""
        resp = self._http.get(f"/orchestrator/v1/fleets/{fleet_id}")
        resp.raise_for_status()
        return resp.json()

    def add_agent(self, fleet_id: str, *, agent_id: str, name: str, endpoint: str, capabilities: list[str] | None = None, description: str = "") -> dict:
        """Add an agent to a fleet."""
        resp = self._http.post(f"/orchestrator/v1/fleets/{fleet_id}/agents", json={
            "agent_id": agent_id, "name": name, "endpoint": endpoint,
            "capabilities": capabilities or [], "description": description,
        })
        resp.raise_for_status()
        return resp.json()

    def list_agents(self, fleet_id: str) -> list[dict]:
        """List agents in a fleet."""
        resp = self._http.get(f"/orchestrator/v1/fleets/{fleet_id}/agents")
        resp.raise_for_status()
        return resp.json().get("agents", [])
