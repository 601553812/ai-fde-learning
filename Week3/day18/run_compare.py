"""Provided runner: preview by default, labelled replay, or two live requests."""

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path

from Week3.day15.prompt import build_request
from Week3.day16.gemini_gateway import DEFAULT_MODEL, GeminiGateway
from Week3.day17.evaluation import EvaluationResult, evaluate
from Week3.day17.run_eval import load_baseline
from Week3.day18.comparison import classify_change
from Week3.day18.prompt import build_candidate_request


def load_cases() -> dict:
    baseline = load_baseline()
    cases = {
        c["id"]: {**c, "fixture_source": baseline["source"]}
        for c in baseline["cases"] if c["id"] in ("A", "C")
    }
    case = json.loads(Path(__file__).with_name("cases.json").read_text(encoding="utf-8"))
    cases[case["id"]] = case
    return cases


def emit(data: dict) -> None:
    print(json.dumps(data, ensure_ascii=False))


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare baseline/candidate prompts on one fixed case")
    parser.add_argument("--case", choices=["A", "C", "D"], default="D")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--live", action="store_true", help="Make two real calls: baseline then candidate")
    mode.add_argument("--replay", action="store_true", help="Evaluate a labelled fixture; no prompt comparison")
    args = parser.parse_args()
    case = load_cases()[args.case]
    checks = (case["must_contain"], case["must_be_empty"])

    if args.replay:
        result = evaluate(case["raw"], *checks)
        emit({"mode": "replay", "case": args.case, "source": case["fixture_source"],
              "text": case["text"], "raw": case["raw"], "evaluation": asdict(result)})
        return 0 if result.content_passed is True else 1

    try:
        requests = {"baseline": build_request(case["text"]),
                    "candidate": build_candidate_request(case["text"])}
        before, after = requests.values()
        if after.input != before.input or not after.instructions.startswith(before.instructions):
            raise ValueError("Candidate must preserve the document and baseline instructions")
        if not after.instructions[len(before.instructions):].strip():
            raise ValueError("Candidate must add a nonempty rule")
        # Detect unfinished comparison TODO before spending any API calls.
        classify_change(EvaluationResult(True, True, []), EvaluationResult(True, True, []))
    except (NotImplementedError, ValueError) as exc:
        emit({"error": "complete_prompt_and_comparison_TODOs", "error_type": type(exc).__name__})
        return 2

    emit({"mode": "live" if args.live else "preview", "case": args.case, "model": DEFAULT_MODEL,
          "requests": {version: asdict(request) for version, request in requests.items()}})
    if not args.live:
        return 0

    try:
        gateway = GeminiGateway(model=DEFAULT_MODEL)
    except Exception as exc:
        emit({"error": "client_setup_failed", "error_type": type(exc).__name__})
        return 2
    results = {}
    for version, request in requests.items():
        try:
            raw = gateway.complete(request)
        except Exception as exc:
            # Avoid exposing SDK messages that might contain request credentials.
            emit({"version": version, "error": "model_call_failed", "error_type": type(exc).__name__})
            return 2
        result = evaluate(raw, *checks)
        results[version] = result
        emit({"version": version, "recorded_at": datetime.now(timezone.utc).isoformat(),
              "raw": raw, "evaluation": asdict(result)})
    emit({"case": args.case, "change": classify_change(results["baseline"], results["candidate"])})
    return 0 if results["candidate"].content_passed is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
