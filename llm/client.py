import asyncio
import os
import time

import httpx
from dotenv import load_dotenv

load_dotenv()
HF_TOKEN = os.environ.get("HF_TOKEN", "")

# Free API takes priority when configured (FREE_API_URL + FREE_API_TOKEN)
FREE_API_URL = os.environ.get("FREE_API_URL", "").rstrip("/")
FREE_API_TOKEN = os.environ.get("FREE_API_TOKEN", "")

HF_INFERENCE_URL = "https://api-inference.huggingface.co/v1/chat/completions"
MODEL_ID = "openbmb/MiniCPM4.1-8B"

# Resolve active endpoint and token at import time
if FREE_API_URL and FREE_API_TOKEN:
    _ACTIVE_URL = FREE_API_URL + "/v1/chat/completions"
    _ACTIVE_TOKEN = FREE_API_TOKEN
    _ACTIVE_MODEL = "MiniCPM4.1-8B"  # model name used by free vLLM server
    _ACTIVE_PROVIDER = "Free Inference API"
else:
    _ACTIVE_URL = HF_INFERENCE_URL
    _ACTIVE_TOKEN = HF_TOKEN
    _ACTIVE_MODEL = MODEL_ID
    _ACTIVE_PROVIDER = "HuggingFace Inference API"

# Expose for stats module
ACTIVE_PROVIDER = _ACTIVE_PROVIDER
ACTIVE_MODEL_SHORT = _ACTIVE_MODEL.split("/")[-1]

_MAX_RETRIES = 3
_RETRY_DELAYS = [1.0, 3.0, 6.0]


# Lazy import to avoid circular dependency
def _record(
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    latency_ms: float = 0.0,
    is_error: bool = False,
    is_fallback: bool = False,
) -> None:
    try:
        from llm.stats import _stats, record_call

        _stats.has_token = bool(_ACTIVE_TOKEN)
        record_call(prompt_tokens, completion_tokens, latency_ms, is_error, is_fallback)
    except Exception:
        pass


async def call_llm(system: str, user: str, max_tokens: int = 100) -> str:
    if not _ACTIVE_TOKEN:
        _record(is_fallback=True)
        return "[no API token set]"

    headers = {
        "Authorization": f"Bearer {_ACTIVE_TOKEN}",
        "Content-Type": "application/json",
    }
    payload: dict = {
        "model": _ACTIVE_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.85,
    }
    # Disable chain-of-thought on vLLM-hosted MiniCPM reasoning models
    if FREE_API_URL and FREE_API_TOKEN:
        payload["chat_template_kwargs"] = {"enable_thinking": False}

    last_error = "unknown"
    for attempt in range(_MAX_RETRIES):
        t0 = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=35.0) as client:
                r = await client.post(_ACTIVE_URL, headers=headers, json=payload)
                r.raise_for_status()
                latency_ms = (time.perf_counter() - t0) * 1000
                data = r.json()
                usage = data.get("usage", {})
                _record(
                    prompt_tokens=usage.get("prompt_tokens", 0),
                    completion_tokens=usage.get("completion_tokens", 0),
                    latency_ms=latency_ms,
                )
                content = data["choices"][0]["message"]["content"]
                # Strip <think>...</think> blocks emitted by reasoning models
                import re as _re

                content = _re.sub(r"<think>.*?</think>", "", content, flags=_re.DOTALL)
                return content.strip()
        except httpx.ConnectError:
            last_error = "connection_error"
            if attempt < _MAX_RETRIES - 1:
                await asyncio.sleep(_RETRY_DELAYS[attempt])
        except httpx.TimeoutException:
            last_error = "timeout"
            if attempt < _MAX_RETRIES - 1:
                await asyncio.sleep(_RETRY_DELAYS[attempt])
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                last_error = "rate_limited"
                await asyncio.sleep(5.0 + attempt * 3.0)
            else:
                latency_ms = (time.perf_counter() - t0) * 1000
                _record(latency_ms=latency_ms, is_error=True)
                return f"[HTTP {e.response.status_code}]"
        except Exception as e:
            latency_ms = (time.perf_counter() - t0) * 1000
            _record(latency_ms=latency_ms, is_error=True)
            return f"[LLM error: {type(e).__name__}]"

    _record(is_error=True)
    return f"[{last_error} after {_MAX_RETRIES} retries]"
