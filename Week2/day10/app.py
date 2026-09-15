"""Read the route first, then implement the two error-policy TODOs."""

from fastapi import FastAPI, HTTPException

from Week1.day06 import AnalysisOutput, parse_requirement, validate_result
from Week1.day06.cli import build_output
from Week2.day09.models import AnalyzeRequest

MAX_TEXT_LENGTH = 2000
app = FastAPI(title="Requirement Analyzer - Day 10", version="0.2.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/analyze-requirement",
    response_model=AnalysisOutput,
    responses={
        400: {"description": "Strict mode: required sections are missing"},
        413: {"description": "Requirement text exceeds the character limit"},
    },
)
def analyze_requirement(
        request: AnalyzeRequest, strict: bool = False
) -> AnalysisOutput:
    # Inherited Day 9 processing, with two new policy checks.
    check_text_length(request.text)
    requirements = parse_requirement(request.text)
    validation_errors = validate_result(requirements)
    check_business_errors(validation_errors, strict)
    return build_output(requirements, validation_errors)


def check_text_length(text: str) -> None:
    text_length = len(text)
    if text_length > MAX_TEXT_LENGTH:
        error_message = {"code": "TEXT_TOO_LONG", "max_length": 2000, "actual_length": text_length}
        raise HTTPException(status_code=413, detail=error_message)
    pass


def check_business_errors(validation_errors: list[str], strict: bool) -> None:
    if strict and validation_errors != []:
        error_message = {
            "code": "REQUIREMENT_INCOMPLETE",
            "errors": validation_errors,
        }
        raise HTTPException(status_code=400, detail=error_message)
    pass
