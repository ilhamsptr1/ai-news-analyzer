"""Analysis Pydantic schemas — Phase 5A."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Keywords and Entities Schemas for Analysis Creation & Response
# ---------------------------------------------------------------------------

class AnalysisKeywordCreate(BaseModel):
    keyword: str
    score: float | None = None
    rank: int | None = None
    method: str | None = None

class AnalysisKeywordResponse(AnalysisKeywordCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


class AnalysisEntityCreate(BaseModel):
    text: str
    label: str
    start_position: int
    end_position: int
    score: float | None = None
    normalized_label: str | None = None

class AnalysisEntityResponse(AnalysisEntityCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


# ---------------------------------------------------------------------------
# Core Analysis Schemas
# ---------------------------------------------------------------------------

class AnalysisCreate(BaseModel):
    """Schema for creating a new analysis in the database."""

    article_id: int
    
    # Language
    language_code: str | None = None
    language_name: str | None = None
    language_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    
    # Category & Sentiment
    category: str | None = None
    category_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    sentiment: str | None = None
    sentiment_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    
    # Legacy fields mapping
    summary: str | None = None
    sentiment_score: float | None = Field(default=None, ge=-1.0, le=1.0)
    topic: str | None = None
    word_count: int | None = Field(default=None, ge=0)
    character_count: int | None = Field(default=None, ge=0)
    reading_time: int | None = Field(default=None, ge=0)

    # Model metadata
    model_versions: dict[str, Any] | None = None

    # Nested data for creation
    keywords: list[AnalysisKeywordCreate] = Field(default_factory=list)
    entities: list[AnalysisEntityCreate] = Field(default_factory=list)


class AnalysisResponse(BaseModel):
    """Schema for returning an analysis, including nested keywords and entities."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    article_id: int
    
    language_code: str | None
    language_name: str | None
    language_confidence: float | None
    
    category: str | None
    category_confidence: float | None
    sentiment: str | None
    sentiment_confidence: float | None
    
    summary: str | None
    sentiment_score: float | None
    topic: str | None
    word_count: int | None
    character_count: int | None
    reading_time: int | None
    
    model_versions: dict[str, Any] | None

    created_at: datetime
    updated_at: datetime

    # Relationships
    keywords: list[AnalysisKeywordResponse]
    entities: list[AnalysisEntityResponse]
