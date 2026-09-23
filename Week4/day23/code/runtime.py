"""Provided offline dependencies, created afresh for each HTTP request."""

from collections.abc import Callable
from dataclasses import dataclass

from .fakes import RecordingSleeper, SequenceGateway


@dataclass
class BatchRuntime:
    gateway_factory: Callable
    sleeper: Callable


def local_gateway(task_id: str):
    return SequenceGateway([f"模擬結果：{task_id}"])


def get_runtime() -> BatchRuntime:
    return BatchRuntime(local_gateway, RecordingSleeper())
