"""本日适配器契约：HTTP 请求由 MockTransport 接收，所有测试均离线。"""

import copy
import json

import httpx
import pytest

from Week6.day38.code.gemini_gateway import (
    ENDPOINT, GeminiGateway, build_gemini_payload, extract_answer,
)
from Week6.day38.code.qa_prompt import ModelRequest


def completed(*texts):
    # 这是供应商响应的形状；不是最终 QAResult，也不是模型真实结果。
    return {"status": "completed", "steps": [{"type": "model_output", "content": [
        {"type": "text", "text": text} for text in texts
    ]}]}


def test_payload_preserves_request_and_separates_rules():
    request = ModelRequest("只根据资料回答", '{"question":"返品", "context":"[1] 資料"}')
    body = build_gemini_payload(request, "test-model")
    # 完整比较禁止额外历史/工具字段，原 input 仍是字符串，不能二次编码。
    assert body == {"model": "test-model", "system_instruction": request.instructions,
                    "input": request.input, "store": False}
    assert request == ModelRequest("只根据资料回答", '{"question":"返品", "context":"[1] 資料"}')


def test_extract_last_output_preserves_text_and_input():
    data = completed("旧回答。[99]")
    data["steps"].extend([
        {"type": "thought", "text": "这不是最终回答"},
        {"type": "model_output", "content": [
            {"type": "text", "text": " 返品期限は"},
            {"type": "image", "uri": "ignored"},
            {"type": "text", "text": "30日です。[1]\n"},
        ]},
        {"type": "thought", "text": "也不作为回答"},
    ])
    before = copy.deepcopy(data)
    assert extract_answer(data) == " 返品期限は30日です。[1]\n"
    assert data == before  # 不能 pop 或 reverse 原列表。


def test_extract_ignores_text_field_on_non_text_part():
    # 原 TODO 要求按 type 选择文字片段；不能仅凭有 text 字段就拼接。
    # 将不应输出的值保留在 action 输入中，断言完整回答不包含该片段。
    data = completed("返品期限は30日です。[1]")
    data["steps"][0]["content"].append({
        "type": "image", "text": "这段不是 text 类型，不应进入回答",
    })
    before = copy.deepcopy(data)
    assert extract_answer(data) == "返品期限は30日です。[1]"
    assert data == before


@pytest.mark.parametrize("status", [None, "in_progress", "failed", "incomplete"])
def test_unfinished_response_is_not_an_answer(status):
    data = completed("已存在的部分文字。[1]")
    data["status"] = status
    with pytest.raises(ValueError, match="^model_not_completed$"):
        extract_answer(data)


@pytest.mark.parametrize("steps", [[], [{"type": "thought"}],
    [{"type": "model_output", "content": []}],
    [{"type": "model_output", "content": [{"type": "text", "text": " \n"}]}],
    [{"type": "model_output", "content": [{"type": "image", "uri": "ignored"}]}],
])
def test_completed_without_answer_is_rejected(steps):
    with pytest.raises(ValueError, match="^missing_model_text$"):
        extract_answer({"status": "completed", "steps": steps})


def test_empty_last_output_does_not_fall_back_to_old_answer():
    data = completed("旧答案。[1]")
    data["steps"].append({"type": "model_output", "content": []})
    with pytest.raises(ValueError, match="^missing_model_text$"):
        extract_answer(data)


def test_gateway_sends_one_post_and_returns_answer():
    calls = []

    def handler(request):
        # 替换 HTTP 传输而非 complete：本日两个核心函数仍实际执行。
        calls.append(request)
        return httpx.Response(200, json=completed("返品期限は30日です。[1]"))

    request = ModelRequest("规则", "原输入")
    gateway = GeminiGateway("test-model", api_key="fake-test-key", transport=httpx.MockTransport(handler))
    try:
        assert gateway.complete(request) == "返品期限は30日です。[1]"
        assert gateway.request_count == 1
        assert len(calls) == 1
        assert calls[0].method == "POST" and str(calls[0].url) == ENDPOINT
        assert calls[0].headers["x-goog-api-key"] == "fake-test-key"
        assert json.loads(calls[0].content) == {"model": "test-model",
            "system_instruction": "规则", "input": "原输入", "store": False}
    finally:
        gateway.close()
    assert gateway.client.is_closed


@pytest.mark.parametrize("http_status", [403, 429, 500])
def test_http_errors_propagate_without_retry(http_status):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(http_status, json={"error": "fake private response"})

    gateway = GeminiGateway(api_key="fake-test-key", transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(httpx.HTTPStatusError):
            gateway.complete(ModelRequest("规则", "原输入"))
        assert len(calls) == gateway.request_count == 1
    finally:
        gateway.close()


def test_missing_key_rejected_before_client_creation(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "  ")

    def forbidden_client(*args, **kwargs):
        pytest.fail("无密钥时不应创建 HTTP 客户端")

    monkeypatch.setattr("Week6.day38.code.gemini_gateway.httpx.Client", forbidden_client)
    with pytest.raises(ValueError, match="^missing_api_key$"):
        GeminiGateway()
