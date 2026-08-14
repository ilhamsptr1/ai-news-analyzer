"""
Pydantic schemas for Language Detection API — Phase 4C.
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
        description="Normalised language code: 'id' or 'en'. Non-supported languages fall back to 'en'.",
    )
    confidence: float | None = Field(
        None,
        description="Detection confidence [0.0–1.0] if available, else null.",
    )
    raw_lang: str = Field(
        ...,
        description="Raw ISO 639-1 language code as returned by the detector.",
    )
    method: str = Field(
        ...,
        description="Detection engine used: 'langdetect' or 'langid'.",
    )
    is_supported: bool = Field(
        ...,
        description="True if the detected language is directly supported by the AI pipeline.",
    )
    fallback_applied: bool = Field(
        ...,
        description="True when the raw detected language was not supported and fell back to 'en'.",
    )
