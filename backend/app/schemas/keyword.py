"""Keyword Pydantic schemas."""

from pydantic import BaseModel, ConfigDict, Field


class KeywordCreate(BaseModel):
    analysis_id: int
    keyword: str = Field(..., min_length=1, max_length=255)
    score: float | None = Field(default=None, ge=0.0, le=1.0)


class KeywordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    analysis_id: int
    keyword: str
    score: float | None
