"""Day24 TODOs: prepare form input and call the local batch API."""

import httpx


class DemoError(Exception):
    """A known input or connection problem that the page can display."""


def build_payload(text_a: str, text_b: str, max_attempts: int) -> dict:
    a = text_a.strip()
    b = text_b.strip()
    task_a = dict()
    tasks = []
    if not a :
        raise DemoError("需求 A 不能为空")
    task_a["task_id"] = "A"
    task_a["text"] = a
    tasks.append(task_a)
    if b :
        task_b = dict()
        task_b["task_id"] = "B"
        task_b["text"] = b
        tasks.append(task_b)
    if len(a) > 2000 :
        raise DemoError("需求 A 不能超过 2000 字符")
    if len(b) > 2000 :
        raise DemoError("需求 B 不能超过 2000 字符")
    result = dict()
    result["tasks"] = tasks
    result["max_attempts"] = max_attempts
    return  result



def submit_batch(client: httpx.Client, payload: dict) -> dict:
    try:
        response = client.post("/analyze-batch", json=payload, timeout=5.0)
        status_code = response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise DemoError(f"接口请求失败（HTTP {exc.response.status_code}）")
    except httpx.RequestError as request_exc:
        raise DemoError("无法连接接口或请求超时，请检查本地 API 服务")
    try:
        json = response.json()
    except ValueError as value_exc:
        raise DemoError("接口未返回合法 JSON")
    return json
