"""Day 3 homework: use a dataclass and validate parsed requirements."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path


PREFIX_TO_CATEGORY: dict[str, str] = {
    "機能": "functions",
    "受入条件": "acceptance_criteria",
    "リスク": "risks",
    "確認事項": "questions",
}


@dataclass(frozen=True)
class RequirementItem:
    """One classified requirement line with named fields."""

    category: str
    content: str


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
    """Classify one line into a RequirementItem."""
    # TODO 1: 处理空行、注释、两种冒号、空内容和未知行。
    # 内容中再次出现冒号时，必须保留后半部分。
    raise NotImplementedError("TODO 1: implement classify_line")


def parse_requirement(text: str) -> dict[str, list[str]]:
    """Parse all lines using RequirementItem named fields."""
    result = empty_result()

    # TODO 2: 使用 item is None、item.category 和 item.content。
    raise NotImplementedError("TODO 2: implement parse_requirement")


def validate_result(result: dict[str, list[str]]) -> list[str]:
    """Return validation errors for missing required sections."""
    # TODO 3: functions 和 acceptance_criteria 至少各有一项。
    raise NotImplementedError("TODO 3: implement validate_result")


def run(input_path: Path, output_path: Path) -> int:
    """Read input, write requirements and validation errors, and return a code."""
    try:
        text = input_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"Input file not found: {input_path}")
        return 1
    except UnicodeDecodeError:
        print(f"Input file is not valid UTF-8: {input_path}")
        return 1

    requirements = parse_requirement(text)
    validation_errors = validate_result(requirements)
    payload = {
        "requirements": requirements,
        "validation_errors": validation_errors,
    }
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Created: {output_path}")
    return 0 if not validation_errors else 2


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: python day03_requirement_parser.py INPUT_PATH OUTPUT_PATH")
        raise SystemExit(2)

    raise SystemExit(run(Path(sys.argv[1]), Path(sys.argv[2])))


if __name__ == "__main__":
    main()
