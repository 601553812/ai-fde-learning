"""Learner task: refine one classification boundary without changing input."""
from Week3.day15.prompt import ModelRequest, build_request


CANDIDATE_RULES = "未确认的候选条件放在questions,已确认条件根据内容来匹配对应的字段,没有原文依据的分类保持空数组"


def build_candidate_request(text: str) -> ModelRequest:
    model_request = build_request(text)
    instructions_new =  model_request.instructions + CANDIDATE_RULES
    model_request_new = ModelRequest(instructions_new,model_request.input)
    return model_request_new
