"""Hexel response helpers — format agent responses with telemetry.

Usage:
    from hexel.instrument import init, start_request, finish_request
    from hexel.response import hexel_response

    init()

    async def handle(input_data):
        start_request()
        # ... your agent code, LLM calls auto-tracked ...
        result = {"answer": "..."}
        return hexel_response(result, artifacts=[{"name": "report.md", "type": "document", "content": "..."}])
"""
from __future__ import annotations

from typing import Any

from hexel.instrument._collector import flush


def hexel_response(result: Any, artifacts: list[dict] | None = None) -> dict:
    """Build an agent protocol response. Auto-attaches collected telemetry."""
    response = {"result": result}
    telemetry = flush() or {}
    if artifacts:
        telemetry["artifacts"] = artifacts
    if telemetry:
        response["telemetry"] = telemetry
    return response
