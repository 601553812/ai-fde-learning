"""Business validation rules for parsed requirements."""

from __future__ import annotations


def validate_result(result: dict[str, list[str]]) -> list[str]:
    """Return every missing-required-section error."""
    errors: list[str] = []
    if not result["functions"]:
        errors.append("At least one function is required")
    if not result["acceptance_criteria"]:
        errors.append("At least one acceptance criterion is required")
    return errors
