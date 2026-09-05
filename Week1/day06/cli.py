"""Command-line entry point with a validated Pydantic output schema."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .models import AnalysisOutput, RequirementData
from .parser import parse_requirement
from .validation import validate_result


LOGGER = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Build and return the command-line argument parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_path", type=Path)
    parser.add_argument("output_path", type=Path)
    parser.add_argument("-v", "--verbose", action="store_true")
    return parser


def configure_logging(verbose: bool) -> None:
    """Configure application logging for normal or verbose output."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
        force=True,
    )


def build_output(
    requirements: dict[str, list[str]],
    validation_errors: list[str],
) -> AnalysisOutput:
    """Validate parser data and build the versioned output model."""
    model_requirements = RequirementData.model_validate(requirements)
    analysis = AnalysisOutput.model_validate({"requirements": model_requirements,"validation_errors": validation_errors})
    return analysis



def run(input_path: Path, output_path: Path) -> int:
    """Read input, validate output, write JSON, and return an exit code."""
    LOGGER.debug("Reading: %s", input_path)
    try:
        text = input_path.read_text(encoding="utf-8")
    except (FileNotFoundError, UnicodeDecodeError) as exc:
        LOGGER.error("Could not read input: %s", exc)
        return 1

    requirements = parse_requirement(text)
    validation_errors = validate_result(requirements)
    for error in validation_errors:
        LOGGER.warning("%s", error)

    output = build_output(requirements, validation_errors)
    json_str = output.model_dump_json(indent=2)
    output_path.write_text(json_str, "utf-8")
    LOGGER.info("Created: %s", output_path)
    return 0 if not validation_errors else 2


def main(argv: list[str] | None = None) -> int:
    """Parse command-line arguments and run the application."""
    args = build_parser().parse_args(argv)
    configure_logging(verbose=args.verbose)
    return run(input_path=args.input_path, output_path=args.output_path)


if __name__ == "__main__":
    raise SystemExit(main())
