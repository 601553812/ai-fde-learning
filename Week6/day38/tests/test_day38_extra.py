"""独立验证R4的改善取决于预算后实际准备发送的资料。"""
from dataclasses import asdict

from Week6.day38.code.eval_cases import evaluation_cases, evaluation_chunks
from Week6.day38.code.bigram_retrieval import retrieve_bigrams
from Week6.day38.code.retrieval import retrieve_chunks, RetrievalHit
from Week6.day38.code.context import build_context
from Week6.day38.code.retrieval_eval import check_evidence
from Week6.day38.code.retrieval_compare import classify_change


def test_r4_improvement_disappears_when_budget_excludes_retrieved_chunk():
    case = evaluation_cases()[3]
    chunks = evaluation_chunks()
    # 调用前分别保存完整值快照与原对象引用，检查值和身份是两件事。
    case_dict = asdict(case)
    chunks_dict = []
    for chunk in chunks:
        chunks_dict.append(asdict(chunk))
    originals = chunks.copy()
    # 两种检索共享问题；新方法的同一份命中分别经过500/1预算。
    old_hits = retrieve_chunks(chunks, case.question, 2)
    new_hits = retrieve_bigrams(chunks, case.question, 2)
    old_context = build_context(old_hits, 500)
    new_context_full = build_context(new_hits, 500)
    new_context_tiny = build_context(new_hits, 1)
    old_context_check = check_evidence(case, old_context)
    new_context_full_check = check_evidence(case, new_context_full)
    new_context_tiny_check = check_evidence(case, new_context_tiny)
    old_full_change = classify_change(old_context_check.evidence_found, new_context_full_check.evidence_found)
    old_tiny_change = classify_change(old_context_check.evidence_found, new_context_tiny_check.evidence_found)
    # 所有调用结束后再检查：命中仍保留，但tiny没有任何可发送的资料。
    assert old_hits == []
    assert new_hits == [RetrievalHit(originals[2], 5)]
    assert new_hits[0].chunk is originals[2]
    assert new_context_full.chunks == [originals[2]]
    assert new_context_full.chunks[0] is originals[2]
    assert asdict(new_context_tiny) == {"text": "", "chunks": []}
    assert old_context_check.evidence_found == False
    assert new_context_full_check.evidence_found == True
    assert new_context_tiny_check.evidence_found == False
    assert old_context_check.case is new_context_full_check.case is new_context_tiny_check.case is case
    assert old_context_check.context is old_context
    assert new_context_full_check.context is new_context_full
    assert new_context_tiny_check.context is new_context_tiny
    assert old_full_change == "improved"
    assert old_tiny_change == "unchanged"
    # 完整快照验证值与顺序；长度加zip/is检查每个位置仍是原对象。
    assert asdict(case) == case_dict
    chunks_dict_confirm = []
    for chunk in chunks:
        chunks_dict_confirm.append(asdict(chunk))
    assert chunks_dict == chunks_dict_confirm
    assert len(chunks) == len(originals)
    for current, original in zip(chunks, originals):
        assert current is original
