"""Rank local chunks by query terms; no model or network is involved."""

from dataclasses import dataclass

from .chunking import Chunk


@dataclass(frozen=True)
class RetrievalHit:
    """一条检索命中：原片段对象，加上匹配词项的计数。"""
    chunk: Chunk
    score: int


def retrieve_chunks(chunks: list[Chunk], query: str, top_k: int) -> list[RetrievalHit]:
    """按空白分词做子串匹配；同分保持输入顺序，再取前 top_k 项。"""
    # split() 对空串或全空白字符串返回空列表。
    if not query.split():
        raise ValueError("invalid_query")
    if top_k <= 0:
        raise ValueError("invalid_top_k")
    results = query.split()
    # 去重并统一大小写，重复词项只计一次分。
    results_set = set()
    for result in results:
        results_set.add(result.casefold())
    hits = []
    for chunk in chunks:
        score = 0
        for result in results_set:
            # 只匹配原文，不按来源文件名评分；这不是语义检索。
            if result in chunk.text.casefold():
                score += 1
        if score > 0:
            # 保留原 chunk 对象，便于继续追溯出处。
            hit = RetrievalHit(chunk, score)
            hits.append(hit)
    # Python 排序稳定：降序比较 score 时，同分不改变相对顺序。
    hits.sort(key=lambda x: x.score, reverse=True)
    return hits[:top_k]
