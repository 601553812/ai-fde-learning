"""比较同一固定问题在两种检索下的发送资料；不是模型回答评分。"""

from dataclasses import asdict

from .bigram_retrieval import retrieve_bigrams
from .chunking import Chunk
from .context import build_context
from .eval_cases import EvalCase
from .retrieval import retrieve_chunks
from .retrieval_eval import check_evidence, summarize_evidence


def classify_change(before: bool | None, after: bool | None) -> str:
    """逐题比较证据检查结果；None先排除，剩余才比较命中变化。"""
    # before/after是预算后是否找到证据，不是检索score。
    if before is None or after is None:
        return "unscored"
    elif before == after:
        return "unchanged"
    # 到这里两边都为布尔值且不同，因此False对应改善、True对应退步。
    elif not before:
        return "improved"
    elif before:
        return "regressed"
    return "unexcepted error"


def compare_retrieval(chunks: list[Chunk], cases: list[EvalCase],
                      top_k: int = 2, max_chars: int = 500) -> dict:
    """已提供：对相同输入分别执行两条普通调用链，最后组织完整报告。"""
    baseline_checks = []
    candidate_checks = []
    rows = []
    for case in cases:
        # 两个检索器都只拿问题；expected_evidence只给后面的检查函数。
        baseline_hits = retrieve_chunks(chunks, case.question, top_k)
        candidate_hits = retrieve_bigrams(chunks, case.question, top_k)
        baseline = check_evidence(case, build_context(baseline_hits, max_chars))
        candidate = check_evidence(case, build_context(candidate_hits, max_chars))
        baseline_checks.append(baseline)
        candidate_checks.append(candidate)
        rows.append({
            "case_id": case.case_id,
            "baseline_retrieved_count": len(baseline_hits),
            "candidate_retrieved_count": len(candidate_hits),
            "baseline": asdict(baseline),
            "candidate": asdict(candidate),
            "change": classify_change(baseline.evidence_found, candidate.evidence_found),
        })
    # 两份汇总独立产生；不把字符对得分与旧词项得分直接比较。
    return {
        "dataset_origin": "provided_synthetic_faq_v1",
        "baseline_method": "whitespace_terms", "candidate_method": "character_bigrams",
        "top_k": top_k, "max_chars": max_chars, "results": rows,
        "baseline_summary": asdict(summarize_evidence(baseline_checks)),
        "candidate_summary": asdict(summarize_evidence(candidate_checks)),
        "gateway_calls": 0,
    }
