"""Day26 contracts: mode selection without calling the external model."""

from fastapi.testclient import TestClient
from fastapi import HTTPException
import pytest

from ..code.app import app
from ..code import runtime
from ..code.ui_client import submit_batch
from .test_ui_client import RecordingClient, response


def test_api_live_query_marks_report_from_injected_gateway():
    calls = []

    class FakeGateway:
        def complete(self, request):
            calls.append(request)
            return '{"functions":["CSV出力"],"acceptance_criteria":[],"risks":[],"questions":[],"unknown":[]}'

    app.dependency_overrides[runtime.get_runtime] = lambda: runtime.BatchRuntime(
        lambda task_id: FakeGateway(), lambda seconds: None
    )
    try:
        with TestClient(app) as client:
            res = client.post("/analyze-batch?mode=live", json={
                "tasks": [{"task_id": "A", "text": "一覧をCSVで出力する。"}],
                "max_attempts": 1,
            })
    finally:
        app.dependency_overrides.clear()
    assert res.status_code == 200
    assert res.json()["mode"] == "live"
    assert res.json()["summary"] == dict(requests=1, succeeded=1, failed=0, attempts=1, retries=0)
    assert len(calls) == 1


def test_live_runtime_accepts_one_key_and_defers_gateway_creation(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "test-only-secret")
    created = []

    class FakeGateway:
        def __init__(self):
            created.append(self)

    monkeypatch.setattr(runtime, "GeminiGateway", FakeGateway)
    selected = runtime.get_runtime("live")
    assert created == []  # The gateway is created only for a submitted task.
    assert isinstance(selected.gateway_factory("A"), FakeGateway)
    assert isinstance(selected.gateway_factory("B"), FakeGateway)
    assert len(created) == 2
    assert selected.sleeper is runtime.time.sleep


def test_live_runtime_rejects_empty_key_values(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    with pytest.raises(HTTPException) as raised:
        runtime.get_runtime("live")
    assert raised.value.status_code == 503
    assert raised.value.detail == {
        "code": "MODEL_NOT_CONFIGURED", "message": "Gemini API key is not configured"}


def test_ui_live_mode_posts_once_with_longer_timeout():
    body = {"mode": "live", "tasks": [], "summary": {
        "requests": 0, "succeeded": 0, "failed": 0, "attempts": 0, "retries": 0}}
    client = RecordingClient(response(body=body))
    assert submit_batch(client, {"tasks": []}, mode="live") == body
    assert client.calls == [("/analyze-batch?mode=live", {"tasks": []}, 45.0)]


def test_invalid_mode_is_422_before_gateway_calls():
    with TestClient(app) as client:
        res = client.post("/analyze-batch?mode=other", json={"tasks": []})
    assert res.status_code == 422
