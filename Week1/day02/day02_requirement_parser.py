"""Day 2 homework: refactor the requirement parser and handle file errors."""

from __future__ import annotations

import json
import sys
from pathlib import Path

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


def classify_line(line: str) -> tuple[str, str] | None:
    """Return (category, content), or None for blank/comment lines."""

    line = str.strip(line)
    if not line or line.startswith("#"):
        return None
    else:
        for key in PREFIX_TO_CATEGORY.keys():
            if line.startswith(key):
                if line.find(":") != -1:
                    content = line.split(":",1)[1].strip()
                    if content:
                        return PREFIX_TO_CATEGORY[key], content
                    else :
                        return "unknown", line

                elif line.find("：") != -1:
                    content = line.split("：",1)[1].strip()
                    if content:
                        return PREFIX_TO_CATEGORY[key], content
                    else :
                        return "unknown", line
        return "unknown", line


def parse_requirement(text: str) -> dict[str, list[str]]:
    """Parse all lines without repeating one branch per category."""
    result = empty_result()

    for line in text.splitlines():
        classified = classify_line(line)
        if classified :
            category, content = classified
            result[category].append(content)
    return result


def run(input_path: Path, output_path: Path) -> int:
    """Parse one UTF-8 file, write JSON, and return a process exit code."""
    try:
        text = input_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"Input file not found: {input_path}")
        return 1
    except UnicodeDecodeError:
        print(f"Input file is not valid UTF-8: {input_path}")
        return 1
    output_path.write_text(json.dumps(parse_requirement(text),ensure_ascii=False,indent=2),encoding="utf-8")
    print("Created: {output_path}".format(output_path=output_path))
    return 0


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: python day02_requirement_parser.py INPUT_PATH OUTPUT_PATH")
        raise SystemExit(2)

    exit_code = run(Path(sys.argv[1]), Path(sys.argv[2]))
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
