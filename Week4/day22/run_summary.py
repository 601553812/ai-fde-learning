"""Provided offline demonstration: no API keys, network calls, or actual sleeps."""

import argparse
import json
import sys

from .fakes import RecordingSleeper, SequenceGateway, status_error
from .prompt import build_request
from .retry_service import call_with_retry
from .summary import summarize


def main(argv=None):
    parser = argparse.ArgumentParser(description="Summarize local simulated retry reports")
    parser.add_argument("--scenario", choices=("mixed", "success", "empty"), default="mixed")
    args = parser.parse_args(argv)
    outcomes = {
        "mixed": [["日本語"], [status_error(503), "日本語"],
                  [status_error(503), status_error(403), "must not reach"]],
        "success": [["日本語"]],
        "empty": [],
    }[args.scenario]
    reports = []
    for sequence in outcomes:
        reports.append(call_with_retry(SequenceGateway(sequence), build_request("CSV出力"),
                                       sleeper=RecordingSleeper()))
    print("本地模拟：只汇总调用层结果，不证明模型内容正确。", file=sys.stderr)
    try:
        result = summarize(reports)
    except NotImplementedError:
        print(json.dumps({"mode": "simulated", "error": "TODO_not_completed"}))
        return 2
    print(json.dumps({"mode": "simulated", "summary": result}, ensure_ascii=False))
    return 1 if result["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
