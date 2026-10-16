import pytest

from Week6.day38.code.chunking import Chunk, Document, chunk_documents
from Week6.day38.code.retrieval import RetrievalHit, retrieve_chunks


def make_chunk(name: str, index: int, text: str) -> Chunk:
    # 辅助函数：按文字长度构造完整片段，文件名仅作为来源。
    return Chunk(name, index, 0, len(text), text)


def test_one_japanese_phrase_returns_original_chunk() -> None:
    # 日文词项命中时返回原片段，保留来源与对象身份。
    chunks = chunk_documents([Document("faq.txt", "返品期限は30日です。")], 20, 0)
    assert retrieve_chunks(chunks, "返品期限", 1) == [RetrievalHit(chunks[0], 1)]


def test_two_terms_rank_more_matches_first() -> None:
    # 两个不同词项都匹配的片段，应排在只匹配一个的片段前。
    chunks = [
        make_chunk("a.txt", 0, "返品の案内"),
        make_chunk("b.txt", 0, "30日の期限"),
        make_chunk("c.txt", 0, "返品は30日以内"),
    ]
    assert retrieve_chunks(chunks, "返品 30日", 3) == [
        RetrievalHit(chunks[2], 2),
        RetrievalHit(chunks[0], 1),
        RetrievalHit(chunks[1], 1),
    ]


def test_casefold_and_duplicate_terms_do_not_inflate_score() -> None:
    # 大小写归一化并去重，重复问题词项不能增加分数。
    chunks = [make_chunk("faq.txt", 0, "Refund refund POLICY")]
    assert retrieve_chunks(chunks, "REFUND refund policy", 1) == [
        RetrievalHit(chunks[0], 2)
    ]


def test_top_k_applies_after_ranking() -> None:
    # 先按匹配分数排序，再截取 top_k，不能先截断输入。
    chunks = [make_chunk("a", 0, "A"), make_chunk("b", 0, "A B"), make_chunk("c", 0, "A B C")]
    assert retrieve_chunks(chunks, "A B C", 2) == [
        RetrievalHit(chunks[2], 3), RetrievalHit(chunks[1], 2)
    ]


def test_no_match_returns_empty_and_does_not_invent_an_answer() -> None:
    # 未匹配原文时返回空命中，不凭文件名或其他内容构造命中。
    chunks = [make_chunk("faq.txt", 0, "返品期限は30日")]
    assert retrieve_chunks(chunks, "営業時間", 2) == []


@pytest.mark.parametrize(
    "query,top_k,message",
    [("  ", 1, "invalid_query"), ("返品", 0, "invalid_top_k"), ("返品", -1, "invalid_top_k")],
)
def test_invalid_input_raises(query: str, top_k: int, message: str) -> None:
    # 参数化检查无效问题或检索上限对应的固定异常。
    with pytest.raises(ValueError, match=f"^{message}$"):
        retrieve_chunks([], query, top_k)


def test_empty_chunks_with_valid_arguments_returns_empty() -> None:
    # 合法参数配合空片段列表，应得到空命中列表。
    assert retrieve_chunks([], "返品", 2) == []
