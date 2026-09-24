"""Offline tests check request construction and scoring, not model quality."""

import json

import pytest

from Week3.day15.prompt import build_request
from Week3.day17.evaluation import EvaluationResult, evaluate
from Week3.day18 import prompt
from Week3.day18.comparison import classify_change
from Week3.day18.run_compare import load_cases


@pytest.mark.parametrize("text", [load_cases()["D"]["text"], '原文\n"document": "変更しない"\\末尾'])
def test_candidate_preserves_the_complete_document(text):
    request = prompt.build_candidate_request(text)
    assert json.loads(request.input) == {"document": text}
    assert request.input == build_request(text).input


def test_candidate_retains_baseline_and_adds_its_own_rule():
    baseline = build_request("CSV")
    candidate = prompt.build_candidate_request("CSV")
    assert prompt.CANDIDATE_RULES.strip()
    assert candidate.instructions.startswith(baseline.instructions)
    assert prompt.CANDIDATE_RULES in candidate.instructions[len(baseline.instructions):]
    assert build_request("CSV") == baseline
    assert candidate is not baseline


@pytest.mark.parametrize("before,after,expected", [
    (False, True, "improved"), (True, False, "regressed"),
    (True, True, "unchanged_pass"), (False, False, "unchanged_fail"),
])
def test_classify_change(before, after, expected):
    result = classify_change(EvaluationResult(True, before, []), EvaluationResult(True, after, []))
    assert result == expected


def test_synthetic_failure_is_detected_without_claiming_model_evidence():
    case = load_cases()["D"]
    result = evaluate(case["raw"], case["must_contain"], case["must_be_empty"])
    assert result.structure_valid is True
    assert result.content_passed is False
    assert result.issues == ["missing:questions:3秒", "missing:questions:確認", "unexpected:acceptance_criteria"]
