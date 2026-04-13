from __future__ import annotations

import json
import re
from typing import TypeVar

import httpx
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)

_JSON_BLOCK = re.compile(r"\{[\s\S]*\}")


class SchemaRetryError(RuntimeError):
    pass


class LLMClient:
    def __init__(
        self,
        base_url: str,
        model: str,
        transport: httpx.BaseTransport | None = None,
        max_retries: int = 3,
        timeout: float = 120.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._max_retries = max_retries
        self._client = httpx.Client(
            base_url=self._base_url, transport=transport, timeout=timeout
        )

    def close(self) -> None:
        self._client.close()

    def _chat(self, messages: list[dict], images: list[str] | None = None) -> str:
        payload = {"model": self._model, "messages": messages, "stream": False}
        if images:
            messages[-1]["images"] = images
        r = self._client.post("/api/chat", json=payload)
        r.raise_for_status()
        data = r.json()
        return data["message"]["content"]

    def generate_structured(
        self,
        prompt: str,
        schema: type[T],
        images: list[str] | None = None,
        system: str | None = None,
    ) -> T:
        messages: list[dict] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        last_error: Exception | None = None
        for _ in range(self._max_retries):
            try:
                content = self._chat(messages, images=images)
                json_text = _extract_json_text(content)
                return schema.model_validate_json(json_text)
            except (json.JSONDecodeError, ValidationError, ValueError) as e:
                last_error = e
        raise SchemaRetryError(f"schema validation failed after retries: {last_error}")


def _extract_json_text(text: str) -> str:
    m = _JSON_BLOCK.search(text)
    if not m:
        raise ValueError(f"no JSON object in response: {text[:120]!r}")
    return m.group(0)
