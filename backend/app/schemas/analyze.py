"""
Pydantic schemas for the Full Analysis API — Phase 4C (Patched).
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
# Response sub-objects — Supported languages
# ---------------------------------------------------------------------------

class LanguageInfo(BaseModel):
    code: str = Field(..., description="Detected language code (e.g. 'id', 'en', 'fr').")
    language_name: str = Field(..., description="Human-readable language name.")
    source: str = Field(..., description="'auto' if auto-detected, 'provided' if passed by caller.")
    confidence: float | None = Field(None, description="Detection confidence (0–1), or null.")
    supported: bool = Field(..., description="True if language is supported by the AI pipeline.")


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
# Full response — supported language
# ---------------------------------------------------------------------------

class AnalyzeResponse(BaseModel):
    """Full analysis response (returned when language IS supported)."""
    status: str = Field(default="ok", description="Always 'ok' for supported languages.")
    language: LanguageInfo
    category: CategoryResult
    sentiment: SentimentResult
    keywords: KeywordsInfo
    entities: EntitiesInfo

from app.schemas.article import ArticleResponse
from app.schemas.analysis import AnalysisResponse

class ArticleAnalyzeRequest(BaseModel):
    """Request payload for E2E Article Analysis."""
    url: str = Field(..., description="The URL of the article to extract and analyze.")
    top_keywords: int = Field(default=10, ge=1, le=20)

class ArticleAnalyzeResponse(BaseModel):
    """Full end-to-end response containing both the article and its saved analysis."""
    article: ArticleResponse
    analysis: AnalysisResponse


# ---------------------------------------------------------------------------
# Unsupported language response
# ---------------------------------------------------------------------------

class UnsupportedLanguageResponse(BaseModel):
    """
    Returned when the detected language is not supported by the AI pipeline.
    No ML analysis is performed.
    """
    status: str = Field(
        default="unsupported_language",
        description="Always 'unsupported_language' for unsupported languages.",
    )
    language: LanguageInfo
    message: str = Field(
        ...,
        description="Human-readable explanation in Bahasa Indonesia.",
    )
