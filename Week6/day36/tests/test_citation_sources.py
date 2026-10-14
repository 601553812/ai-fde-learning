"""资料定位契约：测试能找到哪个片段，不能替代人工事实核查。"""

import json

import pytest

from Week6.day36.code.cases import sample_chunks
from Week6.day36.code.chunking import Chunk
from Week6.day36.code.citation_sources import find_cited_chunks
from Week6.day36.code.citations import check_citations
from Week6.day36.code.context import build_context
from Week6.day36.code.retrieval import RetrievalHit
from Week6.day36.code import run_source_demo


@pytest.mark.parametrize(
    "count,answer,positions",
    [
        (1, "説明。[1]", [0]),
        (2, "説明。[2][1][2]", [1, 0]),
        (2, "説明。[99][2][0][2][1]", [1, 0]),
        (2, "資料からは回答できません。", []),
        (2, "", []),
        (1, "説明。[01][1]", [0]),
        (2, "説明。[99][0]", []),
        (0, "説明。[1]", []),
    ],
)
def test_find_cited_chunks_contract(count, answer, positions):
    # 用已有函数建立合法 context；positions 是预期的 Python 列表下标。
    chunks = [Chunk(f"faq_{i}.txt", 0, 0, 2, "返品") for i in range(count)]
    context = build_context([RetrievalHit(chunk, 1) for chunk in chunks], 500)
    before_text = context.text
    before_chunks = context.chunks.copy()
    result = find_cited_chunks(answer, context)
    # 完整顺序与对象身份同时断言，能发现多出、少取、错序或重建对象。
    assert result == [chunks[i] for i in positions]
    assert all(actual is chunks[i] for actual, i in zip(result, positions))
    assert context.text == before_text
    assert context.chunks == before_chunks
    assert all(actual is original for actual, original in zip(context.chunks, before_chunks))


@pytest.mark.parametrize("answer", ["返品期限は30日です。[1]", "返品期限は90日です。[1]"])
def test_locating_source_does_not_check_answer_facts(answer):
    # 两个回答引用同一个存在的编号；只有人工比对才能看出 90 日与原文冲突。
    chunk = sample_chunks()[0]
    context = build_context([RetrievalHit(chunk, 1)], 500)
    result = find_cited_chunks(answer, context)
    assert result == [chunk]
    assert result[0] is chunk
    assert result[0].text == "返品期限は30日です。\n開封済みの商品は返品できません。"
    assert check_citations(answer, context) == []


def test_provided_demo_keeps_answer_and_evidence_separate(capsys):
    assert run_source_demo.main([]) == 0
    rows = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert [row["case"] for row in rows] == ["A", "B", "wrong_90"]
    assert [row["answer_origin"] for row in rows] == ["recorded_day34", "recorded_day34", "synthetic"]
    assert [row["gateway_calls"] for row in rows] == [0, 0, 0]
    assert rows[0]["answer"] == "返品期限は30日です。[1]"
    assert rows[1]["cited_chunks"] == []
    assert len(rows[1]["context"]["chunks"]) == 1
    assert rows[1]["citation_errors"] == ["missing_citation"]
    assert rows[2]["answer"] == "返品期限は90日です。[1]"
    assert rows[2]["cited_chunks"] == rows[0]["cited_chunks"]
