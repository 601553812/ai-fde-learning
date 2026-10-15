"""验证事先指定的原句与来源、评分分母和输入保留；不评价模型答案。"""

import json
from dataclasses import asdict

import pytest

from Week6.day37.code import run_eval_demo
from Week6.day37.code.chunking import Chunk
from Week6.day37.code.context import ContextBundle, build_context
from Week6.day37.code.eval_cases import evaluation_cases, evaluation_chunks, evaluation_documents
from Week6.day37.code.retrieval import RetrievalHit
from Week6.day37.code.retrieval_eval import EvidenceCheck, check_evidence, summarize_evidence


def context_for(source, text):
    # 用真实build_context建立文字与原片段一致的输入，不手写矛盾的bundle。
    chunk = Chunk(source, 7, 0, len(text), text)
    return build_context([RetrievalHit(chunk, 1)], 500)


@pytest.mark.parametrize("source,text,expected", [
    ("returns_faq.txt", "返品期限は30日です。", True),
    ("other.txt", "返品期限は30日です。", False),
    ("returns_faq.txt", "返品期限は90日です。", False),
    ("returns_faq.txt", "返品期限は30日です", False),
])
def test_check_requires_source_and_full_quote_in_same_chunk(source, text, expected):
    case = evaluation_cases()[0]
    context = context_for(source, text)
    before = asdict(context)
    check = check_evidence(case, context)
    # 同名文件不够，其他文件同一句也不够；两个条件必须同时满足。
    assert check.evidence_found is expected
    assert check.case is case
    assert check.context is context
    assert asdict(context) == before


def test_empty_context_with_expected_evidence_is_miss():
    assert check_evidence(evaluation_cases()[0], ContextBundle("", [])).evidence_found is False


@pytest.mark.parametrize("with_context", [True, False])
def test_no_known_answer_is_unscored_even_with_related_context(with_context):
    context = context_for("returns_faq.txt", "返品期限は30日です。") if with_context else ContextBundle("", [])
    # 没有标准证据，不因存在或不存在相关片段就判合理拒答。
    assert check_evidence(evaluation_cases()[4], context).evidence_found is None


def test_source_and_quote_cannot_be_combined_across_two_chunks():
    first = Chunk("returns_faq.txt", 0, 0, 5, "返品の案内")
    text = "返品期限は30日です。"
    second = Chunk("other.txt", 0, 0, len(text), text)
    context = build_context([RetrievalHit(first, 1), RetrievalHit(second, 1)], 500)
    assert check_evidence(evaluation_cases()[0], context).evidence_found is False


def test_search_continues_after_first_nonmatching_chunk():
    first = Chunk("returns_faq.txt", 0, 0, 5, "返品の案内")
    text = "返品期限は30日です。"
    second = Chunk("returns_faq.txt", 1, 5, 5 + len(text), text)
    context = build_context([RetrievalHit(first, 1), RetrievalHit(second, 1)], 500)
    before = asdict(context)
    check = check_evidence(evaluation_cases()[0], context)
    assert check.evidence_found is True
    assert check.context is context
    assert context.chunks[0] is first
    assert context.chunks[1] is second
    assert asdict(context) == before


@pytest.mark.parametrize("values,expected", [
    ([True, False, None], (3, 2, 1, 1, 1, 0.5)),
    ([], (0, 0, 0, 0, 0, None)),
    ([None, None], (2, 0, 0, 0, 2, None)),
    ([False], (1, 1, 0, 1, 0, 0.0)),
    ([True, True], (2, 2, 2, 0, 0, 1.0)),
])
def test_summary_denominator_excludes_unscored(values, expected):
    # 这里直接构造合法检查记录，单独验证汇总，不让TODO1遮住TODO2。
    cases = evaluation_cases()
    checks = [EvidenceCheck(cases[4] if value is None else cases[0], ContextBundle("", []), value) for value in values]
    before = [asdict(check) for check in checks]
    result = summarize_evidence(checks)
    assert asdict(result) == dict(zip(
        ("total", "evaluated", "hits", "misses", "unscored", "hit_rate"), expected,
    ))
    assert [asdict(check) for check in checks] == before


def test_summary_does_not_accumulate_between_calls():
    case = evaluation_cases()[0]
    first = summarize_evidence([EvidenceCheck(case, ContextBundle("", []), True)])
    second = summarize_evidence([])
    assert asdict(first) == {"total": 1, "evaluated": 1, "hits": 1, "misses": 0, "unscored": 0, "hit_rate": 1.0}
    assert asdict(second) == {"total": 0, "evaluated": 0, "hits": 0, "misses": 0, "unscored": 0, "hit_rate": None}
    assert first is not second


def test_fixed_dataset_expectations_really_exist_in_source_documents():
    docs = {doc.source_name: doc.text for doc in evaluation_documents()}
    cases = evaluation_cases()
    assert [case.case_id for case in cases] == ["R1", "R2", "R3", "R4", "N1", "N2"]
    for case in cases[:4]:
        assert case.expected_evidence.quote in docs[case.expected_evidence.source_name]
    assert [case.expected_evidence for case in cases[4:]] == [None, None]
    assert len(evaluation_chunks()) == 3


def test_demo_reports_existing_keyword_baseline_and_no_model_calls(capsys):
    assert run_eval_demo.main([]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["dataset_origin"] == "provided_synthetic_faq_v1"
    assert report["top_k"] == 2 and report["max_chars"] == 500
    assert report["gateway_calls"] == 0
    assert [row["check"]["case"]["case_id"] for row in report["results"]] == ["R1", "R2", "R3", "R4", "N1", "N2"]
    assert [row["check"]["evidence_found"] for row in report["results"]] == [True, True, True, False, None, None]
    assert [row["retrieved_count"] for row in report["results"]] == [1, 1, 1, 0, 1, 0]
    assert report["summary"] == {"total": 6, "evaluated": 4, "hits": 3, "misses": 1, "unscored": 2, "hit_rate": 0.75}
