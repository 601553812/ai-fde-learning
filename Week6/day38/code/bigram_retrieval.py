"""字符对检索练习：不接收人工预期，不生成回答，也不访问网络。"""

from .chunking import Chunk
from .retrieval import RetrievalHit


def character_bigrams(text: str) -> set[str]:
    """已提供：先统一大小写，收集两个字符都为字母或数字的相邻字符对。"""
    normalized = text.casefold()
    pairs = set()
    for index in range(len(normalized) - 1):
        # 不跨越空白或标点拼接；日文汉字、假名也可以通过isalnum。
        pair = normalized[index:index + 2]
        if pair[0].isalnum() and pair[1].isalnum():
            pairs.add(pair)
    return pairs


def retrieve_bigrams(chunks: list[Chunk], query: str, top_k: int) -> list[RetrievalHit]:
    """按共同的不同字符对计分，先稳定排名，再限制返回条数。"""
    # 即使没有资料，也先按契约顺序检查问题与上限。
    if not query or query.strip() == '':
        raise ValueError('invalid_query')
    if top_k <= 0:
        raise ValueError('invalid_top_k')
    result = []
    query_bigrams = character_bigrams(query)
    for chunk in chunks:
        # 两边都是去重集合；逐个检查共有字符对，重复文字不会重复加分。
        chunk_bigrams = character_bigrams(chunk.text)
        score = 0
        for bigram in chunk_bigrams:
            if bigram in query_bigrams:
                score += 1
        if score > 0:
            # 新建命中记录，内部仍保留输入中的原chunk对象。
            result.append(RetrievalHit(chunk, score))
    # 只排序本次结果，不改变原chunks；同分保持原输入顺序。
    result.sort(key=lambda x: x.score, reverse=True)
    return result[:top_k]
