"""Provided request inspection only: no gateway, model, network, or output file."""

import argparse
import json
from pathlib import Path

from Week3.day15.prompt import build_request


def load_case(case_id: str) -> dict:
    cases = json.loads(Path(__file__).with_name("cases.json").read_text(encoding="utf-8"))
    return next(item for item in cases if item["id"] == case_id)


def main() -> int:
    parser = argparse.ArgumentParser(description="Preview a Day 16 request without calling a model")
    parser.add_argument("--case", choices=["A", "B", "C"], default="A")
    args = parser.parse_args()
    case = load_case(args.case)
    request = build_request(case["text"])
    print("PREVIEW ONLY: no model call")
    print("Case:", case["id"])
    print("Instructions:", request.instructions)
    print("Input JSON:", request.input)
    print("Decoded document:", json.loads(request.input)["document"])
    print("Review focus:", case["check"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
