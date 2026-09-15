"""Provided local observation script; run after the TODOs, no external calls."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from Week2.day13.settings import ENV_NAME
from Week2.day14.app import app
from Week2.day14.model_client import FixedModelClient
from Week2.day14.service import ModelOutputAnalyzer, get_analyzer


def main() -> None:
    # patch.dict restores the environment and overrides even if an assertion fails.
    # Provided demonstration plumbing; no new mocking API is required for the task.
    import os

    input_a = "機能: CSV出力\n受入条件: 3秒以内"
    input_b = "機能: 検索\n受入条件: 1秒以内"
    fake = FixedModelClient('not-json')

    def provide_demo_analyzer():
        return ModelOutputAnalyzer(fake)

    with patch.dict(os.environ, {ENV_NAME: '2000'}):
        with patch.dict(app.dependency_overrides, {get_analyzer: provide_demo_analyzer}):
            with TestClient(app) as client:
                first = client.post('/analyze-requirement', json={"text": input_a})
                print('First response:', first.status_code, first.json())
                print('Calls after first:', fake.calls)
                assert first.status_code == 502, 'TODOs: first model output must be rejected'
                assert first.json() == {"detail": {"code": "MODEL_OUTPUT_INVALID", "message": "Model returned invalid output"}}
                assert fake.calls == [input_a]
                fake.raw = '{"functions":["検索結果"],"acceptance_criteria":["1秒以内"]}'
                second = client.post('/analyze-requirement', json={"text": input_b})
                print('Second response:', second.status_code, second.json())
                print('Calls after second:', fake.calls)
                assert second.status_code == 200
                assert second.json() == {
                    "schema_version": "1.0",
                    "requirements": {"functions": ["検索結果"], "acceptance_criteria": ["1秒以内"],
                                     "risks": [], "questions": [], "unknown": []},
                    "validation_errors": [],
                }
                assert fake.calls == [input_a, input_b]


if __name__ == '__main__':
    main()
