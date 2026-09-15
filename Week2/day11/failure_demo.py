"""Local-only failure demonstration: python -m Week2.day11.failure_demo."""

import uvicorn

from Week1.day06 import AnalysisOutput
from .app import app
from .service import AnalyzerUnavailable, RuleBasedAnalyzer, get_analyzer


class UnavailableDemoAnalyzer(RuleBasedAnalyzer):
    def analyze(self, text: str) -> AnalysisOutput:
        raise AnalyzerUnavailable("simulated internal diagnostic: demo worker offline")


def get_unavailable_analyzer() -> RuleBasedAnalyzer:
    return UnavailableDemoAnalyzer()


def main() -> None:
    """Override only in this standalone process, and restore on shutdown."""
    previous = dict(app.dependency_overrides)
    app.dependency_overrides[get_analyzer] = get_unavailable_analyzer
    try:
        uvicorn.run(app, host="127.0.0.1", port=8012)
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)


if __name__ == "__main__":
    main()
