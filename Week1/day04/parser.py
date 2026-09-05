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
    """Classify one line into a RequirementItem."""
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    for category in PREFIX_TO_CATEGORY.keys():
        if line.startswith(category):
            if line.find(":") != -1:
                content = line.split(":", 1)[1].strip()
            elif line.find("：") != -1:
                content = line.split("：", 1)[1].strip()
            else:
                return RequirementItem("unknown", line)
            if content == "":
                return RequirementItem("unknown", line)
            return RequirementItem(PREFIX_TO_CATEGORY[category], content)
        else:
            continue
    return RequirementItem("unknown", line)


def parse_requirement(text: str) -> dict[str, list[str]]:
    """Parse all requirement lines."""
    result = empty_result()

    for line in text.splitlines():
        item = classify_line(line)
        if item is None:
            continue
        else:
            result[item.category].append(item.content)
    return result
