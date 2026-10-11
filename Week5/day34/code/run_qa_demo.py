"""Provided local demo: fixed gateway text, no API key, network, or files."""

import json
from dataclasses import asdict

from .chunking import Document, chunk_documents
from .model_client import RecordingGateway
from .qa_service import answer_question


def main() -> None:
    """连续演示命中与未命中，检查第二次不会沿用第一次答案。"""
    # 自制 FAQ 经当前日切块函数得到片段列表。
    chunks = chunk_documents([Document("faq.txt", "返品期限は30日")], 20, 0)
    # 两次问答共用同一个记录网关，可核对总调用次数。
    gateway = RecordingGateway("返品期限は30日です。[1]")
    for question in ["返品 期限", "駐車場"]:
        result = answer_question(chunks, question, 2, 100, gateway)
        # asdict 将嵌套数据类转成字典；** 将字段展开到输出字典。
        print(json.dumps({"question": question, **asdict(result)}, ensure_ascii=False))
    # 有资料的问题调用一次；无资料问题不调用，总数应为 1。
    print(json.dumps({"gateway_calls": len(gateway.calls)}, ensure_ascii=False))


if __name__ == "__main__":
    # python -m 执行本模块时进入；普通 import 时不运行演示。
    main()
