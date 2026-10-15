"""同一 HTTP 替身网关先成功，再遇无资料，第二次不能发送请求。"""
import json

import httpx

from Week6.day37.code.qa_service import NO_CONTEXT_ANSWER
from Week6.day37.code.chunking import Chunk
from Week6.day37.code.citations import review_qa_result
from Week6.day37.code.gemini_gateway import GeminiGateway
from Week6.day37.code.qa_prompt import QA_INSTRUCTIONS
from Week6.day37.code.qa_service import answer_question


def test_success_then_no_context_does_not_send_another_post():
    # Arrange：本次测试自己的资料与请求记录；内层 handler 访问同一列表。
    chunk = Chunk("faq.txt", 0, 0, 8, "返品期限は30日")
    http_calls = []

    def handler(http_request):
        # MockTransport 传入真实形状的 HTTP 请求；假响应是供应商的 JSON 结构。
        http_calls.append(http_request)
        return httpx.Response(status_code=200, json={
            "status": "completed",
            "steps": [{"type": "model_output", "content": [
                {"type": "text", "text": "返品期限は30日です。[1]"},
            ]}],
        })

    # 两次问答共享这个网关对象；仅底层传输被替换，没有真实网络调用。
    gateway = GeminiGateway("test-model", api_key="fake-test-key", transport=httpx.MockTransport(handler))
    try:
        # Act：第一次有命中，会 POST；第二次无命中，在 complete 之前返回。
        qa_result1 = answer_question([chunk],"返品",2,100,gateway)
        qa_result2 = answer_question([chunk],"駐車場",2,100,gateway)
    finally:
        gateway.close()

    # Assert：分别检查完整答案与状态，不把供应商 completed 当成本地状态。
    assert qa_result1.status == "generated"
    assert qa_result1.answer == "返品期限は30日です。[1]"
    assert review_qa_result(qa_result1) == []
    assert qa_result2.status == "no_context"
    assert qa_result2.answer == NO_CONTEXT_ANSWER
    assert qa_result2.context.text == ""
    assert qa_result2.context.chunks == []
    assert review_qa_result(qa_result2) == []
    # 保留第一次记录，第二次不新增请求；请求体要读 .content，而非编码 Request。
    assert len(http_calls) == 1 == gateway.request_count
    payload = json.loads(http_calls[0].content)
    expected_payload = {
        "model": "test-model",
        "system_instruction": QA_INSTRUCTIONS,
        "input": json.dumps({
            "question": "返品", "context": "[1] faq.txt (0:8)\n返品期限は30日",
        }, ensure_ascii=False),
        "store": False,
    }
    assert payload == expected_payload
    assert gateway.client.is_closed == True
