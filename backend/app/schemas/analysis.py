"""Analysis Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AnalysisCreate(BaseModel):
    """Schema for creating a new analysis (used internally by AI pipeline in Phase 3)."""

    article_id: int
    summary: str | None = None
    sentiment: str | None = None
    sentiment_score: float | None = Field(default=None, ge=-1.0, le=1.0)
    category: str | None = None
    topic: str | None = None
    word_count: int | None = Field(default=None, ge=0)
    character_count: int | None = Field(default=None, ge=0)
    reading_time: int | None = Field(default=None, ge=0)


class AnalysisResponse(BaseModel):
    """Schema for returning an analysis."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    article_id: int
    summary: str | None
    sentiment: str | None
    sentiment_score: float | None
    category: str | None
    topic: str | None
    word_count: int | None
    character_count: int | None
    reading_time: int | None
    created_at: datetime
