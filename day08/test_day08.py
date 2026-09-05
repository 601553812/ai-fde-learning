"""Day 8 tests: trace the call boundary and replace external dependencies."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import requests
from pydantic import ValidationError

from Week1.day06.models import RequirementData
from Week1.day07.api_client import RequirementApiError, fetch_requirement
from day08.cli import run



VALID_PAYLOAD: dict[str, list[str]] = {
    "functions": ["ユーザー登録"],
    "acceptance_criteria": ["登録成功時にIDを返す"],
    "risks": [],
    "questions": [],
    "unknown": [],
}


class FakeResponse:
    """Only the Response behavior needed by fetch_requirement()."""

    def __init__(
        self,
        payload: Any = None,
        *,
        json_error: requests.JSONDecodeError | None = None,
    ) -> None:
        self.payload = payload
        self.json_error = json_error

    def raise_for_status(self) -> None:
        pass

    def json(self) -> Any:
        if self.json_error is not None:
            raise self.json_error
        return self.payload


def test_default_timeout_is_forwarded(monkeypatch: pytest.MonkeyPatch) -> None:
    #Arrange
    def fake_get(url: str, timeout: float) -> FakeResponse:
        assert timeout == 5.0
        return FakeResponse(payload=VALID_PAYLOAD)
    monkeypatch.setattr("Week1.day07.api_client.requests.get", fake_get)
    #Act
    result = fetch_requirement(
        "https://httpbin.org/get" )
    #Assert
    assert isinstance(result,RequirementData)



def test_invalid_json_keeps_json_error_as_cause(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    #Arrange
    error = requests.JSONDecodeError("json", "", 1)
    fake_response = FakeResponse(payload=VALID_PAYLOAD,json_error = error)

    monkeypatch.setattr( "Week1.day07.api_client.requests.get",lambda url,timeout:fake_response,)
    #Act
    with pytest.raises(RequirementApiError) as caught:
        fetch_requirement(
             "https://httpbin.org/get")
    #Assert
    assert caught.value.__cause__ is error


def test_schema_error_keeps_validation_error_as_cause(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = FakeResponse(payload={
    "functions": "ユーザー登録",
    "acceptance_criteria": ["登録成功時にIDを返す"],
    "risks": [],
    "questions": [],
    "unknown": [],
})
    def fake_get(url: str, timeout: float) -> FakeResponse:
        return response
    monkeypatch.setattr("Week1.day07.api_client.requests.get", fake_get)
    with pytest.raises(RequirementApiError) as e:
        fetch_requirement(
        "https://httpbin.org/get" )
    assert isinstance(e.value.__cause__ , ValidationError)

def test_run_writes_validated_json_and_forwards_timeout(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    data = RequirementData.model_validate(VALID_PAYLOAD)
    def fake_fetch( url: str,timeout: float,)-> RequirementData:
        assert url == "https://httpbin.org/get"
        assert timeout == 2.5
        return data
    monkeypatch.setattr("day08.cli.fetch_requirement", fake_fetch)
    output_path = tmp_path / "output.json"
    result = run(["https://httpbin.org/get", str(output_path), "--timeout", "2.5"])
    assert result == 0
    assert output_path.exists()
    json_text = output_path.read_text(encoding="UTF-8")
    assert RequirementData.model_validate_json(json_text) == data


def test_run_returns_one_and_does_not_write_on_api_error(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def fake_fetch(url, timeout_seconds) -> FakeResponse:
        raise RequirementApiError
    monkeypatch.setattr("day08.cli.fetch_requirement", fake_fetch)
    output_path = tmp_path / "output.json"
    assert run(["https://httpbin.org/get",str(output_path)]) == 1
    assert not output_path.exists()
