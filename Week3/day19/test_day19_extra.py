"""Learner boundary test: a connect timeout is still a timeout."""

import httpx
from Week3.day19.call_service import CallResult, call_once
from Week3.day19.prompt import build_request
from Week3.day19.test_day19 import FakeGateway


def test_connect_timeout_is_not_generic_network_error():
    request = build_request("CSV")
    gateway = FakeGateway(request)
    gateway.error = httpx.ConnectTimeout("offline timeout")
    result = call_once(gateway=gateway,request=request)
    assert result == CallResult(False, None, "timeout", None)
    assert gateway.calls == [request]
