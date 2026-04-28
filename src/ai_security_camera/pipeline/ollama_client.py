"""Ollama HTTP client for JSON-constrained VLM output."""

from __future__ import annotations

import json
import re
from typing import Any

import httpx

from ai_security_camera.domain.vlm_schema import VlmStructuredResponse, validate_vlm_payload


class OllamaError(Exception):
    pass


def _extract_json_object(text: str) -> dict[str, Any] | None:
    """Parse first JSON object from model text (tolerate markdown fences)."""
    t = text.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", t, re.DOTALL)
    if fence:
        t = fence.group(1)
    try:
        data = json.loads(t)
    except json.JSONDecodeError:
        return None
    if isinstance(data, dict):
        return data
    return None


class OllamaClient:
    def __init__(
        self,
        base_url: str,
        model: str,
        *,
        timeout: float = 120.0,
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._own_client = client is None
        self._client = client or httpx.Client(timeout=timeout)

    def close(self) -> None:
        if self._own_client:
            self._client.close()

    def __enter__(self) -> OllamaClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def chat_json(
        self,
        messages: list[dict[str, Any]],
        *,
        images: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Call Ollama /api/chat with format=json. If `images` is set, attaches to last user message.
        Returns parsed assistant JSON dict or raises OllamaError.
        """
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "format": "json",
        }
        if images:
            if not messages:
                msg = "messages required when passing images"
                raise ValueError(msg)
            last = messages[-1].copy()
            last["images"] = images
            payload["messages"] = messages[:-1] + [last]

        r = self._client.post(f"{self.base_url}/api/chat", json=payload)
        if r.status_code >= 400:
            raise OllamaError(f"Ollama HTTP {r.status_code}: {r.text}")
        body = r.json()
        content = body.get("message", {}).get("content")
        if not isinstance(content, str):
            raise OllamaError("Missing message.content in Ollama response")
        parsed = _extract_json_object(content)
        if parsed is None:
            raise OllamaError("Assistant content is not valid JSON object")
        return parsed

    def complete_vlm(
        self,
        *,
        system: str,
        user: str,
        images: list[str] | None = None,
        max_retries: int = 1,
    ) -> VlmStructuredResponse | None:
        """
        Request structured VLM output; validate schema (VLM-022).
        Retries once if JSON invalid (caller may adjust prompt later).
        """
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        last_err: Exception | None = None
        for _ in range(max_retries + 1):
            try:
                raw = self.chat_json(messages, images=images)
            except (OllamaError, httpx.HTTPError) as e:
                last_err = e
                break
            validated = validate_vlm_payload(raw)
            if validated is not None:
                return validated
            last_err = OllamaError("Schema validation failed")
        if last_err:
            raise last_err
        return None
