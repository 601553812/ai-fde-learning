"""Provided HTTP input validation; no model calls occur here."""

from pydantic import BaseModel, Field


class TaskInput(BaseModel):
    task_id: str = Field(min_length=1)
    text: str = Field(min_length=1, max_length=2000)


class BatchRequest(BaseModel):
    tasks: list[TaskInput] = Field(max_length=10)
    max_attempts: int = Field(default=3, ge=1, le=3, strict=True)
