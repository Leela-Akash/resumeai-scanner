"""Groq chat-completions client with JSON mode, schema validation and retries.

Why this exists: LLM output is untrusted input. Every response is parsed as JSON and
validated against a Pydantic model before the pipeline uses it, so a malformed reply
fails loudly (and gets retried) instead of silently producing a wrong score.
"""
import asyncio
import json
import logging
import os
from typing import TypeVar

import httpx
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
MAX_RETRIES = 3
REQUEST_TIMEOUT = httpx.Timeout(45.0, connect=10.0)

T = TypeVar("T", bound=BaseModel)


class LLMError(Exception):
    """Raised when the LLM can't produce a usable answer after all retries."""


_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    # One pooled client for the whole process instead of a new TCP/TLS handshake per call.
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(timeout=REQUEST_TIMEOUT)
    return _client


async def close_client() -> None:
    global _client
    if _client is not None and not _client.is_closed:
        await _client.aclose()
    _client = None


def _api_key() -> str:
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise LLMError("GROQ_API_KEY is not set")
    return key


def parse_json_object(raw: str) -> dict:
    """Parse a JSON object, tolerating markdown fences around it."""
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    text = text.strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end <= start:
            raise
        data = json.loads(text[start : end + 1])
    if not isinstance(data, dict):
        raise json.JSONDecodeError("expected a JSON object", text, 0)
    return data


def _backoff(attempt: int) -> float:
    return min(2**attempt, 8)


async def _post(payload: dict) -> str:
    """POST to Groq with retries on rate limits, 5xx and network errors."""
    headers = {"Authorization": f"Bearer {_api_key()}", "Content-Type": "application/json"}
    last_error = "unknown error"
    for attempt in range(MAX_RETRIES):
        try:
            response = await _get_client().post(GROQ_API_URL, headers=headers, json=payload)
        except httpx.HTTPError as e:
            last_error = f"network error: {type(e).__name__}"
            logger.warning("Groq %s (attempt %d)", last_error, attempt + 1)
            await asyncio.sleep(_backoff(attempt))
            continue

        if response.status_code == 200:
            try:
                return response.json()["choices"][0]["message"]["content"]
            except (KeyError, IndexError, ValueError):
                last_error = "unexpected response shape"
        elif response.status_code == 429 or response.status_code >= 500:
            last_error = f"HTTP {response.status_code}"
            retry_after = response.headers.get("retry-after")
            delay = float(retry_after) if retry_after and retry_after.isdigit() else _backoff(attempt)
            logger.warning("Groq %s, retrying in %.1fs", last_error, delay)
            await asyncio.sleep(min(delay, 10))
            continue
        else:
            # 4xx (bad key, bad request) won't fix itself on retry. Log details, raise a generic error.
            logger.error("Groq HTTP %d: %s", response.status_code, response.text[:300])
            raise LLMError(f"AI provider rejected the request (HTTP {response.status_code})")
    raise LLMError(f"AI provider unavailable after {MAX_RETRIES} attempts ({last_error})")


async def complete_json(
    system: str,
    user: str,
    model: type[T],
    *,
    temperature: float = 0.2,
    max_tokens: int = 1500,
) -> T:
    """Ask for a JSON object and validate it against `model`. Retries once on invalid JSON/schema."""
    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
    }
    last_error: Exception | None = None
    for _ in range(2):
        raw = await _post(payload)
        try:
            return model.model_validate(parse_json_object(raw))
        except (json.JSONDecodeError, ValidationError) as e:
            last_error = e
            logger.warning("LLM output failed validation for %s: %s", model.__name__, str(e)[:200])
    raise LLMError(f"AI returned invalid {model.__name__}: {last_error}")


async def complete_text(system: str, user: str, *, temperature: float = 0.5, max_tokens: int = 500) -> str:
    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    return (await _post(payload)).strip()
