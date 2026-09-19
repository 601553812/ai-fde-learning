"""Provided CLI. Default: offline. Optional live child has a 30-second budget."""

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import subprocess
import sys
from .call_service import call_once
from .gemini_gateway import GeminiGateway
from .prompt import build_request
from .scenarios import SCENARIOS, make_transport

TOTAL_TIMEOUT_SECONDS = 30


def emit(data):
    print(json.dumps(data, ensure_ascii=False), flush=True)


def run_live() -> int:
    print("正在调用 Gemini：单个案例，不自动重试；总等待上限约 30 秒。", file=sys.stderr, flush=True)
    try:
        process = subprocess.run(
            [sys.executable, "-X", "utf8", "-m", "Week3.day19.run_call", "--live-worker"],
            cwd=Path(__file__).resolve().parents[2], capture_output=True,
            text=True, encoding="utf-8", timeout=TOTAL_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        emit({"mode": "live", "ok": False, "raw": None, "error": "overall_timeout", "status_code": None})
        return 1
    except KeyboardInterrupt:
        emit({"mode": "live", "error": "cancelled"})
        return 130
    if process.stdout:
        print(process.stdout, end="", flush=True)
    else:
        emit({"mode": "live", "error": "worker_failed"})
    return process.returncode if process.returncode in (0, 1, 2, 130) else 2


def main() -> int:
    parser = argparse.ArgumentParser(description="Report one model call; offline by default")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--scenario", choices=SCENARIOS)
    mode.add_argument("--live", action="store_true", help="Optional single live call with a 30s total budget")
    mode.add_argument("--live-worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.live:
        return run_live()
    scenario = args.scenario or "success"
    gateway = None
    try:
        if args.live_worker:
            gateway = GeminiGateway()
        else:
            gateway = GeminiGateway(api_key="offline-placeholder", transport=make_transport(scenario))
        cases = json.loads(Path(__file__).with_name("cases.json").read_text(encoding="utf-8"))
        case = next(c for c in cases if c["id"] == "C")
        request = build_request(case["text"])
        print("已开始：" + ("真实调用" if args.live_worker else "本地模拟 " + scenario), file=sys.stderr, flush=True)
        result = call_once(gateway, request)
        emit({"mode": "live" if args.live_worker else "simulated", **asdict(result)})
        return 0 if result.ok else 1
    except NotImplementedError:
        emit({"error": "TODO_not_completed"})
        return 2
    except Exception as exc:
        emit({"error": "setup_or_unexpected_failure", "error_type": type(exc).__name__})
        return 2
    finally:
        if gateway is not None:
            gateway.close()


if __name__ == "__main__":
    raise SystemExit(main())
