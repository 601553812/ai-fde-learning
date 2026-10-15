"""事先固定问题和期望原文；预期只给评测器，不参与检索或模型请求。"""

from dataclasses import dataclass

from .chunking import Document, chunk_documents


@dataclass(frozen=True)
class ExpectedEvidence:
    """本日每个有答案的问题只要求一处证据：来源名与完整原句。"""

    source_name: str
    quote: str


@dataclass(frozen=True)
class EvalCase:
    """None表示这份固定资料没有所问答案，不是期望检索列表为空。"""

    case_id: str
    question: str
    expected_evidence: ExpectedEvidence | None


def evaluation_documents() -> list[Document]:
    # 全部为自制FAQ；每次返回新列表，不涉及真实业务资料。
    return [
        Document("returns_faq.txt", "返品期限は30日です。\n開封済みの商品は返品できません。"),
        Document("delivery_guide.txt", "配送日数は3日です。\n配送状況は注文履歴で確認できます。"),
        Document("account_help.txt", "パスワードは設定画面から変更できます。"),
    ]


def evaluation_chunks():
    # 每份资料一块，今天不同时改变切块与检索算法。
    return chunk_documents(evaluation_documents(), 100, 0)


def evaluation_cases() -> list[EvalCase]:
    # 先写人工预期再运行；不能按照本次检索结果修改预期。
    return [
        EvalCase("R1", "返品 期限", ExpectedEvidence("returns_faq.txt", "返品期限は30日です。")),
        EvalCase("R2", "開封 返品", ExpectedEvidence("returns_faq.txt", "開封済みの商品は返品できません。")),
        EvalCase("R3", "配送 日数", ExpectedEvidence("delivery_guide.txt", "配送日数は3日です。")),
        # 旧算法按空白分词：这个自然问句整体不是原文的子串，会漏掉已有答案。
        EvalCase("R4", "パスワードを変更するには？", ExpectedEvidence("account_help.txt", "パスワードは設定画面から変更できます。")),
        EvalCase("N1", "返品 送料", None),  # 有相关词命中，但资料没有送料承担方。
        EvalCase("N2", "駐車場", None),  # 完全没有命中；同样没有已知答案。
    ]
