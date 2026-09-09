"""Real local behavior plus controllable service-boundary tests."""

import pytest
from fastapi.testclient import TestClient

from Week1.day06 import AnalysisOutput
from day11.app import app
from day11.service import AnalyzerUnavailable, RuleBasedAnalyzer, get_analyzer


client = TestClient(app)
ENDPOINT = "/analyze-requirement"
VALID_TEXT = "機能: CSV出力\n受入条件: 3秒以内\nリスク: 文字化け\n確認事項: 対象は何か\n備考: 対象外\n# コメント\n"
MISSING_ACCEPTANCE = ["At least one acceptance criterion is required"]
UNAVAILABLE_BODY = {
    "detail": {
        "code": "ANALYZER_UNAVAILABLE",
        "message": "Analysis service is temporarily unavailable",
    }
}


def make_fake_output() -> AnalysisOutput:
    """Deliberately different from parsing VALID_TEXT: prove replacement works."""
    return AnalysisOutput(
        requirements={"functions": ["替身の結果"], "acceptance_criteria": ["固定の条件"]},
        validation_errors=[],
    )


def make_incomplete_output() -> AnalysisOutput:
    return AnalysisOutput(
        requirements={"functions": ["替身の結果"]},
        validation_errors=list(MISSING_ACCEPTANCE),
    )


class RecordingAnalyzer(RuleBasedAnalyzer):
    def __init__(self, output: AnalysisOutput):
        self.output = output
        self.calls: list[str] = []

    def analyze(self, text: str) -> AnalysisOutput:
        self.calls.append(text)
        return self.output


class UnavailableAnalyzer(RuleBasedAnalyzer):
    def __init__(self):
        self.calls: list[str] = []

    def analyze(self, text: str) -> AnalysisOutput:
        self.calls.append(text)
        raise AnalyzerUnavailable("simulated internal diagnostic: worker unavailable")


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_real_analyzer_reuses_existing_rules() -> None:
    output = get_analyzer().analyze("機能： 登録\n備考: 対象外")
    assert isinstance(output, AnalysisOutput)
    assert output.requirements.functions == ["登録"]
    assert output.requirements.unknown == ["備考: 対象外"]
    assert output.validation_errors == MISSING_ACCEPTANCE


def test_real_api_preserves_all_categories() -> None:
    response = client.post(ENDPOINT, json={"text": VALID_TEXT})
    assert response.status_code == 200
    assert response.json() == {
        "schema_version": "1.0",
        "requirements": {
            "functions": ["CSV出力"], "acceptance_criteria": ["3秒以内"],
            "risks": ["文字化け"], "questions": ["対象は何か"],
            "unknown": ["備考: 対象外"],
        },
        "validation_errors": [],
    }


def test_default_and_false_keep_business_errors_as_results() -> None:
    default = client.post(ENDPOINT, json={"text": "機能: 登録"})
    explicit = client.post(
        ENDPOINT, params={"strict": "false"}, json={"text": "機能: 登録"}
    )
    assert default.status_code == explicit.status_code == 200
    assert default.json() == explicit.json()
    assert default.json()["validation_errors"] == MISSING_ACCEPTANCE


def test_strict_real_missing_section_is_400() -> None:
    response = client.post(
        ENDPOINT, params={"strict": "true"}, json={"text": "機能: 登録"}
    )
    assert response.status_code == 400
    assert response.json() == {
        "detail": {"code": "REQUIREMENT_INCOMPLETE", "errors": MISSING_ACCEPTANCE}
    }


def test_character_boundary_is_preserved() -> None:
    prefix = "機能: 登録\n受入条件: 必須\n#"
    text = prefix + "あ" * (2000 - len(prefix))
    allowed = client.post(ENDPOINT, params={"strict": "true"}, json={"text": text})
    assert allowed.status_code == 200
    assert allowed.json()["validation_errors"] == []
    rejected = client.post(ENDPOINT, json={"text": text + "あ"})
    assert rejected.status_code == 413
    assert rejected.json() == {
        "detail": {"code": "TEXT_TOO_LONG", "max_length": 2000, "actual_length": 2001}
    }


def test_invalid_requests_stay_422() -> None:
    wrong_type = client.post(ENDPOINT, json={"text": 123})
    assert wrong_type.status_code == 422
    assert wrong_type.json()["detail"][0]["type"] == "string_type"
    broken = client.post(ENDPOINT, content="{", headers={"Content-Type": "application/json"})
    assert broken.status_code == 422
    assert broken.json()["detail"][0]["type"] == "json_invalid"
    wrong_query = client.post(ENDPOINT, params={"strict": "banana"}, json={"text": VALID_TEXT})
    assert wrong_query.status_code == 422
    assert wrong_query.json()["detail"][0]["loc"] == ["query", "strict"]
    extra = client.post(ENDPOINT, json={"text": VALID_TEXT, "strict": True})
    assert extra.status_code == 422
    assert extra.json()["detail"][0]["type"] == "extra_forbidden"


def test_override_controls_output_and_receives_exact_text(monkeypatch) -> None:
    output = make_fake_output()
    fake = RecordingAnalyzer(output)

    def override_analyzer():
        return fake

    monkeypatch.setitem(app.dependency_overrides, get_analyzer, override_analyzer)
    input_text = "  機能: 原文を保持\n受入条件: 必須  \n"
    response = client.post(ENDPOINT, json={"text": input_text})
    assert response.status_code == 200
    assert response.json() == output.model_dump()
    assert fake.calls == [input_text]


def test_default_uses_errors_from_injected_output(monkeypatch) -> None:
    output = make_incomplete_output()
    fake = RecordingAnalyzer(output)
    monkeypatch.setitem(app.dependency_overrides, get_analyzer, lambda: fake)
    response = client.post(ENDPOINT, json={"text": VALID_TEXT})
    assert response.status_code == 200
    assert response.json() == output.model_dump()
    assert fake.calls == [VALID_TEXT]


def test_unavailable_is_safe_503(monkeypatch) -> None:
    fake = UnavailableAnalyzer()
    monkeypatch.setitem(app.dependency_overrides, get_analyzer, lambda: fake)
    response = client.post(ENDPOINT, json={"text": VALID_TEXT})
    assert response.status_code == 503
    assert response.json() == UNAVAILABLE_BODY
    assert "simulated internal diagnostic" not in response.text
    assert fake.calls == [VALID_TEXT]


def test_unexpected_programming_error_is_not_disguised_as_503(monkeypatch) -> None:
    class BrokenAnalyzer(RuleBasedAnalyzer):
        def analyze(self, text: str) -> AnalysisOutput:
            raise ValueError("simulated programming error")

    monkeypatch.setitem(app.dependency_overrides, get_analyzer, lambda: BrokenAnalyzer())
    # TestClient exposes an unhandled server exception for debugging.
    with pytest.raises(ValueError, match="simulated programming error"):
        client.post(ENDPOINT, json={"text": VALID_TEXT})


def test_success_and_service_failure_do_not_write_files(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    good = client.post(ENDPOINT, json={"text": VALID_TEXT})
    assert good.status_code == 200
    assert list(tmp_path.iterdir()) == []
    fake = UnavailableAnalyzer()
    monkeypatch.setitem(app.dependency_overrides, get_analyzer, lambda: fake)
    failed = client.post(ENDPOINT, json={"text": VALID_TEXT})
    assert failed.status_code == 503
    assert list(tmp_path.iterdir()) == []


def test_override_scope_restores_real_service(monkeypatch) -> None:
    original = dict(app.dependency_overrides)
    fake = RecordingAnalyzer(make_fake_output())
    # Provided explicit scope: restoration also happens if an assertion fails.
    with monkeypatch.context() as patch:
        patch.setitem(app.dependency_overrides, get_analyzer, lambda: fake)
        response = client.post(ENDPOINT, json={"text": VALID_TEXT})
        assert response.json()["requirements"]["functions"] == ["替身の結果"]
    assert app.dependency_overrides == original
    restored = client.post(ENDPOINT, json={"text": VALID_TEXT})
    assert restored.status_code == 200
    assert restored.json()["requirements"]["functions"] == ["CSV出力"]


def test_unavailable_in_strict_mode(monkeypatch) -> None:
    fake = UnavailableAnalyzer()
    monkeypatch.setitem(app.dependency_overrides,get_analyzer, lambda: fake)
    good = client.post(ENDPOINT, params={"strict": "true"},json={"text": "機能: 登録"})
    assert good.status_code == 503
    assert good.json() == UNAVAILABLE_BODY
    assert fake.calls == ["機能: 登録"]


def test_over_limit_does_not_call_analyzer(monkeypatch) -> None:
    fake = UnavailableAnalyzer()
    monkeypatch.setitem(app.dependency_overrides, get_analyzer, lambda: fake)
    good = client.post(ENDPOINT,params={"strict": "true"},json={"text": "あ" * 2001})
    assert good.status_code == 413
    assert good.json() == {"detail": {"code": "TEXT_TOO_LONG", "max_length": 2000, "actual_length": 2001}}
    assert fake.calls == []


def test_strict_checks_injected_business_errors(monkeypatch) -> None:
    fake = RecordingAnalyzer(make_incomplete_output())
    monkeypatch.setitem(app.dependency_overrides, get_analyzer, lambda: fake)
    good = client.post(ENDPOINT,params={"strict": "true"}, json={"text": VALID_TEXT})
    assert good.status_code == 400
    assert good.json() == {"detail": {"code": "REQUIREMENT_INCOMPLETE", "errors": MISSING_ACCEPTANCE}}
    assert fake.calls == [VALID_TEXT]
