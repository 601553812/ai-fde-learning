"""Audit one model raw response against explicit, human-written expectations."""

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, ConfigDict, ValidationError


class ExtractedRequirements(BaseModel):
    """The five fields requested by the current model prompt."""

    model_config = ConfigDict(extra="forbid", strict=True)

    functions: list[str]
    acceptance_criteria: list[str]
    risks: list[str]
    questions: list[str]
    unknown: list[str]


@dataclass(frozen=True)
class AuditResult:
    status: Literal["call_failed", "invalid_structure", "content_passed", "content_failed"]
    issues: list[str]


def decode_raw(raw: str) -> ExtractedRequirements:
    try:
        extracted = ExtractedRequirements.model_validate_json(raw,strict=True)
    except ValidationError as e:
        raise ValueError("invalid_structure") from e
    return extracted


def audit_content(
    extracted: ExtractedRequirements,
    must_contain: dict[str, list[str]],
    must_be_empty: list[str],
) -> list[str]:
    extracted_dict = extracted.model_dump()
    problem = []
    """取出一个必须包含的require"""
    for must_require in must_contain:
        """看这个require在不在extracted中"""
        if must_require in extracted_dict:
            """再取一个这个require对应的内容"""
            for must_content in must_contain[must_require]:
                found = False
                """看这个require对应的内容在不在extracted对应的require中"""
                for must_content_extracted in extracted_dict[must_require]:
                    if must_content in must_content_extracted :
                        found = True
                        break
                if not found:
                    problem.append(f"missing:{must_require}:{must_content}")

    for empty_require in must_be_empty:
        if empty_require in extracted_dict:
            if extracted_dict[empty_require] :
                problem.append(f"unexpected:{empty_require}")
    return problem

def audit_raw(
    raw: str | None,
    must_contain: dict[str, list[str]],
    must_be_empty: list[str],
) -> AuditResult:
    """Provided control flow: a failed call has no raw response to assess."""
    if raw is None:
        return AuditResult("call_failed", [])
    try:
        extracted = decode_raw(raw)
    except ValueError:
        return AuditResult("invalid_structure", ["invalid_structure"])
    issues = audit_content(extracted, must_contain, must_be_empty)
    if issues:
        return AuditResult("content_failed", issues)
    return AuditResult("content_passed", [])
