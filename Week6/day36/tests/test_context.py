import pytest

from Week6.day36.code.chunking import Chunk, Document, chunk_documents
from Week6.day36.code.context import ContextBundle, build_context
from Week6.day36.code.retrieval import RetrievalHit, retrieve_chunks


def hit(name: str, text: str, start: int = 0, score: int = 1) -> RetrievalHit:
    # 辅助函数：把一个原片段包装成带分数的命中，简化测试准备。
    return RetrievalHit(Chunk(name, 0, start, start + len(text), text), score)


def test_one_block_preserves_whitespace_offsets_and_identity() -> None:
    # 检查原文空白、来源范围和原对象身份，而不仅是文字值相等。
    item = hit("faq.txt", " 返品\n30日 ", start=7)
    result = build_context([item], 100)
    assert isinstance(result, ContextBundle)
    assert result.text == "[1] faq.txt (7:15)\n 返品\n30日 "
    assert result.chunks == [item.chunk]
    assert result.chunks[0] is item.chunk


def test_input_order_is_kept_without_resorting_by_score_or_name() -> None:
    # 资料整理只沿用命中顺序，不能按分数或文件名再次排序。
    items = [hit("z.txt", "返品", score=1), hit("a.txt", "30日", score=9)]
    result = build_context(items, 100)
    assert result.text == "[1] z.txt (0:2)\n返品\n\n[2] a.txt (0:3)\n30日"
    assert result.chunks == [item.chunk for item in items]
    assert all(result.chunks[i] is items[i].chunk for i in range(2))


def test_complete_rendered_block_fits_exact_limit() -> None:
    # 预算恰好等于完整头部和原文的长度时，整块允许纳入。
    item = hit("a.txt", "返品")
    expected = "[1] a.txt (0:2)\n返品"
    result = build_context([item], len(expected))
    assert result.text == expected
    assert len(result.text) == len(expected)
    assert result.chunks[0] is item.chunk


def test_one_character_short_does_not_truncate_text_or_leave_reference() -> None:
    # 少一个字符就放不下；不能截断原文或留下无原文的编号。
    item = hit("a.txt", "返品")
    result = build_context([item], len("[1] a.txt (0:2)\n返品") - 1)
    assert result == ContextBundle("", [])


def test_separator_counts_toward_limit() -> None:
    # 块间两个换行也占预算；分别检查少一个字符与恰好放下。
    items = [hit("a.txt", "返品"), hit("b.txt", "受付")]
    first = "[1] a.txt (0:2)\n返品"
    second = "[2] b.txt (0:2)\n受付"
    result = build_context(items, len(first) + len(second) + 1)
    assert result.text == first
    assert result.chunks == [items[0].chunk]
    complete = build_context(items, len(first) + len(second) + 2)
    assert complete.text == first + "\n\n" + second
    assert complete.chunks == [item.chunk for item in items]


@pytest.mark.parametrize("limit", [0, -1])
def test_invalid_limit_is_rejected_even_without_hits(limit: int) -> None:
    # 空命中也必须校验预算，不能提前返回绕过异常。
    with pytest.raises(ValueError, match="^invalid_context_limit$"):
        build_context([], limit)


def test_empty_input_and_all_oversized_return_empty_bundle() -> None:
    # 无命中与所有块超预算都返回空上下文，返回值不能区分两种原因。
    assert build_context([], 100) == ContextBundle("", [])
    assert build_context([hit("faq.txt", "返品")], 1) == ContextBundle("", [])


def test_repeated_calls_have_independent_results_and_leave_hits_unchanged() -> None:
    # 连续调用的结果列表独立，输入列表及原片段对象不被修改。
    items = [hit("a.txt", "返品")]
    before = items.copy()
    first = build_context(items, 100)
    second = build_context([], 100)
    assert first.text == "[1] a.txt (0:2)\n返品"
    assert second == ContextBundle("", [])
    assert first.chunks is not second.chunks
    assert items == before
    assert items[0] is before[0]
    assert first.chunks[0] is before[0].chunk


def test_chunk_retrieve_context_local_flow() -> None:
    # 连接切块、检索和资料整理，核对完整来源与原对象对应。
    documents = [Document("faq.txt", "返品期限は30日"), Document("hours.txt", "営業時間は9時")]
    chunks = chunk_documents(documents, 30, 0)
    hits = retrieve_chunks(chunks, "返品 30日", 2)
    result = build_context(hits, 100)
    assert result.text == "[1] faq.txt (0:8)\n返品期限は30日"
    assert result.chunks == [chunks[0]]
    assert result.chunks[0] is chunks[0]
