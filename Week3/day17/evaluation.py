"""Learner TODOs: assess structure first, then explicit content checks."""

from dataclasses import dataclass

from Week1.day06 import RequirementData
from Week2.day14.service import InvalidModelOutput, decode_requirements


@dataclass
class EvaluationResult:
    structure_valid: bool
    content_passed: bool | None
    issues: list[str]


def check_content(
    requirements: RequirementData,
    must_contain: dict[str, list[str]],
    must_be_empty: list[str],
) -> list[str]:
    problems: list[str] = []
    requirements_dict = requirements.model_dump()
    for key in must_contain.keys():
        if key in requirements_dict:
            for value in must_contain[key]:
                result = False
                problem = "missing:" + key + ":" + value
                for requirement in requirements_dict[key]:
                    if value in requirement:
                        result = True
                        pass
                if not result:
                    problems.append(problem)
    for empty in must_be_empty:
        if not requirements_dict[empty]:
            pass
        else:
            problem = "unexpected:"+empty
            problems.append(problem)
    return problems


def evaluate(
    raw: str,
    must_contain: dict[str, list[str]],
    must_be_empty: list[str],
) -> EvaluationResult:
    try :requirements = decode_requirements(raw)
    except InvalidModelOutput as exc:
        return EvaluationResult(structure_valid = False, content_passed = None,issues = ["invalid_structure"])
    problems = check_content(requirements,must_contain, must_be_empty)
    if not problems:
        return EvaluationResult(structure_valid = True, content_passed = True,issues = [])
    return EvaluationResult(structure_valid=True, content_passed=False,issues = problems )
