"""已提供的离线演示：展示编号错误，不联网或写文件。"""

import json
from dataclasses import asdict

from .chunking import Chunk
from .citations import review_qa_result
from .model_client import RecordingGateway
from .qa_service import answer_question


def main() -> None:
    chunk = Chunk("faq.txt", 0, 0, 8, "返品期限は30日")
    cases = [
        ("valid_id", "返品", "返品期限は30日です。[1]"),
        ("unknown_id", "返品", "返品期限は30日です。[99]"),
        ("missing_id", "返品", "返品期限は30日です。"),
        ("wrong_content", "返品", "返品期限は90日です。[1]"),
        ("no_context", "駐車場", "不应使用的文字。[99]"),
    ]
    for case, question, raw in cases:
        # 每个案例使用新替身，calls 只属于本次问答。
        gateway = RecordingGateway(raw)
        result = answer_question([chunk], question, 2, 100, gateway)
        errors = review_qa_result(result)
        # 将原问答结果与单独的引用错误并排输出，保留原状态含义。
        print(json.dumps({
            "case": case,
            **asdict(result),
            "citation_errors": errors,
            "gateway_calls": len(gateway.calls),
        }, ensure_ascii=False))


if __name__ == "__main__":
    # 未完成的 TODO 用简短提示结束；不把占位错误当成网关故障。
    try:
        main()
    except NotImplementedError:
        print("请先完成 check_citations，再运行引用演示。")
        raise SystemExit(1)
