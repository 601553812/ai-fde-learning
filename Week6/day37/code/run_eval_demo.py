"""已提供：固定问题→检索→字符预算→证据检查→汇总；离线零模型调用。"""

import argparse
import json
from dataclasses import asdict

from .context import build_context
from .eval_cases import evaluation_cases, evaluation_chunks
from .retrieval import retrieve_chunks
from .retrieval_eval import check_evidence, summarize_evidence


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Day37：固定问题集的发送资料证据检查")
    parser.parse_args(argv)
    chunks = evaluation_chunks()
    checks = []
    rows = []
    for case in evaluation_cases():
        # 检索只接收问题，expected_evidence没有传入；避免用答案反向找资料。
        hits = retrieve_chunks(chunks, case.question, 2)
        context = build_context(hits, 500)
        check = check_evidence(case, context)
        checks.append(check)
        rows.append({"retrieved_count": len(hits), "check": asdict(check)})
    summary = summarize_evidence(checks)
    # 最后一次性打印完整JSON；miss是本次评测结果，不是程序执行失败。
    print(json.dumps({
        "dataset_origin": "provided_synthetic_faq_v1",
        "top_k": 2, "max_chars": 500, "results": rows,
        "summary": asdict(summary), "gateway_calls": 0,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except NotImplementedError:
        print("请先完成 retrieval_eval.py 的两个 TODO，再运行固定评测集。")
        raise SystemExit(1)
