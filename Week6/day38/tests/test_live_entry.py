"""预览及入口安全输出；不会向 Google 发送请求。"""

import json

import httpx
import pytest

from Week6.day38.code import run_live_qa


@pytest.mark.parametrize("case, would_call", [("A", True), ("B", True), ("C", False)])
def test_preview_never_creates_gateway(case, would_call, monkeypatch, capsys):
    def forbidden_gateway(*args, **kwargs):
        pytest.fail("预览不应创建真实网关")

    monkeypatch.setattr(run_live_qa, "GeminiGateway", forbidden_gateway)
    assert run_live_qa.main(["--case", case]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["mode"] == "preview"
    assert output["would_call_model"] is would_call
    assert output["gateway_calls"] == 0
    assert output["input"]["question"] == run_live_qa.QUESTIONS[case]
    assert output["input"]["context"] == output["context"]["text"]


def test_live_no_context_needs_no_key_or_gateway(monkeypatch, capsys):
    def forbidden_gateway(*args, **kwargs):
        pytest.fail("无资料时不应创建真实网关")

    monkeypatch.setattr(run_live_qa, "GeminiGateway", forbidden_gateway)
    assert run_live_qa.main(["--live", "--case", "C"]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "no_context"
    assert output["answer"] == "資料からは回答できません。"
    assert output["citation_errors"] == []
    assert output["gateway_calls"] == 0


def test_http_error_hides_body_and_closes_client(monkeypatch, capsys):
    closed = []

    class FailedGateway:
        def __init__(self, **kwargs):
            pass

        def complete(self, request):
            # 敏感哨兵确实在 action 的异常正文中；检查入口没有打印它。
            req = httpx.Request("POST", "https://example.invalid")
            response = httpx.Response(429, request=req, text="FAKE_PRIVATE_BODY_SENTINEL")
            raise httpx.HTTPStatusError("FAKE_PRIVATE_BODY_SENTINEL", request=req, response=response)

        def close(self):
            closed.append(True)

    monkeypatch.setattr(run_live_qa, "GeminiGateway", FailedGateway)
    assert run_live_qa.main(["--live"]) == 1
    captured = capsys.readouterr()
    assert json.loads(captured.out) == {"error": "http_error", "http_status": 429}
    assert "FAKE_PRIVATE_BODY_SENTINEL" not in captured.out + captured.err
    assert closed == [True]
