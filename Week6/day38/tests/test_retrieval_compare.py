"""逐例对照避免总分掩盖退步；None不当作False。"""

import json
from dataclasses import asdict

import pytest

from Week6.day38.code.eval_cases import evaluation_cases, evaluation_chunks
from Week6.day38.code.retrieval_compare import classify_change, compare_retrieval
from Week6.day38.code import run_compare_demo


@pytest.mark.parametrize("before,after,expected", [
    (False, True, "improved"), (True, False, "regressed"),
    (True, True, "unchanged"), (False, False, "unchanged"),
    (None, None, "unscored"), (None, True, "unscored"),
    (False, None, "unscored"), (True, None, "unscored"),
    (None, False, "unscored"),
])
def test_change_table(before, after, expected):
    assert classify_change(before, after) == expected


def test_same_fixed_cases_show_r4_improvement_without_other_regressions():
    chunks, cases = evaluation_chunks(), evaluation_cases()
    before_chunks = [asdict(chunk) for chunk in chunks]
    before_cases = [asdict(case) for case in cases]
    report = compare_retrieval(chunks, cases)
    rows = report["results"]
    assert [row["case_id"] for row in rows] == ["R1", "R2", "R3", "R4", "N1", "N2"]
    assert [row["change"] for row in rows] == ["unchanged"] * 3 + ["improved", "unscored", "unscored"]
    assert [row["baseline_retrieved_count"] for row in rows] == [1, 1, 1, 0, 1, 0]
    assert [row["candidate_retrieved_count"] for row in rows] == [1, 1, 1, 1, 1, 0]
    assert [row["baseline"]["evidence_found"] for row in rows] == [True, True, True, False, None, None]
    assert [row["candidate"]["evidence_found"] for row in rows] == [True, True, True, True, None, None]
    assert report["baseline_summary"] == dict(total=6, evaluated=4, hits=3, misses=1, unscored=2, hit_rate=0.75)
    assert report["candidate_summary"] == dict(total=6, evaluated=4, hits=4, misses=0, unscored=2, hit_rate=1.0)
    assert rows[3]["candidate"]["context"]["chunks"][0]["source_name"] == "account_help.txt"
    assert [asdict(chunk) for chunk in chunks] == before_chunks
    assert [asdict(case) for case in cases] == before_cases
    assert report["gateway_calls"] == 0


def test_one_character_budget_hides_improvement():
    report = compare_retrieval(evaluation_chunks(), [evaluation_cases()[3]], max_chars=1)
    row = report["results"][0]
    # 新算法命中仍存在，但预算不允许发送，所以不能将检索命中直接当证据命中。
    assert row["candidate_retrieved_count"] == 1
    assert row["candidate"]["context"] == {"text": "", "chunks": []}
    assert row["change"] == "unchanged"
    assert report["candidate_summary"]["hit_rate"] == 0.0


def test_empty_comparison_has_independent_empty_summaries():
    report = compare_retrieval(evaluation_chunks(), [])
    expected = dict(total=0, evaluated=0, hits=0, misses=0, unscored=0, hit_rate=None)
    assert report["results"] == []
    assert report["baseline_summary"] == expected
    assert report["candidate_summary"] == expected
    assert report["baseline_summary"] is not report["candidate_summary"]


def test_demo_prints_complete_offline_report(capsys):
    assert run_compare_demo.main([]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report == compare_retrieval(evaluation_chunks(), evaluation_cases())
    assert report["baseline_method"] == "whitespace_terms"
    assert report["candidate_method"] == "character_bigrams"
    assert report["dataset_origin"] == "provided_synthetic_faq_v1"
    assert report["top_k"] == 2 and report["max_chars"] == 500
