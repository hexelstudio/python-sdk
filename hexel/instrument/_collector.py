"""Per-request telemetry collector. Uses contextvars for request-scoped collection."""
from __future__ import annotations

from contextvars import ContextVar

_current: ContextVar["Collector | None"] = ContextVar("hexel_collector", default=None)


class Collector:
    def __init__(self):
        self.llm_calls: list[dict] = []
        self.tool_calls: list[dict] = []
        self.trace: list[dict] = []

    def record_llm(self, *, model: str, provider: str, input_tokens: int,
                   output_tokens: int, latency_ms: int = 0, cost_usd: float = 0.0):
        self.llm_calls.append({
            "model": model, "provider": provider,
            "input_tokens": input_tokens, "output_tokens": output_tokens,
            "latency_ms": latency_ms, "cost_usd": cost_usd,
        })
        self.trace.append({"action": "llm", "model": model, "duration_ms": latency_ms})

    def record_tool(self, *, tool: str, status: str = "success",
                    input: str | None = None, latency_ms: int = 0):
        self.tool_calls.append({"tool": tool, "status": status, "input": input, "latency_ms": latency_ms})
        self.trace.append({"action": "tool", "tool": tool, "duration_ms": latency_ms})

    def to_dict(self) -> dict | None:
        d = {}
        if self.llm_calls:
            d["llm_calls"] = self.llm_calls
        if self.tool_calls:
            d["tool_calls"] = self.tool_calls
        if self.trace:
            d["trace"] = self.trace
        return d or None


def start() -> Collector:
    c = Collector()
    _current.set(c)
    return c


def current() -> Collector | None:
    return _current.get()


def flush() -> dict | None:
    c = _current.get()
    if c is None:
        return None
    _current.set(None)
    return c.to_dict()
