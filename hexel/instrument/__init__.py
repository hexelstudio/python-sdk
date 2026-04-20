"""Hexel Instrumentation — auto-instrument LLM providers.

Usage:
    from hexel.instrument import init
    init()

    # All OpenAI/Anthropic calls are now auto-tracked.
    # Use collector for per-request scoping:

    from hexel.instrument import start_request, finish_request

    telemetry = start_request()       # Start collecting
    # ... your agent code, LLM calls happen here ...
    hexel_data = finish_request()     # Get collected telemetry as dict
"""
from hexel.instrument._openai import instrument as _instrument_openai
from hexel.instrument._anthropic import instrument as _instrument_anthropic
from hexel.instrument._collector import start as start_request
from hexel.instrument._collector import flush as finish_request
from hexel.instrument._collector import current as current_collector

_initialized = False


def init():
    """Instrument all supported LLM providers. Call once at agent startup."""
    global _initialized
    if _initialized:
        return
    _instrument_openai()
    _instrument_anthropic()
    _initialized = True


__all__ = ["init", "start_request", "finish_request", "current_collector"]
