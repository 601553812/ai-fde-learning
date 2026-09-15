"""Settings tests first, then API behavior and two student-owned tests."""

import pytest
from fastapi.testclient import TestClient

from Week2.day11.service import AnalyzerUnavailable, RuleBasedAnalyzer, get_analyzer
from Week2.day12.exercise import FixedAnalyzer, make_fixed_output
from Week2.day13 import settings as settings_module
from Week2.day13.app import app
from Week2.day13.settings import CONFIG_ERROR_MESSAGE, ENV_NAME, ConfigurationError, Settings, load_settings

client = TestClient(app)
ENDPOINT = "/analyze-requirement"
VALID_TEXT = "機能: CSV出力\n受入条件: 3秒以内\nリスク: 文字化け\n確認事項: 対象は何か\n備考: 対象外\n"
CONFIG_ERROR_BODY = {
    "detail": {"code": "CONFIGURATION_INVALID", "message": "Server configuration is invalid"}
}


def test_missing_environment_uses_default(monkeypatch) -> None:
    monkeypatch.delenv(ENV_NAME, raising=False)
    assert load_settings() == Settings(max_text_length=2000)


def test_valid_environment_is_converted_to_int(monkeypatch) -> None:
    for value, expected in [("80", 80), ("1", 1), ("10000", 10000), (" 120 ", 120)]:
        monkeypatch.setenv(ENV_NAME, value)
        result = load_settings()
        assert result.max_text_length == expected
        assert type(result.max_text_length) is int


def test_non_integer_and_empty_values_are_rejected(monkeypatch) -> None:
    for value in ["not-a-number", "", "2.5"]:
        monkeypatch.setenv(ENV_NAME, value)
        with pytest.raises(ConfigurationError) as captured:
            load_settings()
        assert str(captured.value) == CONFIG_ERROR_MESSAGE


def test_out_of_range_values_are_rejected(monkeypatch) -> None:
    for value in ["0", "-1", "10001"]:
        monkeypatch.setenv(ENV_NAME, value)
        with pytest.raises(ConfigurationError) as captured:
            load_settings()
        assert str(captured.value) == CONFIG_ERROR_MESSAGE


def test_health_is_liveness_not_configuration_validation(monkeypatch) -> None:
    monkeypatch.setenv(ENV_NAME, "not-a-number")
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_default_api_keeps_previous_contract(monkeypatch) -> None:
    monkeypatch.delenv(ENV_NAME, raising=False)
    response = client.post(ENDPOINT, json={"text": VALID_TEXT})
    assert response.status_code == 200
    assert response.json() == {
        "schema_version": "1.0",
        "requirements": {
            "functions": ["CSV出力"], "acceptance_criteria": ["3秒以内"],
            "risks": ["文字化け"], "questions": ["対象は何か"], "unknown": ["備考: 対象外"],
        },
        "validation_errors": [],
    }
    draft = client.post(ENDPOINT, json={"text": "機能: 登録"})
    assert draft.status_code == 200
    assert draft.json()["validation_errors"] == ["At least one acceptance criterion is required"]
    strict = client.post(ENDPOINT, params={"strict": "true"}, json={"text": "機能: 登録"})
    assert strict.status_code == 400
    assert strict.json() == {
        "detail": {"code": "REQUIREMENT_INCOMPLETE", "errors": ["At least one acceptance criterion is required"]}
    }
    assert client.post(ENDPOINT, json={"text": 123}).status_code == 422
    assert client.post(ENDPOINT, params={"strict": "banana"}, json={"text": VALID_TEXT}).status_code == 422
    allowed = client.post(ENDPOINT, json={"text": "あ" * 2000})
    assert allowed.status_code == 200
    rejected = client.post(ENDPOINT, json={"text": "あ" * 2001})
    assert rejected.status_code == 413
    assert rejected.json() == {
        "detail": {"code": "TEXT_TOO_LONG", "max_length": 2000, "actual_length": 2001}
    }


def test_injected_analyzer_still_controls_output(monkeypatch) -> None:
    monkeypatch.delenv(ENV_NAME, raising=False)
    expected = make_fixed_output()
    fake = FixedAnalyzer(expected)

    def get_test_analyzer():
        return fake

    monkeypatch.setitem(app.dependency_overrides, get_analyzer, get_test_analyzer)
    response = client.post(ENDPOINT, json={"text": VALID_TEXT})
    assert response.status_code == 200
    assert response.json() == expected.model_dump()
    assert fake.calls == [VALID_TEXT]
def test_configured_limit_allows_exact_boundary(monkeypatch) -> None:
    limit = len(VALID_TEXT)
    monkeypatch.setenv(ENV_NAME, str(limit))
    allowed = client.post(ENDPOINT, params={"strict": "true"}, json={"text": VALID_TEXT})
    assert allowed.status_code == 200
    rejected = client.post(ENDPOINT, json={"text": VALID_TEXT + "あ"})
    assert rejected.status_code == 413
    assert rejected.json() == {
        "detail": {"code": "TEXT_TOO_LONG", "max_length": limit, "actual_length": limit + 1}
    }


def test_invalid_configuration_is_safe_503(monkeypatch) -> None:
    raw_value = "invalid-internal-setting-value"
    monkeypatch.setenv(ENV_NAME, raw_value)
    response = client.post(ENDPOINT, json={"text": VALID_TEXT})
    assert response.status_code == 503
    assert response.json() == CONFIG_ERROR_BODY
    assert raw_value not in response.text


def test_analyzer_failure_keeps_its_own_503_code(monkeypatch) -> None:
    monkeypatch.delenv(ENV_NAME, raising=False)

    class FailingAnalyzer(RuleBasedAnalyzer):
        def analyze(self, text):
            raise AnalyzerUnavailable("simulated analyzer failure")

    def get_failing_analyzer():
        return FailingAnalyzer()

    monkeypatch.setitem(app.dependency_overrides, get_analyzer, get_failing_analyzer)
    response = client.post(ENDPOINT, json={"text": VALID_TEXT})
    assert response.status_code == 503
    assert response.json() == {
        "detail": {"code": "ANALYZER_UNAVAILABLE", "message": "Analysis service is temporarily unavailable"}
    }


def test_environment_scope_restores_default(monkeypatch) -> None:
    monkeypatch.delenv(ENV_NAME, raising=False)
    with monkeypatch.context() as patch:
        patch.setenv(ENV_NAME, "80")
        assert load_settings().max_text_length == 80
    assert load_settings().max_text_length == 2000


def test_unexpected_configuration_bug_is_not_hidden(monkeypatch) -> None:
    def broken_loader():
        raise TypeError("simulated programming error")

    monkeypatch.setattr(settings_module, "load_settings", broken_loader)
    with pytest.raises(TypeError, match="simulated programming error"):
        client.post(ENDPOINT, json={"text": VALID_TEXT})


def test_custom_limit_rejects_before_analyzer_call(monkeypatch) -> None:
    monkeypatch.setenv(ENV_NAME, "12")
    fake = FixedAnalyzer(make_fixed_output())
    def get_analyzer_test():
        return fake
    monkeypatch.setitem(app.dependency_overrides, get_analyzer,get_analyzer_test)
    response = client.post(ENDPOINT, json={"text": "あ" * 13})
    assert response.status_code == 413
    assert response.json() == {"detail": {"code": "TEXT_TOO_LONG", "max_length": 12, "actual_length": 13}}
    assert fake.calls == []



def test_repaired_configuration_allows_the_next_request(monkeypatch) -> None:
    expected = make_fixed_output()
    fake = FixedAnalyzer(expected)
    def get_analyzer_test():
        return fake
    monkeypatch.setitem(app.dependency_overrides, get_analyzer, get_analyzer_test)
    monkeypatch.setenv(ENV_NAME, "bad")
    response = client.post(ENDPOINT, json={"text": VALID_TEXT})
    assert response.status_code == 503
    assert response.json() == CONFIG_ERROR_BODY
    assert fake.calls == []
    monkeypatch.setenv(ENV_NAME, "80")
    response = client.post(ENDPOINT, json={"text": VALID_TEXT})
    assert response.status_code == 200
    assert response.json() == expected.model_dump()
    assert fake.calls == [VALID_TEXT]
