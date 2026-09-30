"""Rank local chunks by query terms; no model or network is involved."""

from dataclasses import dataclass

from .chunking import Chunk


@dataclass(frozen=True)
class RetrievalHit:
    chunk: Chunk
    score: int


def retrieve_chunks(chunks: list[Chunk], query: str, top_k: int) -> list[RetrievalHit]:
    if not query.split():
        raise ValueError("invalid_query")
    if top_k <= 0:
        raise ValueError("invalid_top_k")
    results = query.split()
    results_set = set()
    for result in results:
        results_set.add(result.casefold())
    hits = []
    for chunk in chunks:
        score = 0
        for result in results_set:
            if result in chunk.text.casefold():
                score += 1
        if score > 0:
            hit = RetrievalHit(chunk, score)
            hits.append(hit)
    hits.sort(key=lambda x: x.score, reverse=True)
    return hits[:top_k]
