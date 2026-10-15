"""Local version of Day15's gateway and recording-double contracts."""

from .qa_prompt import ModelRequest


class ModelGateway:
    """约定 complete(request) 方法；实际对象需要提供具体实现。"""

    def complete(self, request: ModelRequest) -> str:
        # 仅有基类时不能完成调用；子类覆盖此方法。
        raise NotImplementedError("A concrete gateway must implement complete")


class RecordingGateway(ModelGateway):
    """手写测试替身：记录请求、返回固定文字，不联网或推理。"""

    def __init__(self, raw: str):
        # raw 来自构造时传入的字符串，不是根据问题生成的答案。
        self.raw = raw
        # 每个实例有自己的列表；测试可检查调用次数和具体请求。
        self.calls: list[ModelRequest] = []

    def complete(self, request: ModelRequest) -> str:
        # 每调用一次追加一个请求对象，再原样返回固定文字。
        self.calls.append(request)
        return self.raw
