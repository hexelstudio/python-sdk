"""Auto-instrument OpenAI SDK. Intercepts chat.completions.create to collect telemetry."""
from __future__ import annotations

import time

_original_create = None
_original_acreate = None
_instrumented = False

# Rough cost per 1M tokens (USD) — updated periodically
_COST_TABLE = {
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4-turbo": (10.00, 30.00),
    "gpt-4": (30.00, 60.00),
    "gpt-3.5-turbo": (0.50, 1.50),
    "o1": (15.00, 60.00),
    "o1-mini": (3.00, 12.00),
    "o3-mini": (1.10, 4.40),
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
                provider="openai",
                input_tokens=result.usage.prompt_tokens or 0,
                output_tokens=result.usage.completion_tokens or 0,
                latency_ms=elapsed_ms,
                cost_usd=_estimate_cost(
                    result.model or kwargs.get("model", ""),
                    result.usage.prompt_tokens or 0,
                    result.usage.completion_tokens or 0,
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
                provider="openai",
                input_tokens=result.usage.prompt_tokens or 0,
                output_tokens=result.usage.completion_tokens or 0,
                latency_ms=elapsed_ms,
                cost_usd=_estimate_cost(
                    result.model or kwargs.get("model", ""),
                    result.usage.prompt_tokens or 0,
                    result.usage.completion_tokens or 0,
                ),
            )
        return result
    return wrapper


def instrument():
    global _original_create, _original_acreate, _instrumented
    if _instrumented:
        return

    try:
        from openai.resources.chat.completions import Completions, AsyncCompletions

        _original_create = Completions.create
        Completions.create = _wrap_create(_original_create)

        _original_acreate = AsyncCompletions.create
        AsyncCompletions.create = _wrap_acreate(_original_acreate)

        _instrumented = True
    except ImportError:
        pass  # openai not installed, skip silently
