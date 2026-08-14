"""
Keyword Pydantic schemas.

Contains:
  - KeywordCreate / KeywordResponse   : Phase 2 database schemas
  - KeywordExtractRequest             : Phase 4B-2 API request
  - KeywordItem                       : Phase 4B-2 single result item
  - KeywordExtractResponse            : Phase 4B-2 API response
"""

from typing import List

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------------------------------------------------------------------------
# Phase 2 — Database schemas (must not be removed)
# ---------------------------------------------------------------------------

class KeywordCreate(BaseModel):
    """Schema for creating a keyword record linked to an analysis (Phase 2 DB)."""
    analysis_id: int
    keyword: str = Field(..., min_length=1, max_length=255)
    score: float | None = Field(default=None, ge=0.0, le=1.0)


class KeywordResponse(BaseModel):
    """Schema for returning a keyword record from the database (Phase 2 DB)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    analysis_id: int
    keyword: str
    score: float | None


# ---------------------------------------------------------------------------
# Phase 4B-2 — Keyword Extraction API schemas
# ---------------------------------------------------------------------------

class KeywordExtractRequest(BaseModel):
    """Request body for POST /api/keywords/extract."""

    text: str = Field(
        ...,
        min_length=1,
        max_length=500_000,
        description="Article or text to extract keywords from.",
        examples=["Apple announced a new artificial intelligence chip for its devices."],
    )
    top_n: int = Field(
        default=10,
        ge=1,
        le=20,
        description="Maximum number of keywords to return (1-20).",
        examples=[10],
    )

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("text must not be blank or whitespace only.")
        return v


class KeywordItem(BaseModel):
    """A single extracted keyword with its relevance score."""

    keyword: str = Field(
        ...,
        description="Extracted keyword or keyphrase.",
        examples=["artificial intelligence"],
    )
    score: float = Field(
        ...,
        description=(
            "Relevance score. "
            "For YAKE: lower score = higher relevance (NOT a probability). "
            "For TF-IDF: higher score = higher relevance."
        ),
        examples=[0.021],
    )


class KeywordExtractResponse(BaseModel):
    """Response body from POST /api/keywords/extract."""

    keywords: List[KeywordItem] = Field(
        ...,
        description="List of extracted keywords with scores.",
    )
    method: str = Field(
        ...,
        description="Algorithm used: 'yake' (primary) or 'tfidf' (fallback).",
        examples=["yake"],
    )
    total: int = Field(
        ...,
        description="Total number of keywords returned.",
        examples=[10],
    )
    note: str = Field(
        default="",
        description="Informational note about score interpretation.",
    )
