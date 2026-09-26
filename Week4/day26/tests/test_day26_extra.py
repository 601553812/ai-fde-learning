"""Learner-owned Day26 boundary test."""


from fastapi.testclient import TestClient

from ..code.app import app
from ..code import runtime
from ..code.fakes import SequenceGateway, RecordingSleeper

created = []

def fake_gateway():
    created.append("created")
    return SequenceGateway([])




def test_missing_key_rejects_live_request_without_gateway_call(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY",raising=False)
    monkeypatch.delenv("GEMINI_API_KEY",raising=False)
    monkeypatch.setattr(runtime, "GeminiGateway", fake_gateway)
    body = {
        "tasks": [
            {"task_id": "A", "text": "一覧をCSVで出力する。"}
        ],
        "max_attempts": 1,
    }
    response = TestClient(app).post(
        "/analyze-batch?mode=live",
        json=body,
    )
    assert response.status_code == 503
    assert response.json()["detail"] == {"code": "MODEL_NOT_CONFIGURED", "message": "Gemini API key is not configured"}
    assert created == []

