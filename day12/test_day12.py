"""Read the provided recovery test before completing TODO 2."""

import pytest
from fastapi.testclient import TestClient

from Week1.day06 import AnalysisOutput, RequirementData
from day11.app import app
from day11.service import get_analyzer
from day12.exercise import FixedAnalyzer, make_fixed_output


client = TestClient(app)
ENDPOINT = "/analyze-requirement"
INPUT_A = "  機能: CSV出力\n受入条件: 3秒以内  \n"
INPUT_B = "機能: PDF出力\n受入条件: 5秒以内\n"


def test_real_analyzer_and_result_are_different_objects() -> None:
    analyzer = get_analyzer()
    output = analyzer.analyze(INPUT_A)
    assert isinstance(output, AnalysisOutput)
    assert isinstance(output.requirements, RequirementData)
    assert output.requirements.functions == ["CSV出力"]
    assert output.validation_errors == []


def test_new_fake_has_no_call_records() -> None:
    expected = make_fixed_output()
    fake = FixedAnalyzer(expected)
    assert fake.output == expected
    assert fake.calls == []


def test_fake_direct_call_returns_prepared_output() -> None:
    expected = make_fixed_output()
    fake = FixedAnalyzer(expected)
    output = fake.analyze(INPUT_A)
    assert isinstance(output, AnalysisOutput)
    assert output == expected
    assert fake.calls == [INPUT_A]


def test_override_scope_restores_real_service(monkeypatch) -> None:
    # This complete example is for reading; do not modify its assertions.
    original = dict(app.dependency_overrides)
    expected = make_fixed_output()
    fake = FixedAnalyzer(expected)

    def get_test_analyzer():
        return fake

    with monkeypatch.context() as patch:
        patch.setitem(app.dependency_overrides, get_analyzer, get_test_analyzer)
        response = client.post(ENDPOINT, json={"text": INPUT_A})
        assert response.status_code == 200
        assert response.json() == expected.model_dump()
        assert fake.calls == [INPUT_A]

    assert app.dependency_overrides == original
    restored = client.post(ENDPOINT, json={"text": INPUT_A})
    assert restored.status_code == 200
    assert restored.json()["requirements"]["functions"] == ["CSV出力"]
    assert fake.calls == [INPUT_A]


def test_two_requests_keep_both_inputs(monkeypatch) -> None:
    expected = make_fixed_output()
    fake = FixedAnalyzer(expected)

    def get_test_analyzer():
        return fake

    with monkeypatch.context() as patch:
        patch.setitem(app.dependency_overrides, get_analyzer, get_test_analyzer)
        response_a = client.post(ENDPOINT, json={"text": INPUT_A})
        response_b = client.post(ENDPOINT, json={"text": INPUT_B})
        assert response_a.status_code == 200
        assert response_a.json() == expected.model_dump()
        assert response_b.status_code == 200
        assert response_b.json() == expected.model_dump()
        assert fake.calls == [INPUT_A, INPUT_B]
