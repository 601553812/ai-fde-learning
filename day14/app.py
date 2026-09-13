"""Keep Day 13's contract; add a safe response for invalid model output."""

from fastapi import Depends, FastAPI, HTTPException

from Week1.day06 import AnalysisOutput
from day09.models import AnalyzeRequest
from day10.app import check_business_errors
from day11.app import invoke_analyzer
from day13.app import check_text_length
from day13.settings import Settings, get_settings
from day14.service import InvalidModelOutput, ModelOutputAnalyzer, get_analyzer

app = FastAPI(title="Requirement Analyzer - Day 14 (local simulation)", version="0.5.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/analyze-requirement",
    response_model=AnalysisOutput,
    responses={
        400: {"description": "Strict mode: required sections are missing"},
        413: {"description": "Requirement text exceeds the configured limit"},
        502: {"description": "Model output does not match the schema"},
        503: {"description": "Invalid server configuration or unavailable analyzer"},
    },
)
def analyze_requirement(
    request: AnalyzeRequest,
    strict: bool = False,
    settings: Settings = Depends(get_settings),
    analyzer: ModelOutputAnalyzer = Depends(get_analyzer),
) -> AnalysisOutput:
    check_text_length(request.text, settings.max_text_length)
    try:
        output = invoke_analyzer(analyzer, request.text)
    except InvalidModelOutput as e:
        raise HTTPException(status_code=502, detail={"code":"MODEL_OUTPUT_INVALID","message":"Model returned invalid output"}) from e
    check_business_errors(output.validation_errors, strict)
    return output
