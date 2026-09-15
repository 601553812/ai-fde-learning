"""Complete only FixedAnalyzer.analyze; do not change Day 11's API."""

from Week1.day06 import AnalysisOutput, RequirementData
from Week2.day11.service import RuleBasedAnalyzer


def make_fixed_output() -> AnalysisOutput:
    """Prepared data, deliberately different from either request's text."""
    return AnalysisOutput(
        requirements=RequirementData(
            functions=["固定のテスト結果"],
            acceptance_criteria=["固定の確認条件"],
        ),
        validation_errors=[],
    )


class FixedAnalyzer(RuleBasedAnalyzer):
    """A fake: record each input and return the prepared output."""

    def __init__(self, output: AnalysisOutput):
        self.output = output
        self.calls: list[str] = []

    def analyze(self, text: str) -> AnalysisOutput:
        self.calls.append(text)
        return self.output
