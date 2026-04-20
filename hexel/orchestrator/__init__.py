"""Hexel Orchestrator — fleet management, task execution, streaming."""
from hexel.orchestrator._fleet import FleetClient
from hexel.orchestrator._task import TaskClient

__all__ = ["OrchestratorClient", "FleetClient", "TaskClient"]


class OrchestratorClient:
    """Manage agent fleets and execute tasks."""

    def __init__(self, http):
        self.fleet = FleetClient(http)
        self.task = TaskClient(http)
