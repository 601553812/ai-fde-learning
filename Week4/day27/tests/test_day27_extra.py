"""Learner-owned edge case for a structurally valid but unwanted field."""
import json

from Week4.day27.code.output_audit import audit_raw


def test_nonempty_risk_fails_when_risks_must_be_empty():
    body = {"functions": ["一覧をCSVで出力する"], "acceptance_criteria": [], "risks": ["個人情報の確認が必要"],
            "questions": [], "unknown": []}
    audit_result = audit_raw(json.dumps(body), {}, ["risks"])
    assert audit_result.status == "content_failed"
    assert audit_result.issues == ["unexpected:risks"]