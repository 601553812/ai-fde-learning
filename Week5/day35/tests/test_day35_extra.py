"""用原文块序号不同于引用编号的资料，独立验证定位。"""
from Week5.day35.code.chunking import Chunk
from Week5.day35.code.retrieval import RetrievalHit
from Week5.day35.code.context import build_context
from Week5.day35.code.citation_sources import find_cited_chunks


def test_citation_uses_sent_position_not_document_chunk_index():
    # 原文内的块序号刻意取 7 和 3；本次发送顺序仍为第一块、第二块。
    first = Chunk("a.txt", 7, 0, 2, "返品")
    second = Chunk("b.txt", 3, 0, 2, "送料")
    hits = [RetrievalHit(first, 1), RetrievalHit(second, 1)]
    context = build_context(hits, 500)
    answer = "送料の説明。[2][2][99][0]"
    text = context.text
    chunks = context.chunks.copy()
    # 记录输入后执行一次；重复 [2] 与越界 [99]/[0] 同时出现在本次回答中。
    result_chunks = find_cited_chunks(answer, context)
    # 完整结果与对象身份分别验证去重、过滤和返回原对象。
    assert result_chunks == [second]
    assert result_chunks[0] is second
    # 原资料文字、完整片段顺序及两项对象身份都应保持不变。
    assert text == context.text
    assert chunks == context.chunks
    assert context.chunks[0] is first
    assert context.chunks[1] is second
