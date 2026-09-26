"""TODO 3: a retry encounters a different, non-retryable failure."""
from time import sleep

from Week4.day26.code.call_service import CallResult
from Week4.day26.code.fakes import RecordingSleeper, SequenceGateway, status_error
from Week4.day26.code.prompt import build_request
from Week4.day26.code.retry_service import RetryResult, call_with_retry


def test_503_then_403_stops_and_returns_latest_failure():
    request = build_request("CSV")
    gateway = SequenceGateway([status_error(503), status_error(403), "must not reach"])
    sleep = RecordingSleeper()
    result = call_with_retry(gateway, request, max_attempts=3, sleeper=sleep)
    assert result == RetryResult(CallResult(False, None, "auth_error", 403), 2)
    assert gateway.calls == [request, request]
    assert sleep.calls == [0.2]
