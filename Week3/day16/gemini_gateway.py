"""Gemini adapter for the Day 15 instruction-aware request contract."""

from google import genai

from Week3.day15.model_client import ModelGateway
from Week3.day15.prompt import ModelRequest


DEFAULT_MODEL = "gemini-3.8-flash"


class GeminiGateway(ModelGateway):
    """Send one ModelRequest to Gemini through the official Python SDK.

    The SDK reads GEMINI_API_KEY from the process environment. The key is
    therefore never part of this class, a request object, or a repository file.
    """

    def __init__(self, model: str = DEFAULT_MODEL, client=None):
        self.model = model
        self.client = client or genai.Client()

    def complete(self, request: ModelRequest) -> str:
        interaction = self.client.interactions.create(
            model=self.model,
            system_instruction=request.instructions,
            input=request.input,
        )
        return interaction.output_text or ""
