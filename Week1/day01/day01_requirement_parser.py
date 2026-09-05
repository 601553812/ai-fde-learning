"""Day 1 homework: convert a Japanese requirement text file to JSON."""

from __future__ import annotations

import json
from pathlib import Path


def empty_result() -> dict[str, list[str]]:
    """Return a new empty result container."""
    return {
        "functions": [],
        "acceptance_criteria": [],
        "risks": [],
        "questions": [],
        "unknown": [],
    }


def classify_line(line: str) -> tuple[str, str] | None:
    """Classify one line and return (category, content).

    Return None for blank lines and comment lines.
    Unknown non-empty lines should use the category ``unknown``.
    """
    line = line.strip()
    if not line or line.startswith("#"):
        return None

    if line.startswith("機能:") :
        tuple_functions = ("functions",line.split(":", 1)[1].strip())
        return tuple_functions
    elif line.startswith("受入条件:") :
        tuple_acceptance_criteria = ("acceptance_criteria", line.split(":", 1)[1].strip())
        return tuple_acceptance_criteria
    elif line.startswith("リスク:") :
        tuple_risks = ("risks", line.split(":", 1)[1].strip())
        return tuple_risks
    elif line.startswith("確認事項:") :
        tuple_questions = ("questions", line.split(":", 1)[1].strip())
        return tuple_questions
    else:
        tuple_unknown = ("unknown", line)
        return tuple_unknown


def parse_requirement(text: str) -> dict[str, list[str]]:
    """Parse all lines from the input text into a structured dictionary."""
    result = empty_result()

    for line in text.splitlines():
        tuple_str = classify_line(line)
        if tuple_str is None:
            continue
        key = tuple_str[0]
        value = tuple_str[1]
        if key == "functions":
            result["functions"].append(value)
        elif key == "acceptance_criteria":
            result["acceptance_criteria"].append(value)
        elif key == "risks":
            result["risks"].append(value)
        elif key == "questions":
            result["questions"].append(value)
        else:
            result["unknown"].append(value)
    return result


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    input_path = base_dir / "sample_requirement.txt"
    output_path = base_dir / "result.json"

    source_text = input_path.read_text(encoding="utf-8")
    parsed = parse_requirement(source_text)

    with output_path.open("w", encoding="utf-8") as output_file:
        json.dump(parsed, output_file, ensure_ascii=False, indent=2)

    print(f"Created: {output_path}")


if __name__ == "__main__":
    main()
