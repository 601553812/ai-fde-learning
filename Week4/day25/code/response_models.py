"""Day25 exercise: describe the response returned by the local batch API."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictResponse(BaseModel):
    """All response layers reject unknown fields and type coercion."""

    model_config = ConfigDict(extra="forbid", strict=True)


class ResultResponse(StrictResponse):
    ok: bool
    raw: str|None
    error: str|None
    status_code: int|None


class RetryResponse(StrictResponse):
    result: ResultResponse
    attempts: int = Field(ge=1)


class TaskResponse(StrictResponse):
    task_id: str
    report: RetryResponse


class SummaryResponse(StrictResponse):
    requests:int= Field(ge=0)
    succeeded:int= Field(ge=0)
    failed:int= Field(ge=0)
    attempts:int= Field(ge=0)
    retries:int= Field(ge=0)


class BatchResponse(StrictResponse):
    mode: Literal["simulated"]
    tasks: list[TaskResponse]
    summary: SummaryResponse
