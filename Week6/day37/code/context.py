"""Prepare bounded, traceable evidence text without generating an answer."""

from dataclasses import dataclass

from .chunking import Chunk
from .retrieval import RetrievalHit


@dataclass(frozen=True)
class ContextBundle:
    """text 是要发送的资料文字；chunks[i] 对应其中的资料编号 i+1。"""
    text: str
    chunks: list[Chunk]


def build_context(hits: list[RetrievalHit], max_chars: int) -> ContextBundle:
    """按已有命中顺序装入完整资料块，放不下就跳过并继续。"""
    # 即使命中列表为空，也先拒绝非法上限。
    if max_chars <= 0:
        raise ValueError("invalid_context_limit")
    num_hit = 1
    # 本次结果从空字符串/列表开始，避免沿用上次调用的数据。
    text = ""
    chunks = []
    separator = "\n\n"
    for hit in hits:
        # 编号按成功纳入数递增，不使用原 chunk_index。
        hit_text = f"[{num_hit}] {hit.chunk.source_name} ({hit.chunk.start}:{hit.chunk.end})\n{hit.chunk.text}"
        if max_chars >= len(text)+len(hit_text):
            # 非首块还需计算两个换行；放不下继续尝试后续片段。
            if num_hit != 1 and max_chars < len(text)+len(hit_text)+len(separator):
                continue
            if num_hit != 1:
                text += separator
            num_hit += 1
            # 只纳入完整文字，同时保存同一个原片段对象。
            text += hit_text
            chunks.append(hit.chunk)
    context = ContextBundle(text=text, chunks=chunks)
    return context
