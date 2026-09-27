"""Learner-owned boundary: HTTP 200 must preserve a failed task report."""

from .test_ui_client import RecordingClient, response
from ..code.ui_client import submit_batch



def test_http_200_with_failed_task_is_still_a_report():
    body = {"mode": "simulated", "tasks": [{"task_id": "B", "report": {
        "result": {"ok": False, "raw": None, "error": "auth_error", "status_code": 403}, "attempts": 1}}],
     "summary": {"requests": 1, "succeeded": 0, "failed": 1, "attempts": 1, "retries": 0}}
    payload = {"tasks": [{"task_id": "B", "text": "確認"}],"max_attempts": 1}
    client = RecordingClient(response(body=body))
    assert submit_batch(client,payload) == body
    assert client.calls == [('/analyze-batch', payload, 5.0)]
