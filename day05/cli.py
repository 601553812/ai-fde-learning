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
    # TODO 1: 添加 input_path、output_path 和 -v/--verbose。
    raise NotImplementedError("TODO 1: implement build_parser")


def configure_logging(verbose: bool) -> None:
    """Configure application logging for normal or verbose output."""
    # TODO 2: verbose 使用 DEBUG，否则使用 INFO。
    raise NotImplementedError("TODO 2: implement configure_logging")


def run(input_path: Path, output_path: Path) -> int:
    """Read input, write JSON, log results, and return an exit code."""
    # TODO 3: 使用 LOGGER 完成读取、异常、校验、写入和退出码处理。
    raise NotImplementedError("TODO 3: implement run")


def main(argv: list[str] | None = None) -> int:
    """Parse command-line arguments and run the application."""
    # TODO 4: 连接 build_parser、configure_logging 和 run。
    raise NotImplementedError("TODO 4: implement main")


if __name__ == "__main__":
    raise SystemExit(main())
