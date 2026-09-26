"""Provided requirements checks. All calls and waits are local doubles."""

import httpx
import pytest

from Week4.day26.code.call_service import CallResult
from Week4.day26.code.fakes import RecordingSleeper, SequenceGateway, status_error
from Week4.day26.code.prompt import build_request
from Week4.day26.code.retry_service import RetryResult, call_with_retry, should_retry


@pytest.mark.parametrize("result,expected", [
    (CallResult(True, "not-json", None, None), False),
    (CallResult(False, None, "service_unavailable", 503), True),
    (CallResult(False, None, "rate_limited", 429), False),
    (CallResult(False, None, "auth_error", 403), False),
    (CallResult(False, None, "timeout", None), False),
    (CallResult(False, None, "network_error", None), False),
    (CallResult(False, None, "api_error", 500), False),
])
def test_retry_policy(result, expected):
    assert should_retry(result) is expected


def test_success_stops_without_sleep_even_for_invalid_json():
    request = build_request("注文一覧")
    gateway = SequenceGateway(["not-json", "must not reach"])
    sleep = RecordingSleeper(gateway.events)
    actual = call_with_retry(gateway, request, sleeper=sleep)
    assert actual == RetryResult(CallResult(True, "not-json", None, None), 1)
    assert gateway.calls == [request]
    assert sleep.calls == []
    assert gateway.events == ["call"]


def test_503_then_success_preserves_raw_and_stops():
    request = build_request('  日本語\n"引用"  ')
    raw = '  {"functions":["CSV出力"]}  '
    gateway = SequenceGateway([status_error(503), raw, "must not reach"])
    sleep = RecordingSleeper(gateway.events)
    actual = call_with_retry(gateway, request, sleeper=sleep)
    assert actual == RetryResult(CallResult(True, raw, None, None), 2)
    assert gateway.calls == [request, request]
    assert all(item is request for item in gateway.calls)
    assert sleep.calls == [0.2]
    assert gateway.events == ["call", "sleep", "call"]


@pytest.mark.parametrize("limit", [1, 2, 3])
def test_exhausted_budget_returns_last_failure_without_extra_sleep(limit):
    request = build_request("CSV")
    gateway = SequenceGateway([status_error(503)] * 3)
    sleep = RecordingSleeper(gateway.events)
    actual = call_with_retry(gateway, request, max_attempts=limit, sleeper=sleep)
    assert actual == RetryResult(CallResult(False, None, "service_unavailable", 503), limit)
    assert gateway.calls == [request] * limit
    assert sleep.calls == [0.2] * (limit - 1)
    assert gateway.events == ["call"] + ["sleep", "call"] * (limit - 1)


@pytest.mark.parametrize("error,kind,code", [
    (status_error(429), "rate_limited", 429),
    (status_error(401), "auth_error", 401),
    (httpx.ReadTimeout("private mock detail"), "timeout", None),
    (httpx.ConnectError("private mock detail"), "network_error", None),
])
def test_non_retryable_failure_returns_immediately(error, kind, code):
    request = build_request("CSV")
    gateway = SequenceGateway([error, "must not reach"])
    sleep = RecordingSleeper()
    assert call_with_retry(gateway, request, sleeper=sleep) == RetryResult(
        CallResult(False, None, kind, code), 1)
    assert gateway.calls == [request]
    assert sleep.calls == []


@pytest.mark.parametrize("limit", [0, 4, True, 2.5])
def test_invalid_budget_fails_before_call_or_sleep(limit):
    gateway = SequenceGateway(["unused"])
    sleep = RecordingSleeper()
    with pytest.raises(ValueError, match="max_attempts"):
        call_with_retry(gateway, build_request("CSV"), max_attempts=limit, sleeper=sleep)
    assert gateway.calls == []
    assert sleep.calls == []


def test_programming_error_propagates_without_retry():
    request = build_request("CSV")
    gateway = SequenceGateway([ValueError("programming error")])
    sleep = RecordingSleeper()
    with pytest.raises(ValueError, match="programming error"):
        call_with_retry(gateway, request, sleeper=sleep)
    assert gateway.calls == [request]
    assert sleep.calls == []
