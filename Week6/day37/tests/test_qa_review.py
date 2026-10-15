"""人工结论与编号信息分别验证；本地测试不证明真实模型准确率。"""

import json
from dataclasses import asdict

import pytest

from Week6.day37.code import run_review_demo
from Week6.day37.code.context import ContextBundle
from Week6.day37.code.qa_review import ReviewRecord, make_review_record, summarize_reviews
from Week6.day37.code.qa_service import QAResult
from Week6.day37.code.review_cases import demo_review_inputs


@pytest.mark.parametrize("verdict", ["supported", "unsupported", "correct_refusal", "incorrect_refusal"])
def test_record_uses_supplied_manual_verdict(verdict):
    item = demo_review_inputs()[0]
    # 同一个回答搭配不同人工选择，函数应保存选择，不自行改判。
    record = make_review_record("case", item.question, item.result, verdict, "人工说明")
    assert record.verdict == verdict
    assert record.reason == "人工说明"
    assert record.result is item.result
    assert record.citation_errors == []
    assert record.cited_chunks == item.result.context.chunks
    assert record.cited_chunks[0] is item.result.context.chunks[0]


def test_record_preserves_metadata_and_original_input():
    item = demo_review_inputs()[0]
    before = asdict(item.result)
    # strip 只用来判断是否空白，合法字符串的首尾空白仍需保留。
    record = make_review_record(" A ", " 返品 期限 ", item.result, "supported", " 30日有原文依据 \n")
    assert record.case_id == " A "
    assert record.question == " 返品 期限 "
    assert record.reason == " 30日有原文依据 \n"
    assert record.result is item.result
    assert asdict(item.result) == before
    assert record.cited_chunks is not item.result.context.chunks


@pytest.mark.parametrize(
    "case_id,question,status,verdict,reason,message",
    [
        ("", "返品", "generated", "supported", "说明", "invalid_case_id"),
        (" \t", "返品", "generated", "supported", "说明", "invalid_case_id"),
        ("A", " \n", "generated", "supported", "说明", "invalid_question"),
        ("A", "返品", "no_context", "supported", "说明", "unreviewable_status"),
        ("A", "返品", "generated", "", "说明", "invalid_verdict"),
        ("A", "返品", "generated", "Supported", "说明", "invalid_verdict"),
        ("A", "返品", "generated", "supported", " \t", "invalid_review_reason"),
    ],
)
def test_record_rejects_invalid_input(case_id, question, status, verdict, reason, message):
    result = QAResult(status, "資料からは回答できません。", ContextBundle("", []))
    # match 的 ^/$ 要求完整错误消息，契约在 README 明确给出。
    with pytest.raises(ValueError, match=f"^{message}$"):
        make_review_record(case_id, question, result, verdict, reason)


def test_correct_refusal_keeps_missing_citation_as_separate_information():
    item = demo_review_inputs()[1]
    record = make_review_record(item.case_id, item.question, item.result, item.verdict, item.reason)
    # 原文无送料答案：合理拒答可保留缺编号信息，两者不互相覆盖。
    assert record.verdict == "correct_refusal"
    assert record.citation_errors == ["missing_citation"]
    assert record.cited_chunks == []
    assert len(record.result.context.chunks) == 1


def test_wrong_fact_keeps_valid_citation_as_separate_information():
    item = demo_review_inputs()[2]
    record = make_review_record(item.case_id, item.question, item.result, item.verdict, item.reason)
    # 90日反例有合法编号，但人根据30日原文选择 unsupported。
    assert record.verdict == "unsupported"
    assert record.result.answer == "返品期限は90日です。[1]"
    assert record.citation_errors == []
    assert record.cited_chunks[0] is item.result.context.chunks[0]


def records_with_verdicts(verdicts):
    # 直接构造已校验形状的记录，使 TODO 2 的测试独立于 TODO 1。
    item = demo_review_inputs()[0]
    return [ReviewRecord(str(i), item.question, item.result, verdict, "测试人工结论", [], [])
            for i, verdict in enumerate(verdicts)]


@pytest.mark.parametrize(
    "verdicts,counts,passed,rate",
    [
        ([], [0, 0, 0, 0], 0, None),
        (["supported"], [1, 0, 0, 0], 1, 1.0),
        (["unsupported"], [0, 1, 0, 0], 0, 0.0),
        (["correct_refusal"], [0, 0, 1, 0], 1, 1.0),
        (["incorrect_refusal"], [0, 0, 0, 1], 0, 0.0),
        (["supported", "unsupported", "supported", "correct_refusal", "incorrect_refusal"],
         [2, 1, 1, 1], 3, 0.6),
    ],
)
def test_summary_counts_all_four_verdicts(verdicts, counts, passed, rate):
    records = records_with_verdicts(verdicts)
    before = [asdict(record) for record in records]
    summary = summarize_reviews(records)
    expected = {
        "total": len(verdicts), "passed": passed, "failed": len(verdicts) - passed,
        "pass_rate": rate,
        "verdict_counts": dict(zip(
            ("supported", "unsupported", "correct_refusal", "incorrect_refusal"), counts,
        )),
    }
    # 检查完整结构，能发现漏掉零计数类别、错误分母或多出字段。
    assert asdict(summary) == expected
    assert [asdict(record) for record in records] == before


def test_summary_counts_are_new_on_every_call():
    first = summarize_reviews(records_with_verdicts(["supported"]))
    first.verdict_counts["supported"] = 999
    second = summarize_reviews([])
    # frozen 不会冻结嵌套字典；第二次必须建立自己的字典，不受第一次修改影响。
    assert second.verdict_counts == {
        "supported": 0, "unsupported": 0, "correct_refusal": 0, "incorrect_refusal": 0,
    }
    assert second.verdict_counts is not first.verdict_counts
    assert second.pass_rate is None


def test_demo_shows_manual_sources_and_full_summary(capsys):
    assert run_review_demo.main([]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["gateway_calls"] == 0
    assert [row["answer_origin"] for row in output["reviews"]] == [
        "recorded_day34", "recorded_day34", "synthetic", "synthetic",
    ]
    assert all(row["review_origin"] == "provided_manual_example" for row in output["reviews"])
    assert [row["record"]["case_id"] for row in output["reviews"]] == ["A", "B", "wrong_90", "wrong_refusal"]
    assert output["reviews"][1]["record"]["citation_errors"] == ["missing_citation"]
    assert output["reviews"][2]["record"]["citation_errors"] == []
    assert output["summary"] == {
        "total": 4, "passed": 2, "failed": 2, "pass_rate": 0.5,
        "verdict_counts": {"supported": 1, "unsupported": 1, "correct_refusal": 1, "incorrect_refusal": 1},
    }
