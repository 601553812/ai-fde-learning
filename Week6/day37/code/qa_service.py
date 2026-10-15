"""Connect retrieval, bounded context, and a single replaceable gateway call."""

from dataclasses import dataclass

from .chunking import Chunk
from .context import ContextBundle, build_context
from .model_client import ModelGateway
from .qa_prompt import build_qa_request
from .retrieval import retrieve_chunks


NO_CONTEXT_ANSWER = "資料からは回答できません。"


@dataclass(frozen=True)
class QAResult:
    """一次问答的结果；generated 仅表示网关返回文字。"""

    status: str  # generated 或 no_context，不是内容/引用质量结论。
    answer: str  # 网关原返回文字，或无资料路径的固定提示。
    context: ContextBundle  # 本次真正使用的资料文字与原片段对象。


def answer_question(
    chunks: list[Chunk],
    question: str,
    top_k: int,
    max_context_chars: int,
    gateway: ModelGateway,
) -> QAResult:
    """依次检索、整理资料；有资料时调用传入的网关一次。"""
    # 先检查问题，让空白问题的错误优先于两个上限的错误。
    if question.strip() == "":
        raise ValueError("invalid_question")
    # 原 question 传入检索；分词与 top_k 校验由已有函数负责。
    hits = retrieve_chunks(chunks,question,top_k)
    # 即使没有命中也调用，确保字符上限仍被校验。
    context = build_context(hits,max_context_chars)
    # 空列表为假：无命中或所有块放不下时，跳过请求构造和网关调用。
    if not context.chunks :
        return QAResult("no_context", NO_CONTEXT_ANSWER, context)
    # 只发送预算内的 context.text，不发送所有命中或 Chunk 对象。
    request = build_qa_request(question,context)
    # 调用的是传入对象的方法；异常自然向上传播，不重试或伪造答案。
    answer = gateway.complete(request)
    # 保留 Day32 的原返回行为；编号检查由 citations.py 在返回后另做。
    return QAResult("generated", answer, context)
