"""Completed Day31 boundary test, copied to preserve verified behavior."""

import pytest

from Week6.day37.code.chunking import Chunk
from Week6.day37.code.context import build_context
from Week6.day37.code.retrieval import RetrievalHit


def test_skip_middle_block_and_keep_contiguous_reference_numbers() -> None:
    # 跳过中间长块后仍纳入后续短块，资料编号连续且输入不变。
    text_a = "A"
    text_b = "B"*80
    text_c = "C"
    chunk_a = Chunk("a.txt", 0,0,len(text_a),text_a)
    chunk_b = Chunk("long.txt", 0,0,len(text_b),text_b)
    chunk_c = Chunk("c.txt", 0,0,len(text_c),text_c)
    hit_a = RetrievalHit(chunk_a, 1)
    hit_b = RetrievalHit(chunk_b, 1)
    hit_c = RetrievalHit(chunk_c, 1)
    hits = [hit_a, hit_b, hit_c]
    hits_copy = hits.copy()
    expected= "[1] a.txt (0:1)\nA\n\n[2] c.txt (0:1)\nC"
    context = build_context(hits,len(expected))
    assert context.text == expected
    assert context.chunks[0] is chunk_a
    assert context.chunks[1] is chunk_c
    assert len(context.text) <= len(expected)
    assert hits == hits_copy
    assert context.chunks == [chunk_a, chunk_c]
    assert all(
        current is original
        for current, original in zip(hits, hits_copy)
    )
