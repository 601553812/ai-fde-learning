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
    line = line.strip()
    if not line or line.startswith("#"):
        return None

    for label, category in PREFIX_TO_CATEGORY.items():
        for separator in (":", "："):
            marker = f"{label}{separator}"
            if line.startswith(marker):
                content = line[len(marker) :].strip()
                if not content:
                    return RequirementItem(category="unknown", content=line)
                return RequirementItem(category=category, content=content)

    return RequirementItem(category="unknown", content=line)


def parse_requirement(text: str) -> dict[str, list[str]]:
    """Parse all requirement lines."""
    result = empty_result()

    for line in text.splitlines():
        item = classify_line(line)
        if item is None:
            continue
        result[item.category].append(item.content)

    return result
