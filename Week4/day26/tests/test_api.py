"""Provided HTTP contracts. All gateways are local recording doubles."""

from copy import deepcopy
from dataclasses import asdict
import json

import pytest
from fastapi.testclient import TestClient

from ..code.app import app, make_response
from ..code.batch import TaskReport
from ..code.batch_fakes import RecordingFactory
from ..code.call_service import CallResult
from ..code.fakes import RecordingSleeper, status_error
from ..code.retry_service import RetryResult
from ..code.runtime import BatchRuntime, get_runtime


@pytest.fixture
def setup_api():
    factory = RecordingFactory({"A": ["日本語"], "B": [status_error(403)],
                                "C": [status_error(503), "回復"]})
    sleeper = RecordingSleeper()
    app.dependency_overrides[get_runtime] = lambda: BatchRuntime(factory, sleeper)
    try:
        with TestClient(app) as client:
            yield client, factory, sleeper
    finally:
        app.dependency_overrides.clear()


def mixed_body():
    return {"tasks": [{"task_id": key, "text": "  CSV出力\n"} for key in "ABC"]}


def test_make_response_preserves_details_without_mutation():
    rows = [TaskReport("Z", RetryResult(CallResult(False, None, "timeout", None), 1))]
    before = deepcopy(rows)
    body = make_response(rows)
    assert body == {"mode": "simulated", "tasks": [asdict(rows[0])],
                    "summary": dict(requests=1, succeeded=0, failed=1, attempts=1, retries=0)}
    assert rows == before
    assert json.loads(json.dumps(body)) == body


def test_make_response_empty_and_previous_result_are_independent():
    first = make_response([TaskReport("X", RetryResult(CallResult(True, "ok", None, None), 1))])
    saved = deepcopy(first)
    assert make_response([]) == {"mode": "simulated", "tasks": [], "summary":
                               dict(requests=0, succeeded=0, failed=0, attempts=0, retries=0)}
    assert first == saved


def test_mixed_batch_http_200_keeps_failed_row(setup_api):
    client, factory, sleeper = setup_api
    response = client.post("/analyze-batch", json=mixed_body())
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "simulated"
    assert body["summary"] == dict(requests=3, succeeded=2, failed=1, attempts=4, retries=1)
    assert [row["task_id"] for row in body["tasks"]] == list("ABC")
    assert body["tasks"][1]["report"] == {
        "result": {"ok": False, "raw": None, "error": "auth_error", "status_code": 403}, "attempts": 1}
    assert body["tasks"][2]["report"]["result"]["raw"] == "回復"
    assert factory.calls == list("ABC")
    assert sleeper.calls == [0.2]
    assert json.loads(factory.gateways["A"].calls[0].input) == {"document": "  CSV出力\n"}


def test_http_attempt_limit_reaches_service(setup_api):
    client, factory, sleeper = setup_api
    body = mixed_body()
    body["max_attempts"] = 1
    response = client.post("/analyze-batch", json=body)
    assert response.status_code == 200
    assert response.json()["summary"] == dict(requests=3, succeeded=1, failed=2, attempts=3, retries=0)
    assert len(factory.gateways["C"].calls) == 1
    assert sleeper.calls == []


def test_empty_http_batch_has_no_calls(setup_api):
    client, factory, sleeper = setup_api
    response = client.post("/analyze-batch", json={"tasks": []})
    assert response.status_code == 200
    assert response.json() == {"mode": "simulated", "tasks": [], "summary":
                               dict(requests=0, succeeded=0, failed=0, attempts=0, retries=0)}
    assert factory.calls == sleeper.calls == []


@pytest.mark.parametrize("body", [
    {}, {"tasks": [{"task_id": "", "text": "x"}]},
    {"tasks": [{"task_id": "A", "text": ""}]},
    {"tasks": [{"task_id": "A", "text": "x" * 2001}]},
    {"tasks": [{"task_id": str(i), "text": "x"} for i in range(11)]},
    {"tasks": [], "max_attempts": 0}, {"tasks": [], "max_attempts": 4},
    {"tasks": [], "max_attempts": True}, {"tasks": [], "max_attempts": "1"},
])
def test_invalid_body_is_422_before_gateway_calls(setup_api, body):
    client, factory, sleeper = setup_api
    response = client.post("/analyze-batch", json=body)
    assert response.status_code == 422
    assert isinstance(response.json()["detail"], list)
    assert factory.calls == sleeper.calls == []
    assert all(gateway.calls == [] for gateway in factory.gateways.values())


def test_gateway_value_error_is_not_mislabeled_as_duplicate(setup_api):
    client, factory, sleeper = setup_api
    factory.gateways["A"].outcomes = [ValueError("internal test bug")]
    with pytest.raises(ValueError, match="^internal test bug$"):
        client.post("/analyze-batch", json={"tasks": [{"task_id": "A", "text": "x"}]})


def test_default_runtime_is_fresh_for_two_requests():
    with TestClient(app) as client:
        for _ in range(2):
            response = client.post("/analyze-batch", json={"tasks": [{"task_id": "A", "text": "日本語"}]})
            assert response.status_code == 200
            assert response.json()["tasks"][0]["report"]["result"]["raw"] == "模擬結果：A"
            assert response.json()["summary"]["attempts"] == 1
