"""Provided per-task gateway lookup with an observable creation log."""

from .fakes import SequenceGateway


class RecordingFactory:
    def __init__(self, outcomes_by_id):
        self.gateways = {key: SequenceGateway(value) for key, value in outcomes_by_id.items()}
        self.calls = []

    def __call__(self, task_id):
        self.calls.append(task_id)
        return self.gateways[task_id]
