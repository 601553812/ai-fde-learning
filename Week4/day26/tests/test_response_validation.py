"""Day26 contracts for the HTTP 200 response boundary; no real network."""

from copy import deepcopy

import pytest
from pydantic import ValidationError

from ..code.response_models import BatchResponse
from ..code.ui_client import DemoError, submit_batch, validate_report
from .test_ui_client import RecordingClient, response


def valid_body():
    return {
        "mode": "simulated",
        "tasks": [
            {"task_id": "A", "report": {"result": {
                "ok": True, "raw": "模擬結果：A", "error": None, "status_code": None},
                "attempts": 1}},
            {"task_id": "B", "report": {"result": {
                "ok": False, "raw": None, "error": "auth_error", "status_code": 403},
                "attempts": 1}},
        ],
        "summary": {"requests": 2, "succeeded": 1, "failed": 1,
                    "attempts": 2, "retries": 0},
    }


def test_schema_accepts_complete_nested_report_and_keeps_data():
    body = valid_body()
    saved = deepcopy(body)
    assert BatchResponse.model_validate(body).model_dump() == body
    assert body == saved


@pytest.mark.parametrize("change", [
    lambda body: body["tasks"][0]["report"]["result"].pop("ok"),
    lambda body: body["summary"].pop("failed"),
    lambda body: body["tasks"][0]["report"].pop("attempts"),
])
def test_schema_rejects_missing_nested_fields(change):
    body = valid_body()
    change(body)
    with pytest.raises(ValidationError):
        BatchResponse.model_validate(body)


@pytest.mark.parametrize("change", [
    lambda body: body["tasks"][0]["report"]["result"].update(ok="true"),
    lambda body: body["summary"].update(requests="2"),
    lambda body: body["tasks"][1]["report"].update(attempts=0),
    lambda body: body["summary"].update(retries=-1),
    lambda body: body.update(mode="other"),
    lambda body: body["summary"].update(secret="not part of the contract"),
])
def test_schema_rejects_wrong_values_and_unknown_fields(change):
    body = valid_body()
    change(body)
    with pytest.raises(ValidationError):
        BatchResponse.model_validate(body)


def test_validator_returns_complete_report_without_mutation():
    body = valid_body()
    saved = deepcopy(body)
    assert validate_report(body) == body
    assert body == saved


@pytest.mark.parametrize("body", [None, [], {"mode": "simulated"}])
def test_validator_maps_invalid_structure_to_safe_message(body):
    with pytest.raises(DemoError, match="^接口返回结构不符合预期$"):
        validate_report(body)


def test_http_200_invalid_structure_is_page_error_after_one_post():
    payload = {"tasks": [], "max_attempts": 1}
    client = RecordingClient(response(body={"mode": "simulated", "tasks": []}))
    with pytest.raises(DemoError, match="^接口返回结构不符合预期$"):
        submit_batch(client, payload)
    assert client.calls == [("/analyze-batch", payload, 5.0)]


@pytest.mark.parametrize("change", [
    lambda body: body["summary"].update(requests=3),
    lambda body: body["summary"].update(succeeded=2, failed=0),
    lambda body: body["summary"].update(failed=0),
    lambda body: body["summary"].update(attempts=3),
    lambda body: body["summary"].update(retries=1),
])
def test_validator_rejects_totals_inconsistent_with_rows(change):
    body = valid_body()
    change(body)
    with pytest.raises(DemoError, match="^接口返回结构不符合预期$"):
        validate_report(body)
