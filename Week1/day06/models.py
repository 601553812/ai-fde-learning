"""Pydantic models for the Day 6 requirement tool."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


@dataclass(frozen=True)
class RequirementItem:
    """One classified requirement line with named fields."""

    category: str
    content: str


class RequirementData(BaseModel):
    """Validated collections produced by the text parser."""
    functions:list[str] = Field(default_factory=list)
    acceptance_criteria: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    questions: list[str] = Field(default_factory=list)
    unknown: list[str] = Field(default_factory=list)
    model_config = ConfigDict(extra="forbid")
    pass


class AnalysisOutput(BaseModel):
    """Versioned output schema written by the CLI."""
    schema_version:Literal["1.0"] = "1.0"
    requirements:RequirementData
    validation_errors:list[str] = Field(default_factory=list)
    model_config = ConfigDict(extra="forbid")
    pass
