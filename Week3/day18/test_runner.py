"""Provided harness checks. Fake outputs verify wiring, never prompt quality."""

import json

import pytest

from Week3.day15.prompt import ModelRequest, build_request
from Week3.day18 import run_compare


@pytest.mark.parametrize("candidate_passed,expected_exit", [(True, 0), (False, 1)])
def test_live_wiring_with_fake_gateway(monkeypatch, capsys, candidate_passed, expected_exit):
    case = run_compare.load_cases()["D"]
    good = json.dumps({"functions": ["注文一覧 CSV"], "acceptance_criteria": [], "risks": [],
                       "questions": ["3秒以内にするか確認"], "unknown": []})
    calls = []

    def candidate(text):
        base = build_request(text)
        return ModelRequest(base.instructions + "\nfixture-only rule", base.input)

    class FakeGateway:
        def __init__(self, model):
            assert model == run_compare.DEFAULT_MODEL

        def complete(self, request):
            calls.append(request)
            return good if candidate_passed and len(calls) == 2 else case["raw"]

    monkeypatch.setattr(run_compare, "build_candidate_request", candidate)
    monkeypatch.setattr(run_compare, "classify_change", lambda before, after: "fixture_label")
    monkeypatch.setattr(run_compare, "GeminiGateway", FakeGateway)
    monkeypatch.setattr("sys.argv", ["run_compare", "--case", "D", "--live"])
    assert run_compare.main() == expected_exit
    output = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert len(calls) == 2
    assert calls[0].input == calls[1].input
    assert calls[0].instructions != calls[1].instructions
    assert output[1]["evaluation"]["content_passed"] is False
    assert output[2]["evaluation"]["content_passed"] is candidate_passed
    assert output[3]["change"] == "fixture_label"
