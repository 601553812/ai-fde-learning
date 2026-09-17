"""Provided tests assess the evaluator, never the live model."""

import json

import pytest

from Week2.day14.service import decode_requirements
from Week3.day17.evaluation import check_content, evaluate
from Week3.day17.run_eval import load_baseline


def get_case(case_id):
    return next(c for c in load_baseline()["cases"] if c["id"] == case_id)


@pytest.mark.parametrize("case_id", ["A", "B", "C"])
def test_recorded_outputs_pass_selected_checks(case_id):
    c = get_case(case_id)
    r = evaluate(c["raw"], c["must_contain"], c["must_be_empty"])
    assert (r.structure_valid, r.content_passed, r.issues) == (True, True, [])


@pytest.mark.parametrize("raw", ["not-json", '{"functions": 123}'])
def test_bad_structure_is_not_scored_as_content(raw):
    r = evaluate(raw, {"functions": ["CSV"]}, [])
    assert (r.structure_valid, r.content_passed, r.issues) == (False, None, ["invalid_structure"])


def test_missing_risk_is_content_failure():
    c = get_case("B")
    data = json.loads(c["raw"])
    data["risks"] = []
    r = evaluate(json.dumps(data), c["must_contain"], c["must_be_empty"])
    assert (r.structure_valid, r.content_passed, r.issues) == (True, False, ["missing:risks:文字化け"])


def test_all_checks_are_collected_and_confined_to_their_field():
    c = get_case("B")
    data = json.loads(c["raw"])
    data["functions"] = ["CSV"]
    data["risks"] = []
    data["unknown"] = ["注文一覧 文字化け"]
    r = evaluate(json.dumps(data), c["must_contain"], c["must_be_empty"])
    assert r.issues == ["missing:functions:注文一覧", "missing:risks:文字化け", "unexpected:unknown"]
    assert r.content_passed is False


def test_substring_must_occur_in_one_item_not_across_two():
    c = get_case("A")
    data = json.loads(c["raw"])
    data["functions"] = ["C", "SV"]
    issues = check_content(decode_requirements(json.dumps(data)), {"functions": ["CSV"]}, [])
    assert issues == ["missing:functions:CSV"]


def test_no_checks_means_no_detected_issues():
    c = get_case("A")
    assert check_content(decode_requirements(c["raw"]), {}, []) == []
