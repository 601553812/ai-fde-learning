"""自制资料及三个问题；人工预期只供核查，不拼进模型请求。"""

from .chunking import Document, chunk_documents

DOCUMENTS = [Document("returns_faq.txt", "返品期限は30日です。\n開封済みの商品は返品できません。")]
QUESTIONS = {
    "A": "返品 期限",  # 空格便于已有关键词检索命中；模型仍接收完整原问题。
    "B": "返品 送料",  # 命中“返品”，但原文没有谁承担送料的答案。
    "C": "駐車場",  # 无关键词命中，应用应在模型调用前结束。
}


def sample_chunks():
    # 本日每份资料只切成一块；不改变已学过的切块算法。
    return chunk_documents(DOCUMENTS, 100, 0)
