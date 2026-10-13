"""Day32 边界：跳过首个长块后，仍使用后续短块完成一次调用。"""
import json

from Week5.day35.code.chunking import Chunk
from Week5.day35.code.model_client import RecordingGateway
from Week5.day35.code.qa_prompt import QA_INSTRUCTIONS
from Week5.day35.code.qa_service import answer_question


def test_skip_first_oversized_hit_and_call_with_later_evidence() -> None:
    # Arrange：同分的两块按长、短输入；短块恰好装满资料预算。
    text_1 = "返品" + "B" * 80
    text_2 = "返品期限は30日"
    chunk_1 = Chunk("long.txt",0,0,len(text_1),text_1)
    chunk_2 = Chunk("faq.txt",0,0,len(text_2),text_2)
    chunks = [chunk_1, chunk_2]
    # 浅拷贝创建新列表，里面仍引用同一批原 Chunk 对象。
    chunks_copy = chunks.copy()
    expected_context = "[1] faq.txt (0:8)\n返品期限は30日"
    gateway = RecordingGateway("返品期限は30日です。[1]")
    # Act：执行真实业务函数；网关使用不联网的记录替身。
    answer = answer_question(chunks,"返品",2,len(expected_context),gateway)
    # Assert：不仅核对状态，还核对完整返回文字。
    assert answer.status == "generated"
    assert answer.answer == gateway.raw
    assert answer.context.text == expected_context
    assert len(answer.context.text) <= len(expected_context)
    # 列表 == 检查恰好只有第二块；is 检查它就是原对象。
    assert answer.context.chunks == [chunk_2]
    assert answer.context.chunks[0] is chunk_2
    # 检查真正发送了什么，而不是仅看最终输出。
    assert len(gateway.calls)==1
    assert gateway.calls[0].instructions == QA_INSTRUCTIONS
    assert json.loads(gateway.calls[0].input)=={"question": "返品", "context": expected_context}
    # 完整列表相等检查数量/内容；逐项 is 检查对象顺序。
    assert chunks == chunks_copy
    assert len(chunks) == len(chunks_copy)
    assert all(
        current is original
        for current, original in zip(chunks, chunks_copy)
    )
