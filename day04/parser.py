"""Text parsing functions for the requirement tool."""

from __future__ import annotations

from .models import RequirementItem


PREFIX_TO_CATEGORY: dict[str, str] = {
    "機能": "functions",
    "受入条件": "acceptance_criteria",
    "リスク": "risks",
    "確認事項": "questions",
}


def empty_result() -> dict[str, list[str]]:
    """Return a new empty result container."""
    return {
        "functions": [],
        "acceptance_criteria": [],
        "risks": [],
        "questions": [],
        "unknown": [],
    }


def classify_line(line: str) -> RequirementItem | None:
    """Classify one requirement line."""
    # TODO 2: 从 Day 3 迁移已经通过测试的单行分类逻辑。
    raise NotImplementedError("TODO 2: implement classify_line")


def parse_requirement(text: str) -> dict[str, list[str]]:
    """Parse all requirement lines."""
    # TODO 3: 使用 classify_line() 和 RequirementItem 的具名字段。
    raise NotImplementedError("TODO 3: implement parse_requirement")
