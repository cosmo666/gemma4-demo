import json

import httpx
import pytest

from app.llm.client import LLMClient, SchemaRetryError
from app.llm.schemas import ClassifyDocument


class FakeTransport(httpx.BaseTransport):
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def handle_request(self, request):
        self.calls.append(json.loads(request.content))
        body = self.responses.pop(0)
        return httpx.Response(200, json=body)


def _ollama_response(content: str) -> dict:
    return {"message": {"role": "assistant", "content": content}, "done": True}


def test_generate_structured_parses_valid_json():
    good = json.dumps(
        {
            "bank": "sbi",
            "period_start": "2026-01-01",
            "period_end": "2026-01-31",
            "confidence": 0.9,
            "reason": "logo",
        }
    )
    transport = FakeTransport([_ollama_response(good)])
    client = LLMClient(
        base_url="http://fake", model="test", transport=transport, max_retries=3
    )
    result = client.generate_structured(
        prompt="classify this", schema=ClassifyDocument, images=None
    )
    assert isinstance(result, ClassifyDocument)
    assert result.bank == "sbi"
    assert len(transport.calls) == 1


def test_generate_structured_retries_on_bad_json():
    bad = "not json at all"
    good = json.dumps(
        {
            "bank": "hdfc",
            "period_start": "2026-02-01",
            "period_end": "2026-02-28",
            "confidence": 0.8,
            "reason": "",
        }
    )
    transport = FakeTransport([_ollama_response(bad), _ollama_response(good)])
    client = LLMClient(
        base_url="http://fake", model="test", transport=transport, max_retries=3
    )
    result = client.generate_structured(prompt="classify", schema=ClassifyDocument)
    assert result.bank == "hdfc"
    assert len(transport.calls) == 2


def test_generate_structured_raises_after_max_retries():
    transport = FakeTransport([_ollama_response("nope")] * 3)
    client = LLMClient(
        base_url="http://fake", model="test", transport=transport, max_retries=3
    )
    with pytest.raises(SchemaRetryError):
        client.generate_structured(prompt="classify", schema=ClassifyDocument)
    assert len(transport.calls) == 3
