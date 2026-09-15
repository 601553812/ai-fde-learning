"""Reuse Day 11 behavior; make only the length policy configurable."""

from fastapi import Depends, FastAPI, HTTPException

from Week1.day06 import AnalysisOutput
from Week2.day09.models import AnalyzeRequest
from Week2.day10.app import check_business_errors
from Week2.day11.app import invoke_analyzer
from Week2.day11.service import RuleBasedAnalyzer, get_analyzer
from Week2.day13.settings import Settings, get_settings

app = FastAPI(title="Requirement Analyzer - Day 13", version="0.4.0")


@app.get("/health")
def health() -> dict[str, str]:
    # Liveness only: this endpoint does not read the analysis configuration.
    return {"status": "ok"}


@app.post(
    "/analyze-requirement",
    response_model=AnalysisOutput,
    responses={
        400: {"description": "Strict mode: required sections are missing"},
        413: {"description": "Requirement text exceeds the configured limit"},
        503: {"description": "Invalid server configuration or unavailable analyzer"},
    },
)
def analyze_requirement(
    request: AnalyzeRequest,
    strict: bool = False,
    settings: Settings = Depends(get_settings),
    analyzer: RuleBasedAnalyzer = Depends(get_analyzer),
) -> AnalysisOutput:
    check_text_length(request.text, settings.max_text_length)
    output = invoke_analyzer(analyzer, request.text)
    check_business_errors(output.validation_errors, strict)
    return output


def check_text_length(text: str, max_text_length: int) -> None:
    if len(text) <= max_text_length :
        return None
    else :
        raise HTTPException(status_code=413, detail={"code": "TEXT_TOO_LONG", "max_length": max_text_length, "actual_length": len(text)})
