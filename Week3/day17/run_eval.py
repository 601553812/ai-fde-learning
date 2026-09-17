"""Provided CLI: replay by default; live mode requires one explicit case."""

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from Week3.day17.evaluation import evaluate


def load_baseline() -> dict:
    return json.loads(Path(__file__).with_name("baseline.json").read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate recorded Day16 outputs or one live case")
    parser.add_argument("--case", choices=["A", "B", "C"])
    parser.add_argument("--live", action="store_true", help="Make one real Gemini call; requires --case")
    args = parser.parse_args()
    if args.live and args.case is None:
        parser.error("--live requires --case A, B or C")
    baseline = load_baseline()
    cases = [c for c in baseline["cases"] if args.case is None or c["id"] == args.case]
    client = None
    if args.live:
        from Week3.day15.model_client import PromptedModelClient
        from Week3.day16.gemini_gateway import GeminiGateway
        try:
            client = PromptedModelClient(GeminiGateway())
        except Exception as exc:
            print(json.dumps({"mode": "live", "error": "client_setup_failed", "error_type": type(exc).__name__}))
            return 2
    print(json.dumps({"mode": "live" if args.live else "replay", "source": "new request using Day16 gateway" if args.live else baseline["source"]}, ensure_ascii=False))
    results = []
    for case in cases:
        raw = case["raw"]
        if client is not None:
            try:
                raw = client.generate(case["text"])
            except Exception as exc:
                print(json.dumps({"case": case["id"], "error": "model_call_failed", "error_type": type(exc).__name__}))
                return 2
        try:
            result = evaluate(raw, case["must_contain"], case["must_be_empty"])
        except NotImplementedError:
            print("TODO: complete evaluation.py before running this command.")
            return 2
        results.append(result)
        print(json.dumps({"case": case["id"], "raw": raw, **asdict(result)}, ensure_ascii=False))
    print(json.dumps({"total": len(results), "structure_valid": sum(r.structure_valid for r in results), "content_passed": sum(r.content_passed is True for r in results)}))
    return 0 if all(r.content_passed is True for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
