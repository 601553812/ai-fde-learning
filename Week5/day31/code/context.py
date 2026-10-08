"""Prepare bounded, traceable evidence text without generating an answer."""

from dataclasses import dataclass

from .chunking import Chunk
from .retrieval import RetrievalHit


@dataclass(frozen=True)
class ContextBundle:
    text: str
    chunks: list[Chunk]


def build_context(hits: list[RetrievalHit], max_chars: int) -> ContextBundle:
    if max_chars <= 0:
        raise ValueError("invalid_context_limit")
    num_hit = 1
    text = ""
    chunks = []
    separator = "\n\n"
    for hit in hits:
        hit_text = f"[{num_hit}] {hit.chunk.source_name} ({hit.chunk.start}:{hit.chunk.end})\n{hit.chunk.text}"
        if max_chars >= len(text)+len(hit_text):
            if num_hit != 1 and max_chars < len(text)+len(hit_text)+len(separator):
                continue
            if num_hit != 1:
                text += separator
            num_hit += 1
            text += hit_text
            chunks.append(hit.chunk)
    context = ContextBundle(text=text, chunks=chunks)
    return context
