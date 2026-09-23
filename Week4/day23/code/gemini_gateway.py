"""Provided adapter, adapted from Day16 to make HTTP waits/retries explicit.

Preserves complete(ModelRequest) -> str and the request fields/model.
HTTPX is already installed. No imports from historical days.
"""

import os
import httpx
from .prompt import ModelRequest

DEFAULT_MODEL = "gemini-3.8-flash"
ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/interactions"
TIMEOUT_SECONDS = 10.0


class GeminiGateway:
    def __init__(self, model=DEFAULT_MODEL, *, api_key=None, transport=None):
        key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not key:
            raise ValueError("missing_api_key")
        self.model = model
        self.client = httpx.Client(
            headers={"x-goog-api-key": key}, timeout=TIMEOUT_SECONDS,
            follow_redirects=False, transport=transport,
        )  # HTTPX's default transport does not retry automatically.

    def complete(self, request: ModelRequest) -> str:
        response = self.client.post(ENDPOINT, json={
            "model": self.model, "system_instruction": request.instructions,
            "input": request.input,
        })
        response.raise_for_status()
        data = response.json()
        for step in reversed(data.get("steps", [])):
            if step.get("type") == "model_output":
                return "".join(part["text"] for part in step.get("content", [])
                               if part.get("type") == "text")
        # Earlier Interactions responses placed their content in outputs.
        return "".join(part["text"] for part in data.get("outputs", [])
                       if part.get("type") == "text")

    def close(self) -> None:
        self.client.close()
