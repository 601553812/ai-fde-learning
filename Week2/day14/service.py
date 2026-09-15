"""Validate raw model text, then build the existing API output."""

from pydantic import ValidationError

from Week1.day06 import AnalysisOutput, RequirementData, validate_result
from Week2.day11.service import RuleBasedAnalyzer
from Week2.day14.model_client import LocalModelClient, ModelClient

MODEL_OUTPUT_ERROR_MESSAGE = "Model output does not match the requirement schema"


class InvalidModelOutput(ValueError):
    """The model returned text that cannot satisfy our data contract."""


def decode_requirements(raw: str) -> RequirementData:
    try :
        result = RequirementData.model_validate_json(raw,strict=True)
    except ValidationError as e:
        raise InvalidModelOutput(MODEL_OUTPUT_ERROR_MESSAGE) from e
    return result



class ModelOutputAnalyzer(RuleBasedAnalyzer):
    def __init__(self, client: ModelClient):
        self.client = client

    def analyze(self, text: str) -> AnalysisOutput:
        raw = self.client.generate(text)
        requirements = decode_requirements(raw)
        validation_errors = validate_result(requirements.model_dump())
        return AnalysisOutput(requirements=requirements, validation_errors=validation_errors)



def get_analyzer() -> ModelOutputAnalyzer:
    """Provided: the default server uses a local simulation, not a real LLM."""
    return ModelOutputAnalyzer(LocalModelClient())
