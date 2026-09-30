import pytest

from Week5.day30.code.chunking import Chunk, Document, chunk_documents
from Week5.day30.code.retrieval import RetrievalHit, retrieve_chunks


def make_chunk(name: str, index: int, text: str) -> Chunk:
    return Chunk(name, index, 0, len(text), text)


def test_one_japanese_phrase_returns_original_chunk() -> None:
    chunks = chunk_documents([Document("faq.txt", "返品期限は30日です。")], 20, 0)
    assert retrieve_chunks(chunks, "返品期限", 1) == [RetrievalHit(chunks[0], 1)]


def test_two_terms_rank_more_matches_first() -> None:
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
    chunks = [make_chunk("faq.txt", 0, "Refund refund POLICY")]
    assert retrieve_chunks(chunks, "REFUND refund policy", 1) == [
        RetrievalHit(chunks[0], 2)
    ]


def test_top_k_applies_after_ranking() -> None:
    chunks = [make_chunk("a", 0, "A"), make_chunk("b", 0, "A B"), make_chunk("c", 0, "A B C")]
    assert retrieve_chunks(chunks, "A B C", 2) == [
        RetrievalHit(chunks[2], 3), RetrievalHit(chunks[1], 2)
    ]


def test_no_match_returns_empty_and_does_not_invent_an_answer() -> None:
    chunks = [make_chunk("faq.txt", 0, "返品期限は30日")]
    assert retrieve_chunks(chunks, "営業時間", 2) == []


@pytest.mark.parametrize(
    "query,top_k,message",
    [("  ", 1, "invalid_query"), ("返品", 0, "invalid_top_k"), ("返品", -1, "invalid_top_k")],
)
def test_invalid_input_raises(query: str, top_k: int, message: str) -> None:
    with pytest.raises(ValueError, match=f"^{message}$"):
        retrieve_chunks([], query, top_k)


def test_empty_chunks_with_valid_arguments_returns_empty() -> None:
    assert retrieve_chunks([], "返品", 2) == []
