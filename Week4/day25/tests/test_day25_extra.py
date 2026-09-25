"""Learner-owned Day25 edge case: report totals must match task rows."""
from copy import deepcopy

import pytest

from Week4.day25.code.ui_client import validate_report, DemoError
from .test_response_validation import valid_body


def test_summary_mismatch_is_rejected_without_changing_input():
    body = valid_body()
    body["summary"]["requests"] = 3
    body_copy = deepcopy(body)
    with pytest.raises(DemoError, match="接口返回结构不符合预期"):
        validate_report(body_copy)
    assert body == body_copy
