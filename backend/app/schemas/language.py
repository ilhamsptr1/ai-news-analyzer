"""
Pydantic schemas for Language Detection API — Phase 4C (Patched).
"""

from pydantic import BaseModel, Field


class LanguageDetectRequest(BaseModel):
    """Request payload for language detection."""
    text: str = Field(
        ...,
        min_length=10,
        max_length=500_000,
        description="The text to detect language from. Min 10 characters.",
    )


class LanguageDetectResponse(BaseModel):
    """Response payload containing detected language metadata."""
    language: str = Field(
        ...,
        description=(
            "Detected ISO 639-1 language code (e.g. 'id', 'en', 'fr'). "
            "Always the raw detected code — NEVER silently converted."
        ),
    )
    language_name: str = Field(
        ...,
        description="Human-readable language name (e.g. 'Indonesian', 'French').",
    )
    confidence: float | None = Field(
        None,
        description="Detection confidence [0.0–1.0] from langdetect, or null if unavailable.",
    )
    method: str = Field(
        ...,
        description="Detection engine used: 'langdetect' or 'langid'.",
    )
    supported: bool = Field(
        ...,
        description=(
            "True if this language is supported by the AI pipeline ('id' or 'en'). "
            "False for all other languages — no ML analysis will run."
        ),
    )
