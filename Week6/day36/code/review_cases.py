"""提供已知原文与人工核查示例；不伪造新的模型调用结果。"""

from dataclasses import dataclass

from .cases import sample_chunks
from .context import build_context
from .qa_service import QAResult
from .retrieval import RetrievalHit


@dataclass(frozen=True)
class ReviewInput:
    """供离线演示使用的输入；verdict 和 reason 已由人预先核对。"""

    case_id: str
    answer_origin: str
    question: str
    result: QAResult
    verdict: str
    reason: str


def demo_review_inputs() -> list[ReviewInput]:
    # 四例使用同一份公开资料；A/B 是 Day34 记录，另两例是明确标出的反例。
    context = build_context([RetrievalHit(chunk, 1) for chunk in sample_chunks()], 500)
    examples = [
        ("A", "recorded_day34", "返品 期限", "返品期限は30日です。[1]",
         "supported", "原文写明返品期限は30日です，支持30日回答。"),
        ("B", "recorded_day34", "返品 送料", "資料からは回答できません。",
         "correct_refusal", "已发送资料没有写送料由谁承担，拒答合理。"),
        ("wrong_90", "synthetic", "返品 期限", "返品期限は90日です。[1]",
         "unsupported", "原文明确写30日，与回答的90日冲突。"),
        ("wrong_refusal", "synthetic", "返品 期限", "資料からは回答できません。",
         "incorrect_refusal", "本题问期限，已发送资料明确写30日，拒答遗漏已有答案。"),
    ]
    inputs = []
    for case_id, origin, question, answer, verdict, reason in examples:
        # generated 表示已有一份待审回答；反例仅模拟这一结构，没有调用模型。
        result = QAResult("generated", answer, context)
        inputs.append(ReviewInput(case_id, origin, question, result, verdict, reason))
    return inputs
