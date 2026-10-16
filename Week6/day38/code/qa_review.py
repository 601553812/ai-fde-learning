"""保存人工依据核查结论，再汇总这些已经核查的案例。"""

from dataclasses import dataclass

from .chunking import Chunk
from .citation_sources import find_cited_chunks
from .citations import review_qa_result
from .qa_service import QAResult

# 人工对照问题、回答、原文后选择一种；不是由引用错误列表推算出来。
VERDICTS = ("supported", "unsupported", "correct_refusal", "incorrect_refusal")
PASS_VERDICTS = ("supported", "correct_refusal")


@dataclass(frozen=True)
class ReviewRecord:
    """一条人工核查记录；result 保存同一个问答结果，方便回查。"""

    case_id: str
    question: str
    result: QAResult
    verdict: str
    reason: str
    citation_errors: list[str]  # 既有自动编号检查结果，独立于 verdict。
    cited_chunks: list[Chunk]  # 有效编号指向的原对象，不自动判断事实。


@dataclass(frozen=True)
class ReviewSummary:
    """只汇总传入的人工记录；pass_rate 为空时为 None。"""

    total: int
    passed: int
    failed: int
    pass_rate: float | None
    verdict_counts: dict[str, int]


def make_review_record(
        case_id: str,
        question: str,
        result: QAResult,
        verdict: str,
        reason: str,
) -> ReviewRecord:
    """按固定顺序校验人工输入，同时保留原问答与独立的编号信息。"""
    # strip只用于判断空白，校验后仍保存调用方给出的原文字。
    if not case_id or case_id.strip() == "":
        raise ValueError("invalid_case_id")
    if not question or question.strip() == "":
        raise ValueError("invalid_question")
    if result.status != "generated":
        raise ValueError("unreviewable_status")
    if verdict not in VERDICTS:
        raise ValueError("invalid_verdict")
    if not reason or reason.strip() == "":
        raise ValueError("invalid_review_reason")
    # 两个辅助函数只检查编号和定位原文，不替调用方判断日文事实。
    record = ReviewRecord(case_id, question, result, verdict, reason, review_qa_result(result),
                          find_cited_chunks(result.answer, result.context))
    return record


def summarize_reviews(records: list[ReviewRecord]) -> ReviewSummary:
    """只统计传入的合法人工记录，空报告的通过比例为None。"""
    total = len(records)
    # 每次建立自己的四类计数字典，保留未出现类别的0。
    verdict_counts: dict[str, int] = {
        verdict: 0 for verdict in VERDICTS
    }
    for record in records:
        if record.verdict in VERDICTS:
            verdict_counts[record.verdict] = verdict_counts[record.verdict] + 1
    # 合理拒答也算通过；比例描述的是这批人工记录。
    passed = verdict_counts["supported"] + verdict_counts["correct_refusal"]
    failed = verdict_counts["unsupported"] + verdict_counts["incorrect_refusal"]
    # 没有样本时保留None，不做除法；有样本且全失败时才是0.0。
    pass_rate = None
    if total > 0:
        pass_rate = passed / total

    return ReviewSummary(total, passed, failed, pass_rate, verdict_counts)
