"""独立检查检索命中不等于预算后的证据仍然存在。"""
from dataclasses import asdict
from Week6.day38.code.context import build_context
from Week6.day38.code.eval_cases import evaluation_cases, evaluation_chunks
from Week6.day38.code.retrieval import retrieve_chunks
from Week6.day38.code.retrieval_eval import check_evidence


def test_budget_can_remove_retrieved_evidence_without_changing_input():
    cases = evaluation_cases()
    case = cases[0]
    chunks = evaluation_chunks()
    # 在检索前保存完整值快照和原对象引用，之后分别检查内容与身份。
    case_copy = asdict(case).copy()
    chunks_copy = []
    for chunk in chunks:
        chunks_copy.append(asdict(chunk))
    original_chunks = chunks.copy()
    hits = retrieve_chunks(chunks, case.question, 2)
    # 同一份检索命中依次使用两种预算：小预算不改变原hits，但不能发送资料。
    full = build_context(hits, 500)
    tiny = build_context(hits, 1)
    check_full = check_evidence(case,full)
    check_tiny = check_evidence(case,tiny)
    # 所有调用后再看命中、发送片段、完整检查记录和原对象，避免只断言布尔值。
    assert len(hits) == 1
    assert hits[0].chunk is original_chunks[0]
    assert full.chunks == [original_chunks[0]]
    assert full.chunks[0] is original_chunks[0]
    assert asdict(tiny) == {"text": "", "chunks": []}
    assert asdict(check_full) == {"case": asdict(case), "context": asdict(full), "evidence_found": True}
    assert asdict(check_tiny) == {"case": asdict(case), "context": asdict(tiny), "evidence_found": False}
    assert check_full.case is case
    assert check_tiny.case is case
    assert check_full.context is full
    assert check_tiny.context is tiny
    assert asdict(case) == case_copy
    # 重建调用后的完整数据快照，和调用前同形式比较，再逐项检查原对象。
    chunks_confirm = []
    for chunk in chunks:
        chunks_confirm.append(asdict(chunk))
    assert chunks_confirm == chunks_copy
    assert chunks[0] is original_chunks[0]
    assert chunks[1] is original_chunks[1]
    assert chunks[2] is original_chunks[2]
