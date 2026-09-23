"""TODO 2: two separate summaries must not share accumulated counts."""

from ..code.call_service import CallResult
from ..code.retry_service import RetryResult
from ..code.summary import summarize


def test_second_summary_starts_from_zero():
    first = summarize([RetryResult(CallResult(False, None, "service_unavailable", 503), 3)])
    assert first == {"requests": 1, "succeeded": 0, "failed": 1, "attempts": 3, "retries": 2}
    second = summarize([RetryResult(CallResult(True, "not-json", None, None), 1)])
    assert second == {"requests": 1, "succeeded": 1, "failed": 0, "attempts": 1, "retries": 0}
    assert first == {"requests": 1, "succeeded": 0, "failed": 1, "attempts": 3, "retries": 2}
