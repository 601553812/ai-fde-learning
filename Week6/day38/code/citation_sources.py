"""把回答中的编号对应到本次发送的原资料，供人查看。"""

from .chunking import Chunk
from .citations import extract_citation_ids
from .context import ContextBundle


def find_cited_chunks(answer: str, context: ContextBundle) -> list[Chunk]:
    """按回答中的首次引用顺序取原片段；保留原对象供人工核查。"""
    ids = extract_citation_ids(answer)
    # 结果按原编号列表的遍历顺序追加；set 仅用于记录已经取过的编号。
    chunks = []
    chunks_id = set()
    for id in ids:
        # 先检查引用编号的范围，再减 1 转为 Python 下标，避免 [0] 取到末项。
        if 1 <= id <= len(context.chunks):
            number = id - 1
            if id not in chunks_id:
                chunks_id.add(id)
                # 保存本次发送资料中的同一个 Chunk，不重新构造或修改原片段。
                chunks.append(context.chunks[number])
    return chunks
