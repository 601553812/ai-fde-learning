"""已提供：离线回看 Day34 的公开回答，并排展示引用的原资料。"""

import argparse
import json
from dataclasses import asdict

from .cases import sample_chunks
from .citation_sources import find_cited_chunks
from .citations import check_citations
from .context import build_context
from .retrieval import RetrievalHit


# A/B 是 Day34 已记录的原回答；第三行明确是反例，不冒充模型结果。
DEMO_ANSWERS = [
    ("A", "recorded_day34", "返品 期限", "返品期限は30日です。[1]"),
    ("B", "recorded_day34", "返品 送料", "資料からは回答できません。"),
    ("wrong_90", "synthetic", "返品 期限", "返品期限は90日です。[1]"),
]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Day37：离线并排查看回答与引用原文")
    parser.parse_args(argv)
    # 使用当天复制的自制原文；没有创建网关，也没有再次询问模型。
    context = build_context([RetrievalHit(chunk, 1) for chunk in sample_chunks()], 500)
    for case, origin, question, answer in DEMO_ANSWERS:
        cited_chunks = find_cited_chunks(answer, context)
        # context 保存全部实际资料；cited_chunks 只保存回答写出的有效编号所指片段。
        print(json.dumps({
            "case": case, "answer_origin": origin, "question": question,
            "answer": answer, "context": asdict(context),
            "citation_errors": check_citations(answer, context),
            "cited_chunks": [asdict(chunk) for chunk in cited_chunks],
            "gateway_calls": 0,
        }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except NotImplementedError:
        print("请先完成 find_cited_chunks，再运行原文对照演示。")
        raise SystemExit(1)
