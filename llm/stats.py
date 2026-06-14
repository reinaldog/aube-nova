"""Global LLM usage statistics — updated by client.py on every API call."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

MODEL_ID = "openbmb/MiniCPM4.1-8B"
MODEL_SHORT = "MiniCPM4.1-8B"


def _resolve_provider() -> tuple[str, str]:
    """Return (model_short, provider) from the active client config."""
    try:
        from llm.client import ACTIVE_MODEL_SHORT, ACTIVE_PROVIDER

        return ACTIVE_MODEL_SHORT, ACTIVE_PROVIDER
    except Exception:
        return MODEL_SHORT, "HuggingFace Inference API"


_model_short, _provider = _resolve_provider()


@dataclass
class LLMStats:
    model_id: str = MODEL_ID
    model_short: str = field(default_factory=lambda: _model_short)
    provider: str = field(default_factory=lambda: _provider)
    total_calls: int = 0
    successful_calls: int = 0
    fallback_calls: int = 0
    error_calls: int = 0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    last_latency_ms: float = 0.0
    _latency_sum: float = field(default=0.0, repr=False)
    _latency_count: int = field(default=0, repr=False)
    last_error: str = ""
    session_start: float = field(default_factory=time.time)
    has_token: bool = False

    @property
    def total_tokens(self) -> int:
        return self.total_prompt_tokens + self.total_completion_tokens

    @property
    def avg_latency_ms(self) -> float:
        return (
            self._latency_sum / self._latency_count if self._latency_count > 0 else 0.0
        )

    @property
    def session_minutes(self) -> float:
        return (time.time() - self.session_start) / 60.0

    @property
    def success_rate_pct(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return self.successful_calls / self.total_calls * 100.0


_stats = LLMStats()


def get_stats() -> LLMStats:
    return _stats


def record_call(
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    latency_ms: float = 0.0,
    is_error: bool = False,
    is_fallback: bool = False,
) -> None:
    _stats.total_calls += 1
    if is_error:
        _stats.error_calls += 1
    elif is_fallback:
        _stats.fallback_calls += 1
    else:
        _stats.successful_calls += 1
    _stats.total_prompt_tokens += prompt_tokens
    _stats.total_completion_tokens += completion_tokens
    _stats.last_latency_ms = latency_ms
    if latency_ms > 0:
        _stats._latency_sum += latency_ms
        _stats._latency_count += 1
