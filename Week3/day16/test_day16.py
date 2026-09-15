"""Offline tests for the Gemini adapter; no network call is made here."""

from dataclasses import dataclass

from Week3.day15.prompt import build_request
from Week3.day16.gemini_gateway import GeminiGateway


@dataclass
class FakeInteraction:
    output_text: str


class FakeInteractions:
    def __init__(self):
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        return FakeInteraction('{"functions": [], "acceptance_criteria": [], "risks": [], "questions": [], "unknown": []}')


class FakeClient:
    def __init__(self):
        self.interactions = FakeInteractions()


def test_gateway_maps_internal_request_to_gemini_interactions():
    fake_client = FakeClient()
    gateway = GeminiGateway(model="test-model", client=fake_client)
    request = build_request("機能: CSV出力")

    result = gateway.complete(request)

    assert result.startswith('{"functions"')
    assert fake_client.interactions.kwargs == {
        "model": "test-model",
        "system_instruction": request.instructions,
        "input": request.input,
    }
