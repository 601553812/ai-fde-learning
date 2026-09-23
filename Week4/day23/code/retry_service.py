"""Completed Day20 retry implementation copied for Day21 statistics."""

from dataclasses import dataclass
from collections.abc import Callable

from .call_service import CallResult, call_once
from .gemini_gateway import GeminiGateway
from .prompt import ModelRequest

WAIT_SECONDS = 0.2  # Offline teaching interval, not a production retry policy.


@dataclass
class RetryResult:
    result: CallResult
    attempts: int


def should_retry(result: CallResult) -> bool:
    if result.ok == False and result.status_code == 503:
        return True
    return False


def call_with_retry(
    gateway: GeminiGateway,
    request: ModelRequest,
    *,
    max_attempts: int = 3,
    sleeper: Callable[[float], None],
) -> RetryResult:
    if max_attempts not in [1,2,3] or type(max_attempts) is not int:
        raise ValueError("max_attempts must be an integer between 1 and 3")
    for attempt in range(1,max_attempts+1):
        result = call_once(gateway, request)
        if should_retry(result) and attempt < max_attempts:
            sleeper(WAIT_SECONDS)
        else:
            retry_result = RetryResult(result, attempt)
            return retry_result
    retry_result = RetryResult(result, attempt)
    return retry_result
