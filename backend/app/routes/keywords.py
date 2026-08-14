"""
Keyword Extraction Route — Phase 4B-2.

Endpoints:
    POST /api/keywords/extract
"""

import logging

from fastapi import APIRouter, HTTPException, status

from app.ai.keyword_extractor import get_keyword_extractor
from app.schemas.keyword import (
    KeywordExtractRequest,
    KeywordExtractResponse,
    KeywordItem,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Keywords"])

_SCORE_NOTES = {
    "yake": (
        "YAKE score: lower value = higher relevance. "
        "This is a statistical relevance score, NOT a probability or confidence."
    ),
    "tfidf": (
        "TF-IDF score: higher value = higher relevance. "
        "This is a term-frequency/inverse-document-frequency score, NOT a probability."
    ),
}


@router.post(
    "/extract",
    response_model=KeywordExtractResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract keywords from text",
    description=(
        "Extracts keywords and keyphrases from the provided text using YAKE "
        "(primary) with TF-IDF as fallback. "
        "Score is a relevance metric, not a probability."
    ),
)
async def extract_keywords(request: KeywordExtractRequest) -> KeywordExtractResponse:
    """
    Extract keywords from article text.

    - **text**: Input article or text (max 500,000 characters).
    - **top_n**: Maximum keywords to return (1–20, default 10).

    Score interpretation:
    - YAKE: lower score = higher relevance.
    - TF-IDF: higher score = higher relevance.
    """
    extractor = get_keyword_extractor()

    try:
        result = extractor.extract(text=request.text, top_n=request.top_n)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error("Keyword extraction error: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Keyword extraction failed. Please try again.",
        )

    method = result.get("method", "yake")
    keywords = [
        KeywordItem(keyword=item["keyword"], score=item["score"])
        for item in result.get("keywords", [])
    ]

    return KeywordExtractResponse(
        keywords=keywords,
        method=method,
        total=len(keywords),
        note=_SCORE_NOTES.get(method, ""),
    )
