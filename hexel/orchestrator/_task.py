"""Task execution — submit, stream, get results."""
from __future__ import annotations
import json
from typing import Generator
from hexel._internal.http import HttpClient


class TaskEvent:
    """A single SSE event from task execution."""
    __slots__ = ("type", "data", "raw")

    def __init__(self, type: str, data: dict, raw: str = ""):
        self.type = type
        self.data = data
        self.raw = raw

    def __repr__(self):
        return f"TaskEvent(type={self.type!r}, data={self.data!r})"


class TaskResult:
    """Completed task with execution trail."""

    def __init__(self, data: dict):
        self._data = data
        self.id = data.get("id", "")
        self.status = data.get("status", "")
        self.input = data.get("input", "")
        self.error = data.get("error")
        self.fleet_id = data.get("fleet_id", "")
        self.created_at = data.get("created_at", "")

        result_raw = data.get("result")
        if isinstance(result_raw, str):
            try:
                result_raw = json.loads(result_raw)
            except (json.JSONDecodeError, TypeError):
                result_raw = None
        self._result = result_raw or {}
        self.workflow_id = self._result.get("workflow_id", "")
        self.nodes = [NodeResult(n) for n in self._result.get("nodes", [])]

    def __repr__(self):
        return f"TaskResult(id={self.id!r}, status={self.status!r}, nodes={len(self.nodes)})"


class NodeResult:
    """Single node execution result."""

    def __init__(self, data: dict):
        self._data = data
        self.node_id = data.get("node_id", "")
        self.agent_id = data.get("agent_id", "")
        self.status = data.get("status", "")
        self.started_at = data.get("started_at")
        self.completed_at = data.get("completed_at")
        self.tokens_used = data.get("tokens_used", 0)
        self.error = data.get("error")

        output = data.get("output", {}) or {}
        self.result = output.get("result")
        telemetry = output.get("telemetry", {}) or {}
        self.artifacts = telemetry.get("artifacts", [])
        self.llm_calls = telemetry.get("llm_calls", [])
        self.trace = telemetry.get("trace", [])

    @property
    def output_text(self) -> str:
        """Best-effort text representation of the agent output."""
        if self.artifacts:
            return self.artifacts[0].get("content", "")
        if isinstance(self.result, str):
            return self.result
        if isinstance(self.result, dict):
            return self.result.get("report", self.result.get("summary", json.dumps(self.result, indent=2)))
        return str(self.result) if self.result else ""

    def __repr__(self):
        return f"NodeResult(node_id={self.node_id!r}, agent_id={self.agent_id[:8]!r}, status={self.status!r})"


class TaskClient:
    """Submit tasks and stream execution."""

    def __init__(self, http: HttpClient):
        self._http = http

    def submit(self, *, fleet_id: str, goal: str, environment_id: str, workspace_id: str, context: str = "{}") -> TaskResult:
        """Submit a task to a fleet. Returns immediately with task ID."""
        resp = self._http.post("/orchestrator/v1/tasks", json={
            "fleet_id": fleet_id, "environment_id": environment_id,
            "workspace_id": workspace_id, "input": goal, "context": context,
        })
        resp.raise_for_status()
        return TaskResult(resp.json())

    def get(self, task_id: str) -> TaskResult:
        """Get task details including execution trail."""
        resp = self._http.get(f"/orchestrator/v1/tasks/{task_id}")
        resp.raise_for_status()
        return TaskResult(resp.json())

    def list(self, *, fleet_id: str) -> list[TaskResult]:
        """List tasks for a fleet."""
        resp = self._http.get("/orchestrator/v1/tasks", params={"fleet_id": fleet_id})
        resp.raise_for_status()
        return [TaskResult(t) for t in resp.json().get("tasks", [])]

    def stream(self, task_id: str, *, timeout: float = 300) -> Generator[TaskEvent, None, None]:
        """Stream task execution events via SSE. Yields TaskEvent objects.

        Usage:
            task = client.orchestrator.task.submit(fleet_id="...", goal="...")
            for event in client.orchestrator.task.stream(task.id):
                print(f"{event.type}: {event.data}")
                if event.type == "node.output":
                    print(f"  Agent {event.data.get('node_id')} completed")
        """
        import httpx

        url = f"{self._http._base_url}/orchestrator/v1/tasks/{task_id}/stream"
        headers = {"Authorization": f"Bearer {self._http._auth.token}", "Accept": "text/event-stream"}

        with httpx.stream("GET", url, headers=headers, timeout=timeout) as resp:
            resp.raise_for_status()
            event_type = ""
            for line in resp.iter_lines():
                if line.startswith("event:"):
                    event_type = line[6:].strip()
                elif line.startswith("data:"):
                    raw = line[5:].strip()
                    try:
                        data = json.loads(raw)
                    except (json.JSONDecodeError, TypeError):
                        data = {"raw": raw}
                    yield TaskEvent(type=event_type, data=data, raw=raw)
                    if event_type in ("task.complete", "task.failed", "task.cancelled"):
                        return

    def wait(self, task_id: str, *, poll_interval: float = 2.0, timeout: float = 300) -> TaskResult:
        """Poll until task completes. Returns full result with execution trail."""
        import time
        deadline = time.time() + timeout
        while time.time() < deadline:
            result = self.get(task_id)
            if result.status in ("completed", "failed", "cancelled"):
                return result
            time.sleep(poll_interval)
        raise TimeoutError(f"Task {task_id} did not complete within {timeout}s")

    def run(self, *, fleet_id: str, goal: str, environment_id: str, workspace_id: str, timeout: float = 300) -> TaskResult:
        """Submit a task and wait for completion. Returns full execution trail.

        Usage:
            result = client.orchestrator.task.run(
                fleet_id="...", goal="Research AI trends", environment_id="...", workspace_id="..."
            )
            print(f"Status: {result.status}")
            for node in result.nodes:
                print(f"  {node.node_id}: {node.output_text[:100]}")
        """
        task = self.submit(fleet_id=fleet_id, goal=goal, environment_id=environment_id, workspace_id=workspace_id)
        return self.wait(task.id, timeout=timeout)
