"""Run one selected Day 16 case through the real Gemini gateway."""

import argparse
import json
import os
import sys

from Week2.day14.service import InvalidModelOutput, decode_requirements
from Week3.day15.model_client import PromptedModelClient
from Week3.day16.gemini_gateway import DEFAULT_MODEL, GeminiGateway
from Week3.day16.preview import load_case


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Call Gemini for one self-made Day 16 case")
    parser.add_argument("--case", choices=("A", "B", "C"), default="A")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not os.getenv("GEMINI_API_KEY"):
        print("ERROR: 未检测到 GEMINI_API_KEY；请在当前终端重新打开后再运行。", file=sys.stderr)
        return 2

    case = load_case(args.case)
    client = PromptedModelClient(GeminiGateway())

    print(f"MODEL={DEFAULT_MODEL}")
    print(f"CASE={args.case}")
    print("Calling Gemini once; raw model output follows.")
    raw = client.generate(case["text"])
    print(raw)

    try:
        requirements = decode_requirements(raw)
    except InvalidModelOutput:
        print("STRUCTURE_VALID=False")
        print("CONTENT_REVIEW=无法按项目 JSON 契约解析；请保留上面的原始输出进行人工核查。")
        return 0

    print("STRUCTURE_VALID=True")
    print("PARSED_REQUIREMENTS=" + json.dumps(requirements.model_dump(), ensure_ascii=False))
    print("CONTENT_REVIEW=" + case["check"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
