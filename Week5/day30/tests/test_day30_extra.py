"""The learner replaces this placeholder with a ranking boundary test."""
from Week5.day30.code.chunking import Chunk
from Week5.day30.code.retrieval import retrieve_chunks


def test_equal_scores_keep_input_order_after_top_k() -> None:
    chunks = []
    a = Chunk("z.txt", 0, 0, len("返品案内"), "返品案内")
    b = Chunk("a.txt", 0, 0, len("返品期限"), "返品期限")
    c = Chunk("m.txt", 0, 0, len("返品受付"), "返品受付")
    chunks.append(a)
    chunks.append(b)
    chunks.append(c)
    results = retrieve_chunks(chunks, "返品", 2)
    assert ["z.txt", "a.txt"] == [result.chunk.source_name for result in results]
    assert [1, 1] == [result.score for result in results]
    assert [a, b] == [result.chunk for result in results]
    assert results[0].chunk is a
    assert results[1].chunk is b
