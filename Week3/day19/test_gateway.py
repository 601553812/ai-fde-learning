"""Assistant tests: adapted from Day16, including actual HTTPX failure behavior."""

import json
import httpx
import pytest
from Week3.day19.gemini_gateway import GeminiGateway, TIMEOUT_SECONDS
from Week3.day19.prompt import build_request


def test_copied_request_retains_document():
    text = '日本語\n"引用"\\末尾'
    assert json.loads(build_request(text).input) == {"document": text}


def test_gateway_maps_request_and_extracts_final_text():
    calls = []
    request = build_request("機能: CSV出力")
    def handle(req):
        calls.append(req)
        return httpx.Response(200, json={"steps": [
            {"type": "thought", "content": [{"type": "text", "text": "ignore"}]},
            {"type": "model_output", "content": [{"type": "text", "text": "old"}]},
            {"type": "model_output", "content": [{"type": "text", "text": "日本"}, {"type": "text", "text": "語"}]},
        ]})
    gateway = GeminiGateway(model="test-model", api_key="offline-placeholder", transport=httpx.MockTransport(handle))
    try:
        assert gateway.complete(request) == "日本語"
    finally:
        gateway.close()
    assert len(calls) == 1
    assert json.loads(calls[0].content) == {"model": "test-model", "system_instruction": request.instructions, "input": request.input}
    assert calls[0].headers["x-goog-api-key"] == "offline-placeholder"
    assert calls[0].extensions["timeout"]["read"] == TIMEOUT_SECONDS


@pytest.mark.parametrize("kind", ["503", "timeout"])
def test_adapter_does_not_retry(kind):
    calls = []
    def handle(req):
        calls.append(req)
        if kind == "timeout":
            raise httpx.ReadTimeout("offline", request=req)
        return httpx.Response(503)
    gateway = GeminiGateway(api_key="offline-placeholder", transport=httpx.MockTransport(handle))
    try:
        with pytest.raises(httpx.ReadTimeout if kind == "timeout" else httpx.HTTPStatusError):
            gateway.complete(build_request("test"))
    finally:
        gateway.close()
    assert len(calls) == 1
