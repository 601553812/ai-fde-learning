"""TODO 3: duplicate validation must precede any task execution."""

import pytest

from .batch import Task, run_batch
from .batch_fakes import RecordingFactory
from .fakes import RecordingSleeper


def test_duplicate_id_rejects_whole_batch_before_calls():
    tasks = [Task("A", "one"), Task("B", "two"), Task("A", "three")]
    factory = RecordingFactory({"A": ["ok"], "B": ["ok"]})
    sleeper = RecordingSleeper()
    with pytest.raises(ValueError,  match="^duplicate task_id$"):
        run_batch(tasks,factory,max_attempts= 3, sleeper=sleeper)
    assert factory.calls == []
    assert factory.gateways["A"].calls == []
    assert factory.gateways["B"].calls == []
    assert sleeper.calls == []
