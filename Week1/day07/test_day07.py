"""Tests for the Day 7 HTTP JSON client."""

from __future__ import annotations

from typing import Any

import pytest
import requests

from Week1.day06.models import RequirementData
from Week1.day07.api_client import RequirementApiError, fetch_requirement


VALID_PAYLOAD: dict[str, list[str]] = {
    "functions": ["ユーザー登録"],
    "acceptance_criteria": ["登録成功時にIDを返す"],
    "risks": [],
    "questions": [],
    "unknown": [],
}


class FakeResponse:
    """Small response substitute; no real network call is made in tests."""

    def __init__(
        self,
        payload: Any = None,
        *,
        status_error: requests.HTTPError | None = None,
        json_error: requests.JSONDecodeError | None = None,
    ) -> None:
        self.payload = payload
        self.status_error = status_error
        self.json_error = json_error
        self.raise_for_status_called = False
        self.json_called = False

    def raise_for_status(self) -> None:
        self.raise_for_status_called = True
        if self.status_error is not None:
            raise self.status_error

    def json(self) -> Any:
        self.json_called = True
        if self.json_error is not None:
            raise self.json_error
        return self.payload


def test_requirement_api_error_inherits_runtime_error() -> None:
    assert issubclass(RequirementApiError, RuntimeError)


def test_fetch_requirement_uses_timeout_and_returns_model(monkeypatch: pytest.MonkeyPatch) -> None:
    response = FakeResponse(payload=VALID_PAYLOAD)

    def fake_get(url:str,timeout: float) -> FakeResponse:
        assert url == "https://example.invalid/requirements"
        assert timeout == 3.0
        return response

    monkeypatch.setattr("Week1.day07.api_client.requests.get", fake_get)

    result = fetch_requirement("https://example.invalid/requirements",timeout_seconds=3.0)
    assert isinstance(result, RequirementData)
    assert result.functions == ["ユーザー登録"]


def test_fetch_requirement_converts_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url:str,timeout: float) -> FakeResponse:
        raise requests.Timeout
    monkeypatch.setattr("Week1.day07.api_client.requests.get", fake_get)
    with pytest.raises(RequirementApiError):
        fetch_requirement("https://example.invalid/requirements")


def test_fetch_requirement_converts_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    response = FakeResponse(status_error=requests.HTTPError("503 Server Error"))
    monkeypatch.setattr("Week1.day07.api_client.requests.get", lambda url, timeout: response)

    with pytest.raises(RequirementApiError):
        fetch_requirement("https://example.invalid/requirements")

    assert response.raise_for_status_called
    assert not response.json_called


def test_fetch_requirement_converts_invalid_json(monkeypatch: pytest.MonkeyPatch) -> None:
    json_error = requests.JSONDecodeError("invalid JSON", "{", 1)
    response = FakeResponse(json_error=json_error)
    monkeypatch.setattr("Week1.day07.api_client.requests.get", lambda url, timeout: response)

    with pytest.raises(RequirementApiError):
        fetch_requirement("https://example.invalid/requirements")


def test_fetch_requirement_converts_schema_error(monkeypatch: pytest.MonkeyPatch) -> None:
    response = FakeResponse(payload={"functions":"not-a-list"})
    monkeypatch.setattr("Week1.day07.api_client.requests.get", lambda url, timeout: response)
    with pytest.raises(RequirementApiError):
       fetch_requirement(
           "https://example.invalid/requirements" )


def test_requirement_api_error_keeps_original_cause(monkeypatch: pytest.MonkeyPatch) -> None:
    original_error = requests.ConnectionError("connection refused")

    def fake_get(url: str, timeout: float) -> FakeResponse:
        raise original_error

    monkeypatch.setattr("Week1.day07.api_client.requests.get", fake_get)

    with pytest.raises(RequirementApiError) as caught:
        fetch_requirement("https://example.invalid/requirements")

    assert caught.value.__cause__ is original_error
