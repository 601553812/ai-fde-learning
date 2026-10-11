"""只检查回答中的资料编号是否存在，不判断文字是否有依据。"""

import re

from .context import ContextBundle
from .qa_service import QAResult


def extract_citation_ids(answer: str) -> list[int]:
    """已提供：按出现顺序提取半角方括号里的 ASCII 整数，保留重复。"""
    # findall 返回数字字符串；例如 [2][01][2] 得到 ["2", "01", "2"]。
    raw_ids = re.findall(r"\[([0-9]+)\]", answer)
    # 转成整数后 [01] 与 [1] 都表示资料 1；没有匹配就返回空列表。
    return [int(raw_id) for raw_id in raw_ids]


def check_citations(answer: str, context: ContextBundle) -> list[str]:
    """检查实际发送资料的编号范围，按首次出现顺序报告未知编号。"""
    # 提取回答里的编号；合法上限取实际发送块数，不取检索命中数。
    ids = extract_citation_ids(answer)
    actual_send_chunk_len = len(context.chunks)
    results = []
    # 没有编号与有未知编号是两种不同情况。
    if not ids:
        return ["missing_citation"]
    for check_id in ids:
        if not 1 <= check_id <= actual_send_chunk_len:
            # 逐个检查并避免重复错误；合法编号不会让其他未知编号通过。
            if f"unknown_citation:{check_id}" not in results:
                results.append(f"unknown_citation:{check_id}")
    return results


def review_qa_result(result: QAResult) -> list[str]:
    """已提供：无资料分支跳过引用检查；生成分支检查原回答。"""
    # no_context 的固定提示本来就没有引用；[] 表示这里没有引用错误，
    # 不代表存在一份通过内容检查的模型答案。
    if result.status == "no_context":
        return []
    # 只使用这次结果内的资料，不改变 status、answer 或原片段对象。
    return check_citations(result.answer, result.context)
