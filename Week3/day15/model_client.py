"""Adapt the existing generate(text) contract to an instruction-aware gateway."""

from Week2.day14.model_client import ModelClient
from Week3.day15.prompt import ModelRequest, build_request


class ModelGateway:
    """Provided contract. A future vendor adapter implements complete(request)."""

    def complete(self, request: ModelRequest) -> str:
        raise NotImplementedError("A concrete gateway must implement complete")


class RecordingGateway(ModelGateway):
    """Local test double. Records requests and returns fixed text, without AI."""

    def __init__(self, raw: str):
        self.raw = raw
        self.calls: list[ModelRequest] = []

    def complete(self, request: ModelRequest) -> str:
        self.calls.append(request)
        return self.raw


class PromptedModelClient(ModelClient):
    def __init__(self, gateway: ModelGateway):
        self.gateway = gateway

    def generate(self, text: str) -> str:
        model_request = build_request(text)
        result = self.gateway.complete(model_request)
        return result
