"""Provided offline CLI: HTTPX mock responses; no live mode or API key lookup."""

import argparse
from dataclasses import asdict
import json
import sys
import time

import httpx

from .gemini_gateway import GeminiGateway
from .prompt import build_request
from .retry_service import call_with_retry
from .scenarios import RAW

SCENARIOS = {
    "success": (200,),
    "recover": (503, 200),
    "exhausted": (503, 503, 503),
    "auth_after_503": (503, 403, 200),
    "rate_limit": (429,),
    "timeout": ("timeout",),
}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Offline bounded-retry exercise; no live calls")
    parser.add_argument("--scenario", choices=SCENARIOS, default="recover")
    parser.add_argument("--max-attempts", type=int, choices=(1, 2, 3), default=3)
    args = parser.parse_args(argv)
    codes = SCENARIOS[args.scenario]
    sent = []

    def handle(request):
        index = len(sent)
        sent.append(request)
        if index >= len(codes):
            raise AssertionError("Unexpected extra request")
        code = codes[index]
        if code == "timeout":
            raise httpx.ReadTimeout("simulated timeout", request=request)
        if code == 200:
            return httpx.Response(200, json={"steps": [{"type": "model_output", "content": [
                {"type": "text", "text": RAW}]}]})
        return httpx.Response(code, json={"error": {"message": "simulated failure"}})

    def emit(data):
        print(json.dumps(data, ensure_ascii=False), flush=True)

    print("本地模拟：只对 503 有限重试；每次重试前等待 0.2 秒。", file=sys.stderr, flush=True)
    gateway = GeminiGateway(api_key="offline-placeholder", transport=httpx.MockTransport(handle))
    try:
        report = call_with_retry(gateway, build_request("注文一覧をCSVで出力したい。"),
                                 max_attempts=args.max_attempts, sleeper=time.sleep)
        emit({"mode": "simulated", **asdict(report)})
        return 0 if report.result.ok else 1
    except NotImplementedError:
        emit({"mode": "simulated", "error": "TODO_not_completed"})
        return 2
    except Exception as exc:
        emit({"mode": "simulated", "error": "unexpected_failure", "error_type": type(exc).__name__})
        return 2
    finally:
        gateway.close()


if __name__ == "__main__":
    raise SystemExit(main())
