"""引用编号契约；替身回答来自测试输入，不是模型推理结果。"""

import pytest

from Week6.day36.code.chunking import Chunk
from Week6.day36.code.citations import (
    check_citations,
    extract_citation_ids,
    review_qa_result,
)
from Week6.day36.code.context import build_context
from Week6.day36.code.model_client import RecordingGateway
from Week6.day36.code.qa_service import NO_CONTEXT_ANSWER, answer_question
from Week6.day36.code.retrieval import RetrievalHit


def make_context(count: int):
    # 通过已完成的资料整理函数构造合法上下文，编号是 1 到 count。
    chunks = [Chunk(f"faq_{i}.txt", 0, 0, 2, "返品") for i in range(count)]
    return build_context([RetrievalHit(chunk, 1) for chunk in chunks], 10000)


@pytest.mark.parametrize(
    ("answer", "expected"),
    [("説明。[2][01][2]", [2, 1, 2]), ("引用なし", []), ("[abc][１][-1][1,2]", [])],
)
def test_provided_extractor(answer: str, expected: list[int]) -> None:
    # 此测试仅核对已提供的提取规则，学习者无需实现辅助函数。
    assert extract_citation_ids(answer) == expected


@pytest.mark.parametrize(
    ("count", "answer", "expected"),
    [
        (1, "返品期限は30日です。[1]", []),
        (2, "二つの資料。[2][1][2]", []),
        (1, "返品期限は30日です。", ["missing_citation"]),
        (1, "", ["missing_citation"]),
        (1, "[abc][１][-1][1,2]", ["missing_citation"]),
        (2, "回答。[99][2][99][0][2]", ["unknown_citation:99", "unknown_citation:0"]),
        (0, "回答。[1]", ["unknown_citation:1"]),
        (10, "十番目。[10]", []),
        (1, "先頭ゼロ。[01]", []),
    ],
)
def test_check_citations_contract(count: int, answer: str, expected: list[str]) -> None:
    context = make_context(count)
    before_text = context.text
    before_chunks = context.chunks.copy()
    # 执行核心检查；同一次 action 中既有合法编号也可能有非法编号。
    errors = check_citations(answer, context)
    # 完整列表断言覆盖错误内容、首次出现顺序及去重，不能只检查长度。
    assert errors == expected
    assert context.text == before_text
    assert context.chunks == before_chunks
    assert all(now is old for now, old in zip(context.chunks, before_chunks))


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("返品期限は30日です。[1]", []),
        ("返品期限は30日です。[99]", ["unknown_citation:99"]),
        ("返品期限は30日です。", ["missing_citation"]),
    ],
)
def test_review_generated_answer(raw: str, expected: list[str]) -> None:
    # 先走昨天已经完成的完整调用链，然后检查本次原返回文字。
    chunk = Chunk("faq.txt", 0, 0, 8, "返品期限は30日")
    gateway = RecordingGateway(raw)
    result = answer_question([chunk], "返品", 2, 100, gateway)
    assert review_qa_result(result) == expected
    # 有错误也不重写模型文字、不再次调用，generated 的含义保持不变。
    assert result.status == "generated"
    assert result.answer == raw
    assert result.context.chunks == [chunk]
    assert result.context.chunks[0] is chunk
    assert len(gateway.calls) == 1


def test_no_context_skips_citation_check(monkeypatch) -> None:
    # 若误检查无资料固定提示，这个替换函数会立即失败。
    def forbidden_check(answer, context):
        pytest.fail("no_context must skip check_citations")

    monkeypatch.setattr("Week6.day36.code.citations.check_citations", forbidden_check)
    gateway = RecordingGateway("不应使用的文字。[99]")
    result = answer_question([], "返品", 2, 100, gateway)
    assert review_qa_result(result) == []
    assert result.status == "no_context"
    assert result.answer == NO_CONTEXT_ANSWER
    assert result.context.chunks == []
    assert gateway.calls == []
