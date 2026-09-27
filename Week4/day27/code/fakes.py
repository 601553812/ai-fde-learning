"""Provided recording doubles; no network and no waiting."""

import httpx


def status_error(code: int) -> httpx.HTTPStatusError:
    request = httpx.Request("POST", "https://example.invalid/model")
    response = httpx.Response(code, request=request)
    return httpx.HTTPStatusError("private mock detail", request=request, response=response)


class SequenceGateway:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = []
        self.events = []

    def complete(self, request):
        index = len(self.calls)
        self.calls.append(request)
        self.events.append("call")
        if index >= len(self.outcomes):
            raise AssertionError("Unexpected extra model call")
        outcome = self.outcomes[index]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class RecordingSleeper:
    def __init__(self, events=None):
        self.calls = []
        self.events = events if events is not None else []

    def __call__(self, seconds):
        self.calls.append(seconds)
        self.events.append("sleep")
