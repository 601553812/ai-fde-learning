"""TODO 3: verify duplicate IDs at the HTTP boundary before any calls."""

from fastapi.testclient import TestClient

from ..code.app import app
from ..code.batch_fakes import RecordingFactory
from ..code.fakes import RecordingSleeper
from ..code.runtime import BatchRuntime, get_runtime


def test_duplicate_http_request_has_no_calls():
    factory = RecordingFactory({"A": ["ok"], "B": ["ok"]})
    sleeper = RecordingSleeper()
    app.dependency_overrides[get_runtime] = lambda: BatchRuntime(factory, sleeper)
    try:
        with TestClient(app) as client:
            response = client.post("/analyze-batch", json={"tasks": [{"task_id": "A", "text": "one"},{"task_id": "B", "text": "two"},{"task_id": "A", "text": "three"} ]})
        assert response.status_code == 422
        assert response.json() == {"detail":{"code":"DUPLICATE_TASK_ID","message":"duplicate task_id"}}
        assert factory.calls == []
        assert factory.gateways["A"].calls == []
        assert factory.gateways["B"].calls == []
        assert sleeper.calls == []
    finally:
        app.dependency_overrides.clear()
