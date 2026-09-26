"""Provided view tests. AppTest runs the script, not a real Chrome browser."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

from ..code import ui_client


UI = Path(__file__).parents[1] / "code" / "ui.py"


def test_initial_page_makes_no_api_calls(monkeypatch):
    calls = []
    monkeypatch.setattr(ui_client, "submit_batch", lambda *args: calls.append(args))
    at = AppTest.from_file(str(UI)).run()
    assert not at.exception
    assert len(at.text_area) == 2
    assert len(at.button) == 1
    assert calls == []


def test_submitted_page_displays_failed_row(monkeypatch):
    calls = []
    monkeypatch.setattr(ui_client, "build_payload", lambda *args: {"tasks": []})
    body = {"mode": "simulated", "summary": dict(requests=1, succeeded=0, failed=1, attempts=1, retries=0),
            "tasks": [{"task_id": "B", "report": {"attempts": 1, "result": {
                "ok": False, "raw": None, "error": "auth_error", "status_code": 403}}}]}

    def fake_submit(client, payload, mode="simulated"):
        calls.append(payload)
        return body

    monkeypatch.setattr(ui_client, "submit_batch", fake_submit)
    at = AppTest.from_file(str(UI)).run()
    at.button[0].click().run()
    assert not at.exception
    assert len(calls) == 1
    assert len(at.success) == 0
    assert "auth_error" in at.warning[0].value
    assert "403" in at.warning[0].value


def test_input_error_prevents_api_call(monkeypatch):
    calls = []

    def fail(*args):
        raise ui_client.DemoError("需求 A 不能为空")

    monkeypatch.setattr(ui_client, "build_payload", fail)
    monkeypatch.setattr(ui_client, "submit_batch", lambda *args: calls.append(args))
    at = AppTest.from_file(str(UI)).run()
    at.button[0].click().run()
    assert not at.exception
    assert at.error[0].value == "需求 A 不能为空"
    assert calls == []
