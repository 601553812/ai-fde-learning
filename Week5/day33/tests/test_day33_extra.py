"""检索命中两块，但实际只发送一块时检查引用编号。"""
import json

from Week5.day33.code.chunking import Chunk
from Week5.day33.code.citations import review_qa_result
from Week5.day33.code.model_client import RecordingGateway
from Week5.day33.code.qa_service import answer_question


def test_citations_use_sent_context_after_skipping_long_hit() -> None:
    # Arrange：长块在前，两块同分；预算只允许纳入后面的短块。
    text_1 = "返品" + "B" * 80
    text_2 = "返品期限は30日"
    long_chunk = Chunk("long.txt",0,0,len(text_1),text_1)
    faq_chunk = Chunk("faq.txt",0,0,len(text_2),text_2)
    expected_context = "[1] faq.txt (0:8)\n返品期限は30日"
    chunks = [long_chunk,faq_chunk]
    gateway = RecordingGateway("返品期限は30日です。[2][2][0]")
    # Act：先完成问答，再用本次结果检查引用；替身不联网。
    qa_result = answer_question(chunks, "返品",2,len(expected_context),gateway)
    problems = review_qa_result(qa_result)
    # Assert：完整列表检查去重和顺序；原回答与一次调用保持不变。
    assert problems == ["unknown_citation:2", "unknown_citation:0"]
    assert qa_result.status == "generated"
    assert qa_result.answer == "返品期限は30日です。[2][2][0]"
    assert len(gateway.calls) == 1
    # 真正发送的是编号为 [1] 的短块，同时核对其原对象身份。
    assert qa_result.context.text == expected_context
    assert qa_result.context.chunks == [faq_chunk]
    assert qa_result.context.chunks[0] is faq_chunk
    # 解码网关实际收到的 JSON 字符串，对比完整输入字段。
    assert json.loads(gateway.calls[0].input)=={"question": "返品", "context": expected_context}
