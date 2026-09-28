"""Day28: a batch needs one explicit expectation per checked task."""

from copy import deepcopy
import json

import pytest

from ..code.batch_audit import AuditExpectation, TaskAudit, audit_batch
from ..code.response_models import BatchResponse


def raw(**changes):
    body = {"functions": ["一覧をCSVで出力する"], "acceptance_criteria": [],
            "risks": [], "questions": [], "unknown": []}
    body.update(changes)
    return json.dumps(body, ensure_ascii=False)


def report(*outcomes):
    rows = []
    for task_id, model_raw in outcomes:
        ok = model_raw is not None
        rows.append({"task_id": task_id, "report": {"attempts": 1, "result": {
            "ok": ok, "raw": model_raw, "error": None if ok else "timeout",
            "status_code": None}}})
    return BatchResponse.model_validate({"mode": "live", "tasks": rows, "summary": {
        "requests": len(rows), "succeeded": sum(r["report"]["result"]["ok"] for r in rows),
        "failed": sum(not r["report"]["result"]["ok"] for r in rows),
        "attempts": len(rows), "retries": 0}})


def expected(fragment="CSV"):
    return AuditExpectation({"functions": [fragment]}, ["risks"])


def test_each_task_uses_its_own_expectation_and_response_order():
    batch = report(("A", raw()), ("B", raw()))
    before = deepcopy(batch)
    result = audit_batch(batch, {"B": expected("PDF"), "A": expected()})
    assert result == [TaskAudit("A", "content_passed", []),
                      TaskAudit("B", "content_failed", ["missing:functions:PDF"])]
    assert batch == before


def test_failed_call_is_not_counted_as_content_failure():
    assert audit_batch(report(("A", None)), {"A": expected()}) == [
        TaskAudit("A", "call_failed", [])]


def test_bad_structure_is_distinct_from_missing_content():
    assert audit_batch(report(("A", "not-json")), {"A": expected()}) == [
        TaskAudit("A", "invalid_structure", ["invalid_structure"])]


def test_success_without_written_expectation_is_not_checked():
    assert audit_batch(report(("A", raw())), {}) == [TaskAudit("A", "not_checked", [])]


def test_empty_batch_has_no_audit_rows():
    assert audit_batch(report(), {}) == []


def test_unknown_expectation_id_is_rejected_before_any_audit():
    with pytest.raises(ValueError, match="^unknown_expectation:Z$"):
        audit_batch(report(("A", raw())), {"Z": expected()})
