"""Learner TODOs: classify HTTP status, then turn known failures into data."""

from dataclasses import dataclass
from unittest import case

import httpx
from httpx import TimeoutException, HTTPStatusError, RequestError

from .gemini_gateway import GeminiGateway
from .prompt import ModelRequest


@dataclass
class CallResult:
    ok: bool
    raw: str | None
    error: str | None
    status_code: int | None


def classify_status(status_code: int) -> str:
    match status_code:
        case 401 | 403:
            return "auth_error"
        case 429:
            return "rate_limited"
        case 503:
            return "service_unavailable"
        case _:
            return "api_error"


def call_once(gateway: GeminiGateway, request: ModelRequest) -> CallResult:
    try:
        raw = gateway.complete(request)
        return CallResult(ok=True, raw=raw, error=None, status_code=None)
    except TimeoutException:
        return CallResult(ok=False, raw=None, error="timeout", status_code=None)
    except HTTPStatusError as exc:
        return CallResult(ok=False, raw=None, error=classify_status(exc.response.status_code),
                          status_code=exc.response.status_code)
    except RequestError:
        return CallResult(ok=False, raw=None, error="network_error", status_code=None)
