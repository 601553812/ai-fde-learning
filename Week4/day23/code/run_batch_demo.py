"""Provided offline CLI: emits results without saving files."""

import argparse
from dataclasses import asdict
import json
import sys

from .batch import Task, run_batch
from .batch_fakes import RecordingFactory
from .fakes import RecordingSleeper, status_error
from .summary import summarize


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run an offline batch of requirement tasks")
    parser.add_argument("--scenario", choices=("mixed", "empty", "duplicate"), default="mixed")
    parser.add_argument("--max-attempts", type=int, choices=(1, 2, 3), default=3)
    args = parser.parse_args(argv)
    tasks = [Task("A", "CSV出力"), Task("B", "認証"), Task("C", "検索")]
    if args.scenario == "empty":
        tasks = []
    elif args.scenario == "duplicate":
        tasks.append(Task("A", "別の入力"))
    factory = RecordingFactory({"A": ["日本語"], "B": [status_error(403)],
                                "C": [status_error(503), "回復"]})
    print("本地模拟：一份报告对应一个任务；不证明内容准确。", file=sys.stderr)
    try:
        rows = run_batch(tasks, factory, max_attempts=args.max_attempts,
                         sleeper=RecordingSleeper())
    except NotImplementedError:
        print(json.dumps({"mode": "simulated", "error": "TODO_not_completed"}))
        return 2
    except ValueError:
        print(json.dumps({"mode": "simulated", "error": "duplicate task_id"}))
        return 2
    stats = summarize([row.report for row in rows])
    print(json.dumps({"mode": "simulated", "tasks": [asdict(row) for row in rows],
                      "summary": stats}, ensure_ascii=False))
    return 1 if stats["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
