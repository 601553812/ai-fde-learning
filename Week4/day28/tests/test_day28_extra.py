"""Learner-owned boundary test for the difference between checked and unchecked."""

from ..code.batch_audit import audit_batch
from .test_batch_audit import expected, raw, report



def test_one_failed_and_one_unchecked_task():
    batch = report(("A", None), ("B", raw()))
    result = audit_batch(batch,{ "A": expected()})
    result_a = result[0]
    result_b = result[1]
    assert result_a.task_id == "A"
    assert result_b.task_id == "B"
    assert result_a.status == "call_failed"
    assert result_b.status == "not_checked"
    assert result_a.issues == result_b.issues == []
