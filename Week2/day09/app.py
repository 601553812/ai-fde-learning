"""HTTP entry points. Route registration is provided; handlers are exercises."""

from fastapi import FastAPI

from Week1.day06 import AnalysisOutput, parse_requirement, validate_result
from Week1.day06.cli import build_output

from .models import AnalyzeRequest


app = FastAPI(title="Requirement Analyzer - Day 9", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    response_ok = {"status": "ok"}
    return response_ok


@app.post("/analyze-requirement", response_model=AnalysisOutput)
def analyze_requirement(request: AnalyzeRequest) -> AnalysisOutput:
    text = request.text
    requirements = parse_requirement(text)
    validation_error = validate_result(requirements)
    return build_output(requirements, validation_error)
