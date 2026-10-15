"""只检查准备发送的资料中有没有事先指定的证据，不评价生成回答。"""

from dataclasses import dataclass

from .context import ContextBundle
from .eval_cases import EvalCase


@dataclass(frozen=True)
class EvidenceCheck:
    """保留同一个case/context；found为None表示不纳入有答案问题的比例。"""

    case: EvalCase
    context: ContextBundle
    evidence_found: bool | None


@dataclass(frozen=True)
class EvidenceSummary:
    """分母evaluated只含有期望证据的记录；无此类记录时比例为None。"""

    total: int
    evaluated: int
    hits: int
    misses: int
    unscored: int
    hit_rate: float | None


def check_evidence(case: EvalCase, context: ContextBundle) -> EvidenceCheck:
    """检查人工指定原句是否出现在同来源的发送片段中，保留输入对象。"""
    # 没有人工预期时保持None；有预期才进入逐片段检查。
    evidence_found = None
    if case.expected_evidence is not None:
        evidence_found = False
        for chunk in context.chunks:
            # 来源和原句必须在同一块同时匹配；后续不匹配不会覆盖已经找到的True。
            if case.expected_evidence.source_name == chunk.source_name:
                if case.expected_evidence.quote in chunk.text:
                    evidence_found = True
    return EvidenceCheck(case, context, evidence_found)


def summarize_evidence(checks: list[EvidenceCheck]) -> EvidenceSummary:
    """分别统计找到、未找到、不评分；比例分母只包含前两类。"""
    # 每次使用本次局部计数，不沿用上一次汇总。
    total = len(checks)
    hits = 0
    misses = 0
    unscored = 0
    for check in checks:
        # 合法输入只有True/False/None：None不同于有预期但未找到的False。
        if check.evidence_found:
            hits += 1
        elif check.evidence_found == False:
            misses += 1
        else:
            unscored += 1
    evaluated = hits + misses
    # 没有参与评分的记录时不做除法；有记录且全未找到时结果才是0.0。
    hit_rate = None
    if evaluated > 0:
        hit_rate = hits / evaluated
    return EvidenceSummary(total, evaluated, hits, misses, unscored, hit_rate)
