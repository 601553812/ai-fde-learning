"""Keep the old API working while completing the injection TODOs."""

from fastapi import Depends, FastAPI, HTTPException

from Week1.day06 import AnalysisOutput, parse_requirement, validate_result
from Week1.day06.cli import build_output
from day09.models import AnalyzeRequest
from day10.app import check_business_errors, check_text_length

from .service import AnalyzerUnavailable, RuleBasedAnalyzer, get_analyzer


app = FastAPI(title="Requirement Analyzer - Day 11", version="0.3.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/analyze-requirement",
    response_model=AnalysisOutput,
    responses={
        400: {"description": "Strict mode: required sections are missing"},
        413: {"description": "Requirement text exceeds the character limit"},
        503: {"description": "Analysis service is temporarily unavailable"},
    },
)
def analyze_requirement(
    request: AnalyzeRequest,
    strict: bool = False,
    analyzer: RuleBasedAnalyzer = Depends(get_analyzer),
) -> AnalysisOutput:

    check_text_length(request.text)
    output = invoke_analyzer(analyzer,request.text)
    check_business_errors(output.validation_errors, strict)
    return output



def invoke_analyzer(analyzer: RuleBasedAnalyzer, text: str) -> AnalysisOutput:
    try:
        return analyzer.analyze(text)
    except AnalyzerUnavailable as error:
        error_message = {
            "code": "ANALYZER_UNAVAILABLE",
            "message": "Analysis service is temporarily unavailable",
        }
        raise HTTPException(status_code=503, detail=error_message) from error
