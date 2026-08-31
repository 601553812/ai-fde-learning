"""Command-line entry point for the Day 4 requirement tool."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .parser import parse_requirement
from .validation import validate_result


def run(input_path: Path, output_path: Path) -> int:
    """Read input, write JSON, and return a process exit code."""
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
        print("Usage: python -m day04.cli INPUT_PATH OUTPUT_PATH")
        raise SystemExit(2)

    raise SystemExit(run(Path(sys.argv[1]), Path(sys.argv[2])))


if __name__ == "__main__":
    main()
