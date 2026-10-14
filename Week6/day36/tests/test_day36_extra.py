"""独立检查合理拒答计入通过、空输入和连续汇总互不影响。"""
from dataclasses import asdict  # 把数据类转为字典便于比较完整结果。
from Week6.day36.code.qa_review import make_review_record, summarize_reviews
from Week6.day36.code.review_cases import demo_review_inputs


def test_mixed_then_empty_then_failed_summary_is_independent():

    # 输入来自两个已提供的案例；先把ReviewInput转换成正式核查记录。
    inputs = demo_review_inputs()
    b_input = inputs[1]
    wrong_90_input = inputs[2]
    b_record= make_review_record(b_input.case_id,b_input.question,b_input.result,b_input.verdict,b_input.reason)
    wrong_90_record = make_review_record(wrong_90_input.case_id,wrong_90_input.question,wrong_90_input.result,wrong_90_input.verdict,wrong_90_input.reason)
    records = [b_record, wrong_90_record]
    # 外层浅拷贝保存原记录顺序；asdict快照保存调用前的完整数据。
    records_copy = records.copy()
    before_data = [asdict(record) for record in records]
    # 依次汇总混合样本、空输入、单个失败样本，观察调用之间是否独立。
    reviews_1 = summarize_reviews(records)
    reviews_2 = summarize_reviews([])
    reviews_3 = summarize_reviews([wrong_90_record])
    actual_1 = asdict(reviews_1)
    actual_2 = asdict(reviews_2)
    actual_3 = asdict(reviews_3)
    # 数据快照与原对象身份分开验证；三份计数字典检查全部三对。
    assert [asdict(record) for record in records] == before_data
    assert reviews_1.verdict_counts is not reviews_2.verdict_counts is not reviews_3.verdict_counts
    assert reviews_1.verdict_counts is not reviews_3.verdict_counts
    assert [record for record in records] == records_copy
    assert records == records_copy
    assert records[0] is b_record
    assert records[1] is wrong_90_record
    # 三份完整结果均在所有调用结束后比较，也能发现第一份被后续改写。
    assert actual_1 == {
        "total": 2,
        "passed": 1,
        "failed": 1,
        "pass_rate": 0.5,
        "verdict_counts": {
            "supported": 0,
            "unsupported": 1,
            "correct_refusal": 1,
            "incorrect_refusal": 0,
        },
    }
    assert actual_2 == {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "pass_rate": None,
        "verdict_counts": {
            "supported": 0,
            "unsupported": 0,
            "correct_refusal": 0,
            "incorrect_refusal": 0,
        },
    }
    assert actual_3 == {
        "total": 1,
        "passed": 0,
        "failed": 1,
        "pass_rate": 0.0,
        "verdict_counts": {
            "supported": 0,
            "unsupported": 1,
            "correct_refusal": 0,
            "incorrect_refusal": 0,
        },
    }
