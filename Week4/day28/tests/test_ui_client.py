"""Day24 contracts: no sockets, credentials or external model requests."""

from copy import deepcopy

import httpx
import pytest

from ..code.ui_client import DemoError, build_payload, submit_batch


def test_payload_two_tasks_trim_edges_keep_internal_newline():
    assert build_payload("  CSV出力\n3秒以内  ", "  文字コード確認  ", 1) == {
        "tasks": [{"task_id": "A", "text": "CSV出力\n3秒以内"},
                  {"task_id": "B", "text": "文字コード確認"}], "max_attempts": 1}


def test_payload_optional_blank_b():
    assert build_payload("one", " \n ", 2) == {
        "tasks": [{"task_id": "A", "text": "one"}], "max_attempts": 2}


@pytest.mark.parametrize("text_a", ["", " \n\t "])
def test_payload_a_required(text_a):
    with pytest.raises(DemoError, match="^需求 A 不能为空$"):
        build_payload(text_a, "two", 3)


@pytest.mark.parametrize("slot", ["A", "B"])
def test_payload_length_limit(slot):
    args = ("x" * 2001, "") if slot == "A" else ("one", "x" * 2001)
    with pytest.raises(DemoError, match=f"^需求 {slot} 不能超过 2000 字符$"):
        build_payload(*args, 3)


def test_payload_exact_limit_after_trim():
    assert len(build_payload(" " + "日" * 2000 + " ", "", 3)["tasks"][0]["text"]) == 2000


class RecordingClient:
    """A normal object with the one method submit_batch uses."""

    def __init__(self, outcome):
        self.outcome = outcome
        self.calls = []

    def post(self, url, *, json, timeout):
        self.calls.append((url, deepcopy(json), timeout))
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return self.outcome


def response(status=200, *, body=None, text=None):
    request = httpx.Request("POST", "http://test/analyze-batch")
    if text is not None:
        return httpx.Response(status, text=text, request=request)
    return httpx.Response(status, json=body, request=request)


def test_submit_preserves_report_and_posts_once():
    body = {"mode": "simulated", "tasks": [], "summary": {
        "requests": 0, "succeeded": 0, "failed": 0, "attempts": 0, "retries": 0}}
    client = RecordingClient(response(body=body))
    payload = {"tasks": [], "max_attempts": 1}
    before = deepcopy(payload)
    assert submit_batch(client, payload) == body
    assert client.calls == [("/analyze-batch", before, 5.0)]
    assert payload == before


@pytest.mark.parametrize("status", [422, 500])
def test_submit_http_error_before_json_decode(status):
    client = RecordingClient(response(status, text="not-json"))
    with pytest.raises(DemoError, match=f"^接口请求失败（HTTP {status}）$"):
        submit_batch(client, {"tasks": []})
    assert len(client.calls) == 1


@pytest.mark.parametrize("error", [httpx.ConnectError("private detail"), httpx.ReadTimeout("private detail")])
def test_submit_transport_error_is_safe_and_not_retried(error):
    client = RecordingClient(error)
    with pytest.raises(DemoError, match="^无法连接接口或请求超时，请检查本地 API 服务$"):
        submit_batch(client, {"tasks": []})
    assert len(client.calls) == 1


def test_submit_invalid_json():
    client = RecordingClient(response(text="not-json"))
    with pytest.raises(DemoError, match="^接口未返回合法 JSON$"):
        submit_batch(client, {"tasks": []})


def test_submit_unknown_bug_propagates():
    client = RecordingClient(RuntimeError("test bug"))
    with pytest.raises(RuntimeError, match="^test bug$"):
        submit_batch(client, {"tasks": []})
