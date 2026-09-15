"""Print a request and fixed local result. No network or files are used."""

import argparse
import json

from Week2.day14.service import InvalidModelOutput, ModelOutputAnalyzer
from Week3.day15.model_client import PromptedModelClient, RecordingGateway


def main() -> int:
    parser = argparse.ArgumentParser(description="Day 15: inspect a local model request")
    parser.add_argument("--bad-output", action="store_true", help="simulate invalid model JSON")
    args = parser.parse_args()
    text = "機能: CSV出力\n受入条件: 3秒以内"
    raw = "not-json" if args.bad_output else '{"functions":["固定のデモ結果"],"acceptance_criteria":["確認済み"]}'
    fake = RecordingGateway(raw)
    analyzer = ModelOutputAnalyzer(PromptedModelClient(fake))
    try:
        output = analyzer.analyze(text)
    except NotImplementedError as error:
        print(str(error))
        return 2
    except InvalidModelOutput:
        print("Model returned invalid output")
        print("Gateway calls:", len(fake.calls))
        return 1
    if len(fake.calls) != 1:
        print("Expected exactly one gateway call")
        return 2
    request = fake.calls[0]
    print("LOCAL SIMULATION: no model inference")
    print("Instructions:", request.instructions)
    print("Input:", request.input)
    print("Output:", json.dumps(output.model_dump(), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
