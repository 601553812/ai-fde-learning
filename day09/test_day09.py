"""Exercise the HTTP contract with real local parsing and no external API."""

import pytest
from fastapi.testclient import TestClient

from day09.app import app


client = TestClient(app)
ENDPOINT = "/analyze-requirement"


def test_health_returns_ok() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analyze_returns_versioned_requirements() -> None:
    response = client.post(
        ENDPOINT,
        json={"text": "機能: ユーザー登録\n受入条件： IDを返す\nリスク: 重複登録"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {
        "schema_version": "1.0",
        "requirements": {
            "functions": ["ユーザー登録"],
            "acceptance_criteria": ["IDを返す"],
            "risks": ["重複登録"],
            "questions": [],
            "unknown": [],
        },
        "validation_errors": [],
    }


def test_business_errors_are_analysis_results() -> None:
    response = client.post(ENDPOINT, json={"text": "備考: 対象外"})
    assert response.status_code == 200
    assert response.json() == {
        "schema_version": "1.0",
        "requirements": {
            "functions": [],
            "acceptance_criteria": [],
            "risks": [],
            "questions": [],
            "unknown": ["備考: 対象外"],
        },
        "validation_errors": [
            "At least one function is required",
            "At least one acceptance criterion is required",
        ],
    }


def test_missing_text_is_rejected() -> None:
    response = client.post(ENDPOINT, json={})
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "text"]
    assert response.json()["detail"][0]["type"] == "missing"


def test_non_string_text_is_rejected() -> None:
    response = client.post(ENDPOINT, json={"text": 123})
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "text"]
    assert response.json()["detail"][0]["type"] == "string_type"


def test_empty_text_is_rejected() -> None:
    response = client.post(ENDPOINT, json={"text": ""})
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "string_too_short"


def test_extra_field_is_rejected() -> None:
    response = client.post(ENDPOINT, json={"text": "機能: 登録", "unexpected": True})
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "unexpected"]
    assert response.json()["detail"][0]["type"] == "extra_forbidden"


def test_invalid_json_is_rejected() -> None:
    response = client.post(
        ENDPOINT,
        content="{",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "json_invalid"


def test_analyze_uses_another_input() -> None:
    #Arrange
    input_text = "機能： CSV出力\n受入条件: 3秒以内"
    #Act
    response = client.post(ENDPOINT, json={"text": input_text})
    #Assert
    assert response.status_code == 200
    assert response.json()["requirements"]["functions"] == ["CSV出力"]
    assert response.json()["requirements"]["acceptance_criteria"] == ["3秒以内"]
    assert response.json()["validation_errors"] == []
    assert response.json()["schema_version"] == "1.0"


def test_analyze_preserves_questions_and_unknown_lines() -> None:
    #Arrange
    input_text = "機能: 登録\n受入条件: 必須\n確認事項: 期限はいつか\n備考: 対象外\n# コメント\n"
    #Act
    response = client.post(ENDPOINT, json={"text": input_text})
    assert response.status_code == 200
    assert response.json()["requirements"]["functions"] == ["登録"]
    assert response.json()["requirements"]["acceptance_criteria"] == ["必須"]
    assert response.json()["requirements"]["questions"] == ["期限はいつか"]
    assert response.json()["requirements"]["unknown"] == ["備考: 対象外"]
    assert response.json()["requirements"]["risks"] == []
    assert response.json()["validation_errors"] == []
