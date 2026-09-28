"""Connect Day27's single-response audit to a validated batch report."""

from dataclasses import dataclass
from typing import Literal

from .output_audit import audit_raw
from .response_models import BatchResponse


@dataclass(frozen=True)
class AuditExpectation:
    must_contain: dict[str, list[str]]
    must_be_empty: list[str]


@dataclass(frozen=True)
class TaskAudit:
    task_id: str
    status: Literal[
        "call_failed", "invalid_structure", "content_passed", "content_failed", "not_checked"
    ]
    issues: list[str]


def audit_batch(
    report: BatchResponse,
    expectations: dict[str, AuditExpectation],
) -> list[TaskAudit]:
    task_ids = {row.task_id for row in report.tasks}
    for key in expectations:
        if key not in task_ids:
            raise ValueError(f"unknown_expectation:{key}")

    results: list[TaskAudit] = []
    for row in report.tasks:
        task_id = row.task_id
        result = row.report.result
        if not result.ok:
            results.append(TaskAudit(task_id, "call_failed", []))
        elif task_id not in expectations:
            results.append(TaskAudit(task_id, "not_checked", []))
        else:
            expected = expectations[task_id]
            audit = audit_raw(result.raw, expected.must_contain, expected.must_be_empty)
            results.append(TaskAudit(task_id, audit.status, audit.issues))
    return results
