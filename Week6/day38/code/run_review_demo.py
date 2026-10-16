"""已提供：显示四条人工核查示例及汇总，不联网、不写文件。"""

import argparse
import json
from dataclasses import asdict

from .qa_review import make_review_record, summarize_reviews
from .review_cases import demo_review_inputs


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Day38：离线人工依据核查记录与汇总")
    parser.parse_args(argv)
    rows = []
    records = []
    for item in demo_review_inputs():
        # 先保存一例的人工结论和原结果；没有网关、回调或外部服务。
        record = make_review_record(
            item.case_id, item.question, item.result, item.verdict, item.reason,
        )
        records.append(record)
        rows.append({
            "answer_origin": item.answer_origin,
            "review_origin": "provided_manual_example",
            "record": asdict(record),
        })
    # 所有记录建立成功后才打印一次完整报告，不留下半份 JSON。
    summary = summarize_reviews(records)
    print(json.dumps({
        "reviews": rows, "summary": asdict(summary), "gateway_calls": 0,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except NotImplementedError:
        print("请先完成 qa_review.py 的两个 TODO，再运行核查汇总演示。")
        raise SystemExit(1)
