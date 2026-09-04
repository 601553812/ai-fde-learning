"""Tests for the Day 7 HTTP JSON client."""

from __future__ import annotations

from typing import Any

import pytest
import requests

from day06.models import RequirementData
from day07.api_client import RequirementApiError, fetch_requirement


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
    # TODO 4: 用 FakeResponse 和 monkeypatch 模拟成功响应，并检查 URL、timeout 和结果。
    pytest.fail("TODO 4: test successful HTTP JSON response")


def test_fetch_requirement_converts_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    # TODO 5: 让假的 requests.get 抛出 requests.Timeout，并检查 RequirementApiError。
    pytest.fail("TODO 5: test timeout conversion")


def test_fetch_requirement_converts_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    response = FakeResponse(status_error=requests.HTTPError("503 Server Error"))
    monkeypatch.setattr("day07.api_client.requests.get", lambda url, timeout: response)

    with pytest.raises(RequirementApiError):
        fetch_requirement("https://example.invalid/requirements")

    assert response.raise_for_status_called
    assert not response.json_called


def test_fetch_requirement_converts_invalid_json(monkeypatch: pytest.MonkeyPatch) -> None:
    json_error = requests.JSONDecodeError("invalid JSON", "{", 1)
    response = FakeResponse(json_error=json_error)
    monkeypatch.setattr("day07.api_client.requests.get", lambda url, timeout: response)

    with pytest.raises(RequirementApiError):
        fetch_requirement("https://example.invalid/requirements")


def test_fetch_requirement_converts_schema_error(monkeypatch: pytest.MonkeyPatch) -> None:
    # TODO 6: 返回 functions 类型错误的 JSON，并检查 RequirementApiError。
    pytest.fail("TODO 6: test Pydantic schema error conversion")


def test_requirement_api_error_keeps_original_cause(monkeypatch: pytest.MonkeyPatch) -> None:
    original_error = requests.ConnectionError("connection refused")

    def fake_get(url: str, timeout: float) -> FakeResponse:
        raise original_error

    monkeypatch.setattr("day07.api_client.requests.get", fake_get)

    with pytest.raises(RequirementApiError) as caught:
        fetch_requirement("https://example.invalid/requirements")

    assert caught.value.__cause__ is original_error
