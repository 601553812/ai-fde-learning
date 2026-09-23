"""Learner boundary test: a connect timeout is still a timeout."""

import httpx
from Week4.day23.code.call_service import CallResult, call_once
from Week4.day23.code.prompt import build_request
from Week4.day23.tests.test_call_service import FakeGateway


def test_connect_timeout_is_not_generic_network_error():
    request = build_request("CSV")
    gateway = FakeGateway(request)
    gateway.error = httpx.ConnectTimeout("offline timeout")
    result = call_once(gateway=gateway,request=request)
    assert result == CallResult(False, None, "timeout", None)
    assert gateway.calls == [request]
