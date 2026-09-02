"""Command-line entry point with argparse and logging."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from .parser import parse_requirement
from .validation import validate_result


LOGGER = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Build and return the command-line argument parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_path", type=Path)
    parser.add_argument("output_path", type=Path)
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",)
    return parser


def configure_logging(verbose: bool) -> None:
    """Configure application logging for normal or verbose output."""
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO,format="%(levelname)s %(name)s: %(message)s",force=True)


def run(input_path: Path, output_path: Path) -> int:
    """Read input, write JSON, log results, and return an exit code."""
    LOGGER.debug(input_path)
    try:
        text = input_path.read_text(encoding="utf-8")
    except (FileNotFoundError , UnicodeDecodeError) as exc:
        LOGGER.error(f": Error is {exc}")
        return 1
    dict = parse_requirement(text)
    errors = validate_result(dict)
    for error in errors:
        LOGGER.warning(error)
    payload = {
        "requirements": dict,
        "validation_errors": errors,
    }
    output_path.write_text(json.dumps(payload , ensure_ascii=False, indent=2), encoding="utf-8")
    LOGGER.info(output_path)
    if not errors:
        return 0
    return 2


def main(argv: list[str] | None = None) -> int:
    """Parse command-line arguments and run the application."""
    args = build_parser().parse_args(argv)
    configure_logging(verbose=args.verbose)
    return run(input_path=args.input_path, output_path=args.output_path)

if __name__ == "__main__":
    raise SystemExit(main())
