"""CLI boundary for fetching and saving validated requirement data."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Sequence

from Week1.day07.api_client import RequirementApiError, fetch_requirement


LOGGER = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Build the Day 8 command-line parser."""
    parser = argparse.ArgumentParser(
        description="HTTP API から要件データを取得し、JSON ファイルへ保存します。",
    )
    parser.add_argument("url", help="取得先の HTTP URL")
    parser.add_argument("output", type=Path, help="保存先の JSON ファイル")
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="HTTP タイムアウト秒数 (default: 5.0)",
    )
    return parser


def run(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return a process exit code."""
    args = build_parser().parse_args(argv)
    try :
        requirements = fetch_requirement(args.url, args.timeout)
    except RequirementApiError as e:
        LOGGER.error(e)
        return 1
    json = requirements.model_dump_json(indent=2)
    args.output.write_text(json,encoding="utf-8")
    LOGGER.info("output: %s", args.output)
    return 0


def main() -> None:
    """Process entry point."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    raise SystemExit(run())


if __name__ == "__main__":
    main()
