"""Fetch requirement data from a JSON HTTP API."""

from __future__ import annotations

import requests
from pydantic import ValidationError

from day06.models import RequirementData


# TODO 1: 将父类改为 RuntimeError。
class RequirementApiError(Exception):
    """Public error raised when remote requirement data cannot be loaded."""


def fetch_requirement(
    url: str,
    timeout_seconds: float = 5.0,
) -> RequirementData:
    """Fetch, decode, and validate requirement data from an HTTP endpoint."""
    # TODO 2: 使用 requests.get() 请求 URL，并显式传入 timeout_seconds。
    # TODO 3: 检查 HTTP 状态、解析 JSON、校验 Schema，并统一转换异常。
    raise NotImplementedError("TODO 2-3: implement fetch_requirement")
