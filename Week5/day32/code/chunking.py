"""Split local text into traceable chunks without calling a model or network."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Document:
    """一份原始文档；source_name 为可公开的来源名。"""
    source_name: str
    text: str


@dataclass(frozen=True)
class Chunk:
    """原文片段：text 对应原文 [start:end]，end 不包含在片段内。"""
    source_name: str
    chunk_index: int
    start: int
    end: int
    text: str


def chunk_document(document: Document, max_chars: int, overlap_chars: int) -> list[Chunk]:
    """保留 Day29 的固定字符切块行为，不改历史实现。"""
    # 每次调用创建新列表；原有变量名 chucks 表示本次片段结果。
    chucks = []
    # 必须能够向前移动，重叠量不能达到或超过块长。
    if max_chars>0 and 0<=overlap_chars<max_chars:
        if document.text is None or len(document.text)==0:
            return []
        else :
            # 先生成第一块；min 保证末尾不越过原文长度。
            chunk_index = 0
            start = 0
            end = min(start + max_chars, len(document.text))
            text = document.text[start:end]
            chucks.append(Chunk(source_name=document.source_name,chunk_index=chunk_index,start= start, end =end, text =text))
            while end < len(document.text):
                # 下一块从上一块末尾往前 overlap_chars 个字符开始。
                start = end-overlap_chars
                end=min(start + max_chars, len(document.text))
                text= document.text[start:end]
                chunk_index+=1
                # 记录同一文档内的块序号，与上下文中的 [1] 编号不同。
                chucks.append(Chunk(source_name=document.source_name,chunk_index=chunk_index,start= start, end =end, text =text))

        return chucks
    else:
        raise ValueError('invalid_chunk_size')


def chunk_documents(
    documents: list[Document], max_chars: int, overlap_chars: int
) -> list[Chunk]:
    """保持文档顺序；每份文档内部的块序号从 0 重新开始。"""
    chunks: list[Chunk] = []
    for document in documents:
        # extend 将一份文档的多块逐项加入总列表，而非嵌套成一个列表。
        chunks.extend(chunk_document(document, max_chars, overlap_chars))
    return chunks
