import json

import pytest

from Week6.day36.code.chunking import Chunk, Document, chunk_documents
from Week6.day36.code.context import ContextBundle
from Week6.day36.code.model_client import ModelGateway, RecordingGateway
from Week6.day36.code.qa_prompt import QA_INSTRUCTIONS
from Week6.day36.code.qa_service import NO_CONTEXT_ANSWER, QAResult, answer_question


def make_chunk(name: str, text: str) -> Chunk:
    # 辅助函数：按文字长度构造完整片段，文件名仅作为来源。
    return Chunk(name, 0, 0, len(text), text)


def test_success_makes_one_call_and_preserves_raw_answer_and_source() -> None:
    # 检查一次调用、请求字段、原返回文字、原片段身份和输入不变。
    faq = make_chunk("faq.txt", "返品期限は30日")
    hours = make_chunk("hours.txt", "営業時間は9時")
    chunks = [faq, hours]
    before = chunks.copy()
    gateway = RecordingGateway(" 返品期限は30日です。[1]\n")
    question = " 返品 期限 "
    result = answer_question(chunks, question, 2, 100, gateway)
    assert isinstance(result, QAResult)
    assert result.status == "generated"
    assert result.answer == gateway.raw
    assert result.context.text == "[1] faq.txt (0:8)\n返品期限は30日"
    assert result.context.chunks == [faq]
    assert result.context.chunks[0] is faq
    assert len(gateway.calls) == 1
    assert gateway.calls[0].instructions == QA_INSTRUCTIONS
    assert json.loads(gateway.calls[0].input) == {
        "question": question, "context": result.context.text,
    }
    assert chunks == before
    assert all(current is original for current, original in zip(chunks, before))


@pytest.mark.parametrize("case", ["empty_chunks", "no_hit", "budget_too_small"])
def test_no_usable_context_returns_fixed_answer_without_call(case: str, monkeypatch) -> None:
    # 三种无资料路径都跳过请求构造和网关调用，不能仅断言返回提示。
    chunks = [] if case == "empty_chunks" else [make_chunk("faq.txt", "返品期限は30日")]
    question = "駐車場" if case == "no_hit" else "返品"
    limit = 1 if case == "budget_too_small" else 100
    gateway = RecordingGateway("This must not be used")
    def unexpected_request(*args):
        raise AssertionError("No context must skip request construction")
    monkeypatch.setattr("Week6.day36.code.qa_service.build_qa_request", unexpected_request)
    result = answer_question(chunks, question, 2, limit, gateway)
    assert result == QAResult("no_context", NO_CONTEXT_ANSWER, ContextBundle("", []))
    assert gateway.calls == []


@pytest.mark.parametrize("question", ["", " ", "\n\t"])
def test_invalid_question_is_rejected_before_other_limits_or_calls(question: str) -> None:
    # 多个参数同时无效时，应先报空白问题，且网关调用仍为 0。
    gateway = RecordingGateway("unused")
    with pytest.raises(ValueError, match="^invalid_question$"):
        answer_question([], question, 0, 0, gateway)
    assert gateway.calls == []


@pytest.mark.parametrize("top_k", [0, -1])
def test_invalid_top_k_is_rejected_even_with_empty_chunks(top_k: int) -> None:
    # 没有输入片段也要拒绝非法 top_k，不得提前返回无资料结果。
    gateway = RecordingGateway("unused")
    with pytest.raises(ValueError, match="^invalid_top_k$"):
        answer_question([], "返品", top_k, 100, gateway)
    assert gateway.calls == []


@pytest.mark.parametrize("limit", [0, -1])
def test_invalid_context_limit_is_rejected_even_without_hits(limit: int) -> None:
    # 没有命中也要拒绝非法资料预算，且不能调用网关。
    gateway = RecordingGateway("unused")
    with pytest.raises(ValueError, match="^invalid_context_limit$"):
        answer_question([], "返品", 2, limit, gateway)
    assert gateway.calls == []


def test_gateway_error_propagates_unchanged_without_retry_or_fake_success() -> None:
    # 故意抛出同一个异常对象，用 is 检查原样传播并确认只调用一次。
    error = RuntimeError("mock_gateway_failure")

    class FailingGateway(ModelGateway):
        def __init__(self):
            self.calls = []

        def complete(self, request):
            self.calls.append(request)
            raise error

    gateway = FailingGateway()
    with pytest.raises(RuntimeError) as captured:
        answer_question([make_chunk("faq.txt", "返品期限は30日")], "返品", 2, 100, gateway)
    assert captured.value is error
    assert len(gateway.calls) == 1


def test_repeated_calls_do_not_reuse_previous_context_or_answer() -> None:
    # 先成功、再未命中；第二次不得沿用第一次答案或再次调用网关。
    chunks = [make_chunk("faq.txt", "返品期限は30日")]
    gateway = RecordingGateway("返品期限は30日です。[1]")
    first = answer_question(chunks, "返品", 2, 100, gateway)
    second = answer_question(chunks, "駐車場", 2, 100, gateway)
    assert first.status == "generated"
    assert second == QAResult("no_context", NO_CONTEXT_ANSWER, ContextBundle("", []))
    assert first.context.chunks is not second.context.chunks
    assert len(gateway.calls) == 1


def test_document_to_question_flow_stays_local_and_keeps_source() -> None:
    # 从自制文档到问答结果走完整本地链路，替身不调用真实模型。
    chunks = chunk_documents([Document("faq.txt", "返品期限は30日")], 20, 0)
    gateway = RecordingGateway("返品期限は30日です。[1]")
    result = answer_question(chunks, "返品 期限", 1, 100, gateway)
    assert result.status == "generated"
    assert result.answer == "返品期限は30日です。[1]"
    assert result.context.text == "[1] faq.txt (0:8)\n返品期限は30日"
    assert result.context.chunks == [chunks[0]]
    assert result.context.chunks[0] is chunks[0]
    assert len(gateway.calls) == 1
