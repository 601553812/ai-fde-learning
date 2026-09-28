"""Day27 structure and content contracts use sanitized, local model text."""

import json

import pytest

from ..code.output_audit import audit_raw, decode_raw


def raw_text(**overrides):
    body = {
        "functions": ["一覧をCSVで出力する"],
        "acceptance_criteria": [],
        "risks": [],
        "questions": [],
        "unknown": [],
    }
    body.update(overrides)
    return json.dumps(body, ensure_ascii=False)


@pytest.mark.parametrize("raw", [
    "not-json",
    raw_text(functions="CSV"),
    raw_text(extra=["unused"]),
    json.dumps({"functions": []}),
])
def test_decode_rejects_invalid_json_types_and_extra_fields(raw):
    with pytest.raises(ValueError, match="^invalid_structure$"):
        decode_raw(raw)
    assert audit_raw(raw, {"functions": ["CSV"]}, []).status == "invalid_structure"


def test_content_passes_when_required_fragment_is_present():
    result = audit_raw(raw_text(), {"functions": ["CSV"]}, ["risks"])
    assert result.status == "content_passed"
    assert result.issues == []


def test_content_passes_when_one_of_several_items_has_required_fragment():
    result = audit_raw(
        raw_text(functions=["一覧をCSVで出力する", "検索も追加する"]),
        {"functions": ["CSV"]},
        [],
    )
    assert result.status == "content_passed"
    assert result.issues == []


def test_valid_structure_can_still_fail_content():
    result = audit_raw(raw_text(), {"functions": ["PDF"]}, [])
    assert result.status == "content_failed"
    assert result.issues == ["missing:functions:PDF"]


def test_failed_call_has_no_structure_or_content_result():
    result = audit_raw(None, {"functions": ["CSV"]}, [])
    assert result.status == "call_failed"
    assert result.issues == []
