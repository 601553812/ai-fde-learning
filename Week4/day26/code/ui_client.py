"""Prepare form input, call the local API, and validate its response."""

import httpx
from pydantic import ValidationError

from .response_models import BatchResponse


class DemoError(Exception):
    """A known input or connection problem that the page can display."""


def validate_report(body: object) -> dict:
    try:
        model = BatchResponse.model_validate(body)
    except ValidationError as exc:
        raise DemoError("接口返回结构不符合预期")
    if len(model.tasks) != model.summary.requests:
        raise DemoError("接口返回结构不符合预期")
    result_ok = 0
    result_fail = 0
    result_attempts_total = 0
    for task in model.tasks:
        if task.report.result.ok:
            result_ok += 1
        else:
            result_fail += 1
        result_attempts_total += task.report.attempts
    if (result_ok != model.summary.succeeded or
            result_fail != model.summary.failed or
            result_attempts_total != model.summary.attempts or
            model.summary.retries != result_attempts_total - len(model.tasks)):
        raise DemoError("接口返回结构不符合预期")
    return model.model_dump()



def build_payload(text_a: str, text_b: str, max_attempts: int) -> dict:
    a = text_a.strip()
    b = text_b.strip()
    task_a = dict()
    tasks = []
    if not a:
        raise DemoError("需求 A 不能为空")
    task_a["task_id"] = "A"
    task_a["text"] = a
    tasks.append(task_a)
    if b:
        task_b = dict()
        task_b["task_id"] = "B"
        task_b["text"] = b
        tasks.append(task_b)
    if len(a) > 2000:
        raise DemoError("需求 A 不能超过 2000 字符")
    if len(b) > 2000:
        raise DemoError("需求 B 不能超过 2000 字符")
    result = dict()
    result["tasks"] = tasks
    result["max_attempts"] = max_attempts
    return result


def submit_batch(client: httpx.Client, payload: dict, mode: str = "simulated") -> dict:
    if mode not in ("simulated", "live"):
        raise ValueError("unknown mode")
    url = "/analyze-batch" if mode == "simulated" else "/analyze-batch?mode=live"
    timeout = 5.0 if mode == "simulated" else 45.0
    try:
        response = client.post(url, json=payload, timeout=timeout)
        status_code = response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise DemoError(f"接口请求失败（HTTP {exc.response.status_code}）")
    except httpx.RequestError as request_exc:
        raise DemoError("无法连接接口或请求超时，请检查本地 API 服务")
    try:
        json = response.json()
    except ValueError as value_exc:
        raise DemoError("接口未返回合法 JSON")
    return validate_report(json)
