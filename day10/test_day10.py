"""HTTP contracts: existing behavior, new policies, and three learner tests."""
from typing import Any

import pytest
from fastapi.testclient import TestClient

from day10.app import MAX_TEXT_LENGTH, app


client = TestClient(app)
ENDPOINT = "/analyze-requirement"
VALID_TEXT = "機能： CSV出力\n受入条件: 3秒以内\nリスク: 文字化け\n確認事項: 対象は何か\n備考: 対象外\n# コメント\n"
MISSING_BOTH = [
    "At least one function is required",
    "At least one acceptance criterion is required",
]


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_invalid_json_stays_422() -> None:
    response = client.post(
        ENDPOINT, content="{", headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "json_invalid"


def test_missing_text_stays_422() -> None:
    response = client.post(ENDPOINT, json={})
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "text"]


def test_wrong_text_type_stays_422() -> None:
    response = client.post(ENDPOINT, json={"text": 123})
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "string_type"


def test_empty_text_stays_422() -> None:
    response = client.post(ENDPOINT, json={"text": ""})
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "string_too_short"


def test_strict_in_body_is_not_a_query_parameter() -> None:
    response = client.post(ENDPOINT, json={"text": VALID_TEXT, "strict": True})
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "strict"]
    assert response.json()["detail"][0]["type"] == "extra_forbidden"


def test_invalid_query_bool_is_422() -> None:
    response = client.post(
        ENDPOINT, params={"strict": "banana"}, json={"text": VALID_TEXT}
    )
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["query", "strict"]
    assert response.json()["detail"][0]["type"] == "bool_parsing"


def test_default_mode_keeps_business_errors_as_results() -> None:
    response = client.post(ENDPOINT, json={"text": "備考: 対象外"})
    assert response.status_code == 200
    assert response.json() == {
        "schema_version": "1.0",
        "requirements": {
            "functions": [], "acceptance_criteria": [], "risks": [],
            "questions": [], "unknown": ["備考: 対象外"],
        },
        "validation_errors": MISSING_BOTH,
    }


def test_explicit_false_is_not_a_truthy_string() -> None:
    response = client.post(
        ENDPOINT, params={"strict": "false"}, json={"text": "備考: 対象外"}
    )
    assert response.status_code == 200
    assert response.json()["validation_errors"] == MISSING_BOTH


def test_strict_valid_input_preserves_all_categories() -> None:
    response = client.post(
        ENDPOINT, params={"strict": "true"}, json={"text": VALID_TEXT}
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {
        "schema_version": "1.0",
        "requirements": {
            "functions": ["CSV出力"], "acceptance_criteria": ["3秒以内"],
            "risks": ["文字化け"], "questions": ["対象は何か"],
            "unknown": ["備考: 対象外"],
        },
        "validation_errors": [],
    }


def test_strict_missing_sections_returns_all_errors() -> None:
    response = client.post(
        ENDPOINT, params={"strict": "true"}, json={"text": "備考: 対象外"}
    )
    assert response.status_code == 400
    assert response.json() == {
        "detail": {"code": "REQUIREMENT_INCOMPLETE", "errors": MISSING_BOTH}
    }


def test_exact_character_limit_is_allowed() -> None:
    # A comment pads the length without altering the valid business content.
    prefix = "機能: 登録\n受入条件: 必須\n#"
    text = prefix + "あ" * (2000 - len(prefix))
    assert MAX_TEXT_LENGTH == 2000
    assert len(text) == 2000
    assert len(text.encode("utf-8")) > 2000
    response = client.post(
        ENDPOINT, params={"strict": "true"}, json={"text": text}
    )
    assert response.status_code == 200
    assert response.json()["requirements"]["functions"] == ["登録"]
    assert response.json()["validation_errors"] == []


def test_over_limit_precedes_business_check(monkeypatch) -> None:
    # Provided guard: the parser must not run for oversized input.
    def unexpected_parse(text: str):
        pytest.fail("Length must be checked BEFORE calling the parser")

    monkeypatch.setattr("day10.app.parse_requirement", unexpected_parse)
    response = client.post(
        ENDPOINT, params={"strict": "true"}, json={"text": "あ" * 2001}
    )
    assert response.status_code == 413
    assert response.json() == {
        "detail": {"code": "TEXT_TOO_LONG", "max_length": 2000, "actual_length": 2001}
    }


def test_requests_do_not_create_output_files(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    good = client.post(ENDPOINT, json={"text": VALID_TEXT})
    assert good.status_code == 200
    assert list(tmp_path.iterdir()) == []
    bad = client.post(ENDPOINT, params={"strict": "true"}, json={"text": "備考: 対象外"})
    assert bad.status_code == 400
    assert list(tmp_path.iterdir()) == []
    large = client.post(ENDPOINT, json={"text": "あ" * 2001})
    assert large.status_code == 413
    assert list(tmp_path.iterdir()) == []


def test_strict_only_missing_acceptance() -> None:
    response = client.post(ENDPOINT, params={"strict": "true"}, json={"text": "機能: CSV出力"})
    assert response.status_code == 400
    assert response.json() == {"detail": {"code": "REQUIREMENT_INCOMPLETE", "errors": ["At least one acceptance criterion is required"]}}
    dict_json:list[str]
    dict_json = response.json()["detail"]["errors"]
    assert "At least one function is required" not in dict_json


def test_whitespace_depends_on_strict_mode() -> None:
    response = client.post(ENDPOINT,params={"strict": "false"},json = {"text":" \n "})
    assert response.status_code == 200
    assert response.json()["requirements"]["functions"] == []
    assert response.json()["requirements"]["acceptance_criteria"] == []
    assert response.json()["requirements"]["risks"] == []
    assert response.json()["requirements"]["questions"] == []
    assert response.json()["requirements"]["unknown"] == []
    assert response.json()["validation_errors"]== MISSING_BOTH
    response = client.post(ENDPOINT,params={"strict": "true"},json = {"text":" \n "})
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "REQUIREMENT_INCOMPLETE"
    assert response.json()["detail"]["errors"] == MISSING_BOTH



def test_valid_request_after_business_error() -> None:
    response = client.post(ENDPOINT,params={"strict": "true"},json = {"text":"機能: 登録"})
    assert response.status_code == 400
    assert response.json()["detail"]["errors"] == ["At least one acceptance criterion is required"]

    response = client.post(ENDPOINT,params={"strict": "true"},json = {"text":"機能: ログイン\n受入条件: 1秒以内"})
    assert response.status_code == 200
    assert response.json()["schema_version"] == "1.0"
    assert response.json()["requirements"]["functions"] == ["ログイン"]
    assert response.json()["requirements"]["acceptance_criteria"] == ["1秒以内"]
    assert response.json()["validation_errors"] == []
