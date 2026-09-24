"""Learner task: describe a change under the same evaluation rules."""

from Week3.day17.evaluation import EvaluationResult


def classify_change(before: EvaluationResult, after: EvaluationResult) -> str:
    if before.content_passed:
        if after.content_passed:
            return "unchanged_pass"
        else:
            return "regressed"
    else:
        if after.content_passed:
            return "improved"
        else:
            return "unchanged_fail"