"""
Pydantic schemas for the Full Analysis API — Phase 4C.
"""

from pydantic import BaseModel, Field

from app.schemas.entity import EntityItem


# ---------------------------------------------------------------------------
# Request
# ---------------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    """Request payload for the full analysis pipeline."""
    text: str = Field(
        ...,
        min_length=10,
        max_length=500_000,
        description="The article text to analyse.",
    )
    language: str | None = Field(
        None,
        pattern="^(en|id)$",
        description=(
            "Optional language override ('en' or 'id'). "
            "If not provided, language is auto-detected."
        ),
    )
    top_keywords: int = Field(
        default=10,
        ge=1,
        le=20,
        description="Maximum number of keywords to extract (1–20).",
    )


# ---------------------------------------------------------------------------
# Response sub-objects
# ---------------------------------------------------------------------------

class LanguageInfo(BaseModel):
    code: str = Field(..., description="Language code: 'id' or 'en'.")
    source: str = Field(..., description="'auto' if auto-detected, 'provided' if passed by caller.")
    confidence: float | None = Field(None, description="Detection confidence (0–1) or null if provided.")
    raw_detected: str | None = Field(None, description="Raw ISO code from detector, or null if language was provided.")


class CategoryResult(BaseModel):
    category: str
    confidence: float
    all_scores: dict[str, float]


class SentimentResult(BaseModel):
    sentiment: str
    confidence: float
    all_scores: dict[str, float]


class KeywordResult(BaseModel):
    keyword: str
    score: float


class KeywordsInfo(BaseModel):
    keywords: list[KeywordResult]
    method: str
    total: int


class EntitiesInfo(BaseModel):
    entities: list[EntityItem]
    model: str


# ---------------------------------------------------------------------------
# Full response
# ---------------------------------------------------------------------------

class AnalyzeResponse(BaseModel):
    """Full analysis response containing all NLP pipeline results."""
    language: LanguageInfo
    category: CategoryResult
    sentiment: SentimentResult
    keywords: KeywordsInfo
    entities: EntitiesInfo
