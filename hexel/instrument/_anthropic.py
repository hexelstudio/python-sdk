"""Auto-instrument Anthropic SDK. Intercepts messages.create to collect telemetry."""
from __future__ import annotations

import time

_instrumented = False

_COST_TABLE = {
    "claude-sonnet-4": (3.00, 15.00),
    "claude-3-7-sonnet": (3.00, 15.00),
    "claude-3-5-sonnet": (3.00, 15.00),
    "claude-3-5-haiku": (0.80, 4.00),
    "claude-3-opus": (15.00, 75.00),
}


def _estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    for prefix, (inp, out) in _COST_TABLE.items():
        if model.startswith(prefix):
            return (input_tokens * inp + output_tokens * out) / 1_000_000
    return 0.0


def _wrap_create(original):
    def wrapper(*args, **kwargs):
        from hexel.instrument._collector import current

        start = time.perf_counter()
        result = original(*args, **kwargs)
        elapsed_ms = int((time.perf_counter() - start) * 1000)

        c = current()
        if c and hasattr(result, "usage") and result.usage:
            c.record_llm(
                model=result.model or kwargs.get("model", "unknown"),
                provider="anthropic",
                input_tokens=result.usage.input_tokens or 0,
                output_tokens=result.usage.output_tokens or 0,
                latency_ms=elapsed_ms,
                cost_usd=_estimate_cost(
                    result.model or kwargs.get("model", ""),
                    result.usage.input_tokens or 0,
                    result.usage.output_tokens or 0,
                ),
            )
        return result
    return wrapper


def _wrap_acreate(original):
    async def wrapper(*args, **kwargs):
        from hexel.instrument._collector import current

        start = time.perf_counter()
        result = await original(*args, **kwargs)
        elapsed_ms = int((time.perf_counter() - start) * 1000)

        c = current()
        if c and hasattr(result, "usage") and result.usage:
            c.record_llm(
                model=result.model or kwargs.get("model", "unknown"),
                provider="anthropic",
                input_tokens=result.usage.input_tokens or 0,
                output_tokens=result.usage.output_tokens or 0,
                latency_ms=elapsed_ms,
                cost_usd=_estimate_cost(
                    result.model or kwargs.get("model", ""),
                    result.usage.input_tokens or 0,
                    result.usage.output_tokens or 0,
                ),
            )
        return result
    return wrapper


def instrument():
    global _instrumented
    if _instrumented:
        return

    try:
        from anthropic.resources.messages import Messages, AsyncMessages

        Messages.create = _wrap_create(Messages.create)
        AsyncMessages.create = _wrap_acreate(AsyncMessages.create)

        _instrumented = True
    except ImportError:
        pass  # anthropic not installed, skip silently
