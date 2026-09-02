"""Data models for the requirement tool."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RequirementItem:
    """One classified requirement line with named fields."""

    category: str
    content: str
