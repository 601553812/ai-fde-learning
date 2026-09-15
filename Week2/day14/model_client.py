"""Provided local stand-ins. None of these classes makes a network request."""

from Week2.day11.service import RuleBasedAnalyzer


class ModelClient:
    """The small method contract a future real model client will implement."""

    def generate(self, text: str) -> str:
        raise NotImplementedError("A concrete client must implement generate")


class LocalModelClient(ModelClient):
    """Use the existing rule parser to simulate a model's JSON text response."""

    def generate(self, text: str) -> str:
        output = RuleBasedAnalyzer().analyze(text)
        return output.requirements.model_dump_json()


class FixedModelClient(ModelClient):
    """Record requests and return supplied text, including intentionally bad JSON."""

    def __init__(self, raw: str):
        self.raw = raw
        self.calls: list[str] = []

    def generate(self, text: str) -> str:
        self.calls.append(text)
        return self.raw
