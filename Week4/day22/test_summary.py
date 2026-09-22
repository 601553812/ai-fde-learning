"""Provided contract checks; synthetic reports are not real model evidence."""

from copy import deepcopy

from .call_service import CallResult
from .retry_service import RetryResult
from .summary import summarize


def test_empty_reports():
    assert summarize([]) == dict(requests=0, succeeded=0, failed=0, attempts=0, retries=0)


def test_mixed_reports_count_final_outcomes():
    reports = [RetryResult(CallResult(True, "ok", None, None), 1),
               RetryResult(CallResult(True, "recovered", None, None), 2),
               RetryResult(CallResult(False, None, "auth_error", 403), 2)]
    assert summarize(reports) == dict(requests=3, succeeded=2, failed=1, attempts=5, retries=2)


def test_normal_return_is_not_content_validation():
    reports = [RetryResult(CallResult(True, "not-json", None, None), 3)]
    assert summarize(reports) == dict(requests=1, succeeded=1, failed=0, attempts=3, retries=2)


def test_all_failed_with_different_attempt_counts():
    reports = [RetryResult(CallResult(False, None, "timeout", None), 1),
               RetryResult(CallResult(False, None, "service_unavailable", 503), 3)]
    assert summarize(reports) == dict(requests=2, succeeded=0, failed=2, attempts=4, retries=2)


def test_input_is_preserved():
    reports = [RetryResult(CallResult(True, "  日本語  ", None, None), 2)]
    before = deepcopy(reports)
    result = summarize(reports)
    assert result == dict(requests=1, succeeded=1, failed=0, attempts=2, retries=1)
    assert reports == before
