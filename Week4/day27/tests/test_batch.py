"""Provided contracts. No real network calls or sleeping."""

from copy import deepcopy
import json
import pytest

from ..code.batch import Task, run_batch, validate_task_ids
from ..code.batch_fakes import RecordingFactory
from ..code.fakes import RecordingSleeper, status_error
from ..code.summary import summarize


def test_validate_distinct_ids():
    assert validate_task_ids([Task("A", "same"), Task("B", "same")]) is None


def test_validate_empty():
    assert validate_task_ids([]) is None


def test_validate_duplicate_ids():
    with pytest.raises(ValueError, match="^duplicate task_id$"):
        validate_task_ids([Task("A", "one"), Task("B", "two"), Task("A", "three")])


def test_failure_does_not_stop_later_tasks():
    tasks = [Task("A", "  CSV出力\n"), Task("B", "認証"), Task("C", "検索")]
    factory = RecordingFactory({"A": ["ok"], "B": [status_error(403)],
                                "C": [status_error(503), "recovered"]})
    sleeper = RecordingSleeper()
    rows = run_batch(tasks, factory, sleeper=sleeper)
    assert [row.task_id for row in rows] == ["A", "B", "C"]
    assert factory.calls == ["A", "B", "C"]
    assert [row.report.attempts for row in rows] == [1, 1, 2]
    assert [row.report.result.ok for row in rows] == [True, False, True]
    assert rows[1].report.result.error == "auth_error"
    assert rows[1].report.result.status_code == 403
    assert rows[2].report.result.raw == "recovered"
    assert sleeper.calls == [0.2]
    for task in tasks:
        assert all(json.loads(request.input) == {"document": task.text}
                   for request in factory.gateways[task.task_id].calls)
    assert summarize([row.report for row in rows]) == dict(
        requests=3, succeeded=2, failed=1, attempts=4, retries=1)


def test_nondefault_attempt_limit_applies_to_every_task():
    factory = RecordingFactory({"A": [status_error(503), "unused"],
                                "B": [status_error(503), "unused"]})
    sleeper = RecordingSleeper()
    rows = run_batch([Task("A", "a"), Task("B", "b")], factory,
                     max_attempts=1, sleeper=sleeper)
    assert [row.report.attempts for row in rows] == [1, 1]
    assert [row.report.result.status_code for row in rows] == [503, 503]
    assert [len(factory.gateways[key].calls) for key in ("A", "B")] == [1, 1]
    assert sleeper.calls == []


def test_empty_batch_has_no_calls():
    factory = RecordingFactory({})
    sleeper = RecordingSleeper()
    assert run_batch([], factory, sleeper=sleeper) == []
    assert factory.calls == sleeper.calls == []


def test_unexpected_bug_is_not_swallowed():
    factory = RecordingFactory({"A": [RuntimeError("bug")], "B": ["unused"]})
    with pytest.raises(RuntimeError, match="^bug$"):
        run_batch([Task("A", "a"), Task("B", "b")], factory, sleeper=RecordingSleeper())
    assert factory.calls == ["A"]
    assert factory.gateways["B"].calls == []


def test_inputs_and_previous_batch_are_preserved():
    tasks = [Task("A", "日本語")]
    before = deepcopy(tasks)
    first = run_batch(tasks, RecordingFactory({"A": ["ok"]}), sleeper=RecordingSleeper())
    saved = deepcopy(first)
    second = run_batch([], RecordingFactory({}), sleeper=RecordingSleeper())
    assert tasks == before
    assert first == saved
    assert len(first) == 1
    assert second == []
    assert first is not second
