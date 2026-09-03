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

    # TODO 1: 禁止未知字段，并定义五个 list[str] 字段。
    pass


class AnalysisOutput(BaseModel):
    """Versioned output schema written by the CLI."""

    # TODO 2: 定义 schema_version、requirements 和 validation_errors。
    pass
