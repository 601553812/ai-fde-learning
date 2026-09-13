"""Run decoder tests first; one final recovery case belongs to the student."""

import json

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from Week1.day06 import RequirementData
from day11.service import AnalyzerUnavailable, RuleBasedAnalyzer
from day13.settings import ENV_NAME
from day14.app import app
from day14.model_client import FixedModelClient, LocalModelClient, ModelClient
from day14.service import (
    MODEL_OUTPUT_ERROR_MESSAGE,
    InvalidModelOutput,
    ModelOutputAnalyzer,
    decode_requirements,
    get_analyzer,
)

client = TestClient(app)
ENDPOINT = "/analyze-requirement"
INPUT_A = "機能: CSV出力\n受入条件: 3秒以内"
INPUT_B = "機能: 検索\n受入条件: 1秒以内"
MODEL_DATA = {
    "functions": ["モデル側の固定結果"],
    "acceptance_criteria": ["モデル側の条件"],
    "risks": ["文字化け"],
    "questions": [],
    "unknown": [],
}
MODEL_JSON = json.dumps(MODEL_DATA, ensure_ascii=False)
EXPECTED_OUTPUT = {
    "schema_version": "1.0", "requirements": MODEL_DATA, "validation_errors": [],
}
MODEL_ERROR_BODY = {
    "detail": {"code": "MODEL_OUTPUT_INVALID", "message": "Model returned invalid output"}
}


def test_local_client_is_only_a_rule_based_simulation():
    raw = LocalModelClient().generate(INPUT_A)
    assert isinstance(raw, str)
    assert json.loads(raw) == RuleBasedAnalyzer().analyze(INPUT_A).requirements.model_dump()


def test_fixed_client_records_both_inputs():
    fake = FixedModelClient(MODEL_JSON)
    assert fake.generate(INPUT_A) == MODEL_JSON
    assert fake.generate(INPUT_B) == MODEL_JSON
    assert fake.calls == [INPUT_A, INPUT_B]


def test_decode_preserves_all_fields():
    result = decode_requirements(MODEL_JSON)
    assert isinstance(result, RequirementData)
    assert result.model_dump() == MODEL_DATA


def test_decode_keeps_existing_empty_defaults():
    result = decode_requirements('{}')
    assert result.model_dump() == {
        "functions": [], "acceptance_criteria": [], "risks": [], "questions": [], "unknown": [],
    }


def test_invalid_json_keeps_validation_error_as_cause():
    raw = 'not-json-with-private-marker'
    with pytest.raises(InvalidModelOutput) as captured:
        decode_requirements(raw)
    assert str(captured.value) == MODEL_OUTPUT_ERROR_MESSAGE
    assert raw not in str(captured.value)
    assert isinstance(captured.value.__cause__, ValidationError)


def test_wrong_structure_and_extra_fields_are_rejected():
    for raw in ['[]', 'null', '{"functions":"CSV出力"}', '{"functions":[123]}',
                '{"functions":null}', '{"validation_errors":[]}',
                '```json\n{}\n```']:
        with pytest.raises(InvalidModelOutput) as captured:
            decode_requirements(raw)
        assert str(captured.value) == MODEL_OUTPUT_ERROR_MESSAGE
        assert isinstance(captured.value.__cause__, ValidationError)


def test_analyzer_uses_model_text_instead_of_reparsing_input():
    fake = FixedModelClient(MODEL_JSON)
    output = ModelOutputAnalyzer(fake).analyze(INPUT_A)
    assert output.model_dump() == EXPECTED_OUTPUT
    assert fake.calls == [INPUT_A]


def test_empty_model_fields_are_business_errors():
    fake = FixedModelClient('{}')
    output = ModelOutputAnalyzer(fake).analyze(INPUT_A)
    assert output.requirements == RequirementData()
    assert output.validation_errors == [
        "At least one function is required", "At least one acceptance criterion is required",
    ]
    assert fake.calls == [INPUT_A]


def test_default_api_preserves_day13_behavior(monkeypatch):
    monkeypatch.delenv(ENV_NAME, raising=False)
    assert client.get('/health').json() == {"status": "ok"}
    result = client.post(ENDPOINT, json={"text": INPUT_A})
    assert result.status_code == 200
    assert result.json() == RuleBasedAnalyzer().analyze(INPUT_A).model_dump()
    assert client.post(ENDPOINT, json={"text": "機能: CSV出力"}).status_code == 200
    strict = client.post(ENDPOINT, params={"strict": "true"}, json={"text": "機能: CSV出力"})
    assert strict.status_code == 400
    assert strict.json() == {"detail": {
        "code": "REQUIREMENT_INCOMPLETE", "errors": ["At least one acceptance criterion is required"],
    }}


def test_route_maps_only_model_output_error_to_502(monkeypatch):
    monkeypatch.delenv(ENV_NAME, raising=False)

    class BrokenAnalyzer(RuleBasedAnalyzer):
        def analyze(self, text):
            raise InvalidModelOutput('private-model-fragment')

    def provide_broken_analyzer():
        return BrokenAnalyzer()

    monkeypatch.setitem(app.dependency_overrides, get_analyzer, provide_broken_analyzer)
    response = client.post(ENDPOINT, json={"text": INPUT_A})
    assert response.status_code == 502
    assert response.json() == MODEL_ERROR_BODY
    assert 'private-model-fragment' not in response.text


def test_model_business_errors_follow_strict_query(monkeypatch):
    monkeypatch.delenv(ENV_NAME, raising=False)
    fake = FixedModelClient('{}')

    def provide_model_analyzer():
        return ModelOutputAnalyzer(fake)

    monkeypatch.setitem(app.dependency_overrides, get_analyzer, provide_model_analyzer)
    draft = client.post(ENDPOINT, json={"text": INPUT_A})
    assert draft.status_code == 200
    assert draft.json()['validation_errors'] == [
        "At least one function is required", "At least one acceptance criterion is required",
    ]
    strict = client.post(ENDPOINT, params={"strict": "true"}, json={"text": INPUT_A})
    assert strict.status_code == 400
    assert strict.json() == {"detail": {"code": "REQUIREMENT_INCOMPLETE", "errors": draft.json()['validation_errors']}}
    assert fake.calls == [INPUT_A, INPUT_A]


def test_length_and_bad_configuration_prevent_generation(monkeypatch):
    fake = FixedModelClient(MODEL_JSON)

    def provide_model_analyzer():
        return ModelOutputAnalyzer(fake)

    monkeypatch.setitem(app.dependency_overrides, get_analyzer, provide_model_analyzer)
    monkeypatch.setenv(ENV_NAME, '12')
    response = client.post(ENDPOINT, json={"text": 'あ' * 13})
    assert response.status_code == 413
    assert response.json() == {"detail": {"code": "TEXT_TOO_LONG", "max_length": 12, "actual_length": 13}}
    monkeypatch.setenv(ENV_NAME, 'bad')
    response = client.post(ENDPOINT, json={"text": INPUT_A})
    assert response.status_code == 503
    assert response.json() == {"detail": {"code": "CONFIGURATION_INVALID", "message": "Server configuration is invalid"}}
    assert fake.calls == []


def test_invalid_request_stays_422_without_generation(monkeypatch):
    monkeypatch.delenv(ENV_NAME, raising=False)
    fake = FixedModelClient(MODEL_JSON)

    def provide_model_analyzer():
        return ModelOutputAnalyzer(fake)

    monkeypatch.setitem(app.dependency_overrides, get_analyzer, provide_model_analyzer)
    assert client.post(ENDPOINT, json={"text": 123}).status_code == 422
    assert client.post(ENDPOINT, params={"strict": "banana"}, json={"text": INPUT_A}).status_code == 422
    assert fake.calls == []


def test_unavailable_client_keeps_existing_503(monkeypatch):
    monkeypatch.delenv(ENV_NAME, raising=False)

    class UnavailableClient(ModelClient):
        def generate(self, text):
            raise AnalyzerUnavailable('simulated connection failure')

    def provide_unavailable_analyzer():
        return ModelOutputAnalyzer(UnavailableClient())

    monkeypatch.setitem(app.dependency_overrides, get_analyzer, provide_unavailable_analyzer)
    response = client.post(ENDPOINT, json={"text": INPUT_A})
    assert response.status_code == 503
    assert response.json() == {"detail": {"code": "ANALYZER_UNAVAILABLE", "message": "Analysis service is temporarily unavailable"}}


def test_programming_error_is_not_hidden_as_502(monkeypatch):
    monkeypatch.delenv(ENV_NAME, raising=False)

    class BuggyClient(ModelClient):
        def generate(self, text):
            raise TypeError('simulated programming mistake')

    def provide_buggy_analyzer():
        return ModelOutputAnalyzer(BuggyClient())

    monkeypatch.setitem(app.dependency_overrides, get_analyzer, provide_buggy_analyzer)
    with pytest.raises(TypeError, match='simulated programming mistake'):
        client.post(ENDPOINT, json={"text": INPUT_A})


def test_invalid_model_output_then_success_keeps_both_calls(monkeypatch):
    monkeypatch.delenv(ENV_NAME, raising=False)
    fake = FixedModelClient("not-json")
    def provide_model_analyzer():
        return ModelOutputAnalyzer(fake)
    monkeypatch.setitem(app.dependency_overrides, get_analyzer, provide_model_analyzer)
    response = client.post(ENDPOINT, json={"text": INPUT_A})
    assert response.status_code == 502
    assert response.json() == MODEL_ERROR_BODY
    assert fake.calls == [INPUT_A]
    fake.raw = MODEL_JSON
    response = client.post(ENDPOINT, json={"text": INPUT_B})
    assert response.status_code == 200
    assert response.json() == EXPECTED_OUTPUT
    assert fake.calls == [INPUT_A,INPUT_B]
