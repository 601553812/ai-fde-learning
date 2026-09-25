"""Tests for learner code; no network or sleep."""

import httpx
import pytest
from Week4.day25.code.call_service import CallResult, call_once, classify_status
from Week4.day25.code.prompt import build_request
from Week4.day25.code.scenarios import RAW


class FakeGateway:
    def __init__(self, response=RAW, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def complete(self, request):
        self.calls.append(request)
        if self.error is not None:
            raise self.error
        return self.response


def status_error(code):
    request = httpx.Request("POST", "https://example.invalid/model")
    response = httpx.Response(code, request=request)
    return httpx.HTTPStatusError("private mock detail: never expose", request=request, response=response)


@pytest.mark.parametrize("code,expected", [(401,"auth_error"),(403,"auth_error"),(429,"rate_limited"),(503,"service_unavailable"),(400,"api_error"),(500,"api_error")])
def test_status_mapping(code, expected):
    assert classify_status(code) == expected


def test_success_preserves_raw_and_calls_once():
    gateway = FakeGateway(response="not-json")
    request = build_request("CSV")
    assert call_once(gateway, request) == CallResult(True, "not-json", None, None)
    assert gateway.calls == [request]


@pytest.mark.parametrize("error,kind,code", [
    (httpx.ReadTimeout("private mock detail"),"timeout",None),
    (httpx.ConnectError("private mock detail"),"network_error",None),
    (status_error(503),"service_unavailable",503),
    (status_error(429),"rate_limited",429),
    (status_error(403),"auth_error",403),
    (status_error(400),"api_error",400),
])
def test_expected_failure_becomes_result_without_retry(error, kind, code):
    gateway = FakeGateway(error=error)
    request = build_request("CSV")
    assert call_once(gateway, request) == CallResult(False, None, kind, code)
    assert gateway.calls == [request]


def test_programming_error_is_not_misreported_as_network_failure():
    with pytest.raises(ValueError, match="programming error"):
        call_once(FakeGateway(error=ValueError("programming error")), build_request("CSV"))
