"""Day22 exercise: execute independent tasks in order."""

from collections.abc import Callable
from dataclasses import dataclass

from .gemini_gateway import GeminiGateway
from .prompt import build_request
from .retry_service import RetryResult, call_with_retry


@dataclass(frozen=True)
class Task:
    task_id: str
    text: str


@dataclass(frozen=True)
class TaskReport:
    task_id: str
    report: RetryResult


def validate_task_ids(tasks: list[Task]) -> None:
    set = []
    for task in tasks:
        if task.task_id not in set:
            set.append(task.task_id)
        else:
            raise ValueError("duplicate task_id")
    return None


def run_batch(
    tasks: list[Task],
    gateway_factory: Callable[[str], GeminiGateway],
    *,
    max_attempts: int = 3,
    sleeper: Callable[[float], None],
) -> list[TaskReport]:
    validate_task_ids(tasks)
    task_reports = []
    for task in tasks:
        gateway = gateway_factory(task.task_id)
        request = build_request(task.text)
        retryResult = call_with_retry(gateway, request, max_attempts=max_attempts,sleeper=sleeper)
        task_reports.append(TaskReport(task.task_id, retryResult))
    return task_reports
