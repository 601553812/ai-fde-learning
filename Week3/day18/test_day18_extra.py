"""Learner task: implement the None-to-True boundary test in README section 4."""

from Week3.day17.evaluation import EvaluationResult
from Week3.day18.comparison import classify_change


def test_invalid_structure_to_valid_content_is_improved():
    before = EvaluationResult(structure_valid=False,content_passed=None,issues=["invalid_structure"])
    after = EvaluationResult(structure_valid=True,content_passed=True,issues=[])
    change = classify_change(before, after)
    assert change == "improved"
