"""Day26 HTTP 适配器的当前日版本；本日请求仍是普通日文问答。"""

import os

import httpx

from .qa_prompt import ModelRequest

DEFAULT_MODEL = "gemini-3.8-flash"
ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/interactions"
TIMEOUT_SECONDS = 30.0


def build_gemini_payload(request: ModelRequest, model: str) -> dict:
    # 内部对象的两个字符串原样放入 HTTP 字典；输入不再做第二次 JSON 编码。
    result = {"model": model,"system_instruction":request.instructions,"input":request.input,"store":False}
    return result


def extract_answer(data: dict) -> str:
    # 这是供应商响应的状态；未完成时不能把部分文字当成最终回答。
    if data.get("status") != "completed":
        raise ValueError("model_not_completed")
    steps: list[dict] = data.get("steps",[])
    # 倒序检查副本，寻找最后一个 model_output，不改变原 steps 列表。
    steps_copy = steps.copy()
    steps_copy.reverse()
    for step in steps_copy:
        type = step.get("type")
        if type == "model_output":
            # contents 是片段列表；循环中的每个 content 才是片段字典。
            contents = step.get("content",[])
            if contents:
                result = ""
                for content in contents:
                    # 只拼接 text 类型；其他类型即使有 text 字段也不使用。
                    if content.get("type") == "text":
                        text = content.get("text")
                        if text:
                            result = result + text
                # 所有片段拼完后才检查空白；返回时保留原首尾空白。
                if result.strip()=="":
                    raise ValueError("missing_model_text")
                if result:
                    return result
            else:
                # 最后的 model_output 为空就报错，不回退到更早的输出。
                raise ValueError("missing_model_text")
    raise ValueError("missing_model_text")



class GeminiGateway:
    """提供 complete(request) 方法，与 RecordingGateway 接入同一调用点。"""

    def __init__(self, model=DEFAULT_MODEL, *, api_key=None, transport=None):
        # 密钥只来自显式参数或当前进程环境；不读 .env，也不打印值。
        keys = [api_key, os.getenv("GOOGLE_API_KEY"), os.getenv("GEMINI_API_KEY")]
        key = next((value.strip() for value in keys if value and value.strip()), None)
        if key is None:
            raise ValueError("missing_api_key")
        if not model.strip():
            raise ValueError("invalid_model")
        self.model = model
        # 这里创建 HTTP 客户端，尚未发送请求；MockTransport 可完全隔离网络。
        self.client = httpx.Client(
            headers={"x-goog-api-key": key}, timeout=TIMEOUT_SECONDS,
            follow_redirects=False, transport=transport,
        )
        self.request_count = 0

    def complete(self, request: ModelRequest) -> str:
        payload = build_gemini_payload(request, self.model)
        # 计数表示本对象尝试发送的 POST 次数，不代表模型任务成功次数。
        self.request_count += 1
        response = self.client.post(ENDPOINT, json=payload)
        response.raise_for_status()  # 4xx/5xx 在解析模型文字前抛出 HTTPStatusError。
        try:
            data = response.json()
        except ValueError as exc:
            raise ValueError("invalid_model_response") from exc
        if not isinstance(data, dict):
            raise ValueError("invalid_model_response")
        return extract_answer(data)

    def close(self) -> None:
        # 用 finally 调用，确保成功和异常路径都释放连接。
        self.client.close()
