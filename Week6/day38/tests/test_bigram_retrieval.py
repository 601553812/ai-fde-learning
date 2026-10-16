"""验证新检索规则与边界，不通过修改旧检索器取得通过。"""

from dataclasses import asdict

import pytest

from Week6.day38.code.bigram_retrieval import character_bigrams, retrieve_bigrams
from Week6.day38.code.chunking import Chunk
from Week6.day38.code.eval_cases import evaluation_cases, evaluation_chunks
from Week6.day38.code.retrieval import RetrievalHit


def make_chunk(name, text):
    return Chunk(name, 0, 0, len(text), text)


@pytest.mark.parametrize("text,expected", [
    ("ABAB", {"ab", "ba"}),
    ("配送 日数。", {"配送", "日数"}),
    ("A!B", set()),
    ("猫", set()),
    ("パスワード", {"パス", "スワ", "ワー", "ード"}),
])
def test_supplied_pair_helper(text, expected):
    # 已提供的辅助函数也固定其行为，避免对跨空白/标点的处理产生歧义。
    assert character_bigrams(text) == expected


def test_natural_japanese_question_recovers_original_source():
    chunks = evaluation_chunks()
    before = [asdict(chunk) for chunk in chunks]
    originals = chunks.copy()
    hits = retrieve_bigrams(chunks, evaluation_cases()[3].question, 2)
    # R4共同字符对为パス/スワ/ワー/ード/変更，全部来自同一个原片段。
    assert hits == [RetrievalHit(originals[2], 5)]
    assert hits[0].chunk is originals[2]
    assert [asdict(chunk) for chunk in chunks] == before
    assert all(current is original for current, original in zip(chunks, originals))


def test_rank_before_top_k_and_do_not_sort_input():
    chunks = [make_chunk("first", "ab"), make_chunk("second", "abcd")]
    before = [asdict(chunk) for chunk in chunks]
    hits = retrieve_bigrams(chunks, "abcd", 1)
    assert hits == [RetrievalHit(chunks[1], 3)]
    assert [asdict(chunk) for chunk in chunks] == before


def test_ties_follow_input_order_and_repeated_pairs_count_once():
    chunks = [make_chunk("z", "ABABAB"), make_chunk("a", "baba")]
    # 只有ab/ba两种共同对；不能按出现次数或文件名给同分结果重排。
    assert retrieve_bigrams(chunks, "ABAB", 2) == [
        RetrievalHit(chunks[0], 2), RetrievalHit(chunks[1], 2),
    ]


def test_source_filename_does_not_contribute_to_score():
    assert retrieve_bigrams([make_chunk("パスワード.txt", "返品期限")], "パスワード", 2) == []


@pytest.mark.parametrize("query", ["猫", "! ?", "未登録"])
def test_valid_query_without_shared_pairs_returns_empty(query):
    assert retrieve_bigrams(evaluation_chunks(), query, 2) == []


@pytest.mark.parametrize("query,top_k,message", [
    (" \t", 1, "invalid_query"),
    ("返品", 0, "invalid_top_k"),
    ("返品", -1, "invalid_top_k"),
    (" ", 0, "invalid_query"),
])
def test_validation_including_order(query, top_k, message):
    with pytest.raises(ValueError, match=f"^{message}$"):
        retrieve_bigrams([], query, top_k)


def test_valid_empty_chunks_returns_empty():
    assert retrieve_bigrams([], "返品", 2) == []
