"""Request contract; reuse the verified Day 6 response contract."""

from pydantic import BaseModel, ConfigDict, Field


class AnalyzeRequest(BaseModel):
    """Accept nonempty requirement text and reject unexpected fields."""

    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1)
