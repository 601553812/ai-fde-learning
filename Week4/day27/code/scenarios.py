"""Provided local HTTP scenarios. None of these contact Gemini."""

import httpx

RAW = '{"functions":["CSV出力"],"acceptance_criteria":[],"risks":[],"questions":[],"unknown":[]}'
SCENARIOS = ("success", "timeout", "unavailable", "rate_limit", "auth", "network")


def make_transport(scenario: str) -> httpx.MockTransport:
    def handle(request: httpx.Request) -> httpx.Response:
        if scenario == "timeout":
            raise httpx.ReadTimeout("simulated timeout", request=request)
        if scenario == "network":
            raise httpx.ConnectError("simulated network error", request=request)
        if scenario == "success":
            return httpx.Response(200, json={"steps": [
                {"type": "model_output", "content": [{"type": "text", "text": RAW}]}]})
        code = {"unavailable": 503, "rate_limit": 429, "auth": 403}[scenario]
        return httpx.Response(code, json={"error": {"message": "simulated failure"}})
    return httpx.MockTransport(handle)
