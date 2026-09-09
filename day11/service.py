"""The existing rule parser, packaged as a replaceable local service."""

from Week1.day06 import AnalysisOutput, parse_requirement, validate_result
from Week1.day06.cli import build_output


class AnalyzerUnavailable(RuntimeError):
    """An expected temporary failure of the analysis service."""


class RuleBasedAnalyzer:
    """Keep Day 10's verified parsing behavior; no network or file I/O."""

    def analyze(self, text: str) -> AnalysisOutput:
        requirements = parse_requirement(text)
        validation_errors = validate_result(requirements)
        return build_output(requirements, validation_errors)


def get_analyzer() -> RuleBasedAnalyzer:
    """FastAPI calls this provider to obtain the default service instance."""
    return RuleBasedAnalyzer()
