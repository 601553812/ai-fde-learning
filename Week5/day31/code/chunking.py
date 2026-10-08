"""Split local text into traceable chunks without calling a model or network."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Document:
    source_name: str
    text: str


@dataclass(frozen=True)
class Chunk:
    source_name: str
    chunk_index: int
    start: int
    end: int
    text: str


def chunk_document(document: Document, max_chars: int, overlap_chars: int) -> list[Chunk]:
    chucks = []
    if max_chars>0 and 0<=overlap_chars<max_chars:
        if document.text is None or len(document.text)==0:
            return []
        else :
            chunk_index = 0
            start = 0
            end = min(start + max_chars, len(document.text))
            text = document.text[start:end]
            chucks.append(Chunk(source_name=document.source_name,chunk_index=chunk_index,start= start, end =end, text =text))
            while end < len(document.text):
                start = end-overlap_chars
                end=min(start + max_chars, len(document.text))
                text= document.text[start:end]
                chunk_index+=1
                chucks.append(Chunk(source_name=document.source_name,chunk_index=chunk_index,start= start, end =end, text =text))

        return chucks
    else:
        raise ValueError('invalid_chunk_size')


def chunk_documents(
    documents: list[Document], max_chars: int, overlap_chars: int
) -> list[Chunk]:
    """Keep input document order; chunk_index restarts within each document."""
    chunks: list[Chunk] = []
    for document in documents:
        chunks.extend(chunk_document(document, max_chars, overlap_chars))
    return chunks
