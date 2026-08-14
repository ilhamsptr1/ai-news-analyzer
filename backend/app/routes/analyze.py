"""
Full Analysis Route — Phase 4C.

Endpoints:
    POST /api/analyze
"""

import logging

from fastapi import APIRouter, HTTPException, status

from app.ai.multilingual_analyzer import get_multilingual_analyzer
from app.schemas.analyze import (
    AnalyzeRequest,
    AnalyzeResponse,
    CategoryResult,
    EntitiesInfo,
    KeywordResult,
    KeywordsInfo,
    LanguageInfo,
    SentimentResult,
)
from app.schemas.entity import EntityItem

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Analysis"])


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    status_code=status.HTTP_200_OK,
    summary="Full Article Analysis",
    description=(
        "Run the complete NLP analysis pipeline on a text: "
        "auto-detects language, then performs category classification, "
        "sentiment analysis, keyword extraction, and named entity recognition. "
        "Optionally pass `language` to skip auto-detection."
    ),
)
def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    """
    Full NLP pipeline for a news article.

    - **text**: Article text (min 10 chars, max 500,000 chars).
    - **language**: Optional override ('id' or 'en'). Auto-detected if omitted.
    - **top_keywords**: Number of keywords to extract (default 10).
    """
    analyzer = get_multilingual_analyzer()

    try:
        result = analyzer.analyze(
            text=request.text,
            language=request.language,
            top_keywords=request.top_keywords,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error("Analysis pipeline error: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Analysis failed. Please try again.",
        )

    # -- Build structured response ----------------------------------------
    lang_data = result["language"]
    cat_data = result["category"]
    sent_data = result["sentiment"]
    kw_data = result["keywords"]
    ent_data = result["entities"]

    return AnalyzeResponse(
        language=LanguageInfo(
            code=lang_data["code"],
            source=lang_data["source"],
            confidence=lang_data.get("confidence"),
            raw_detected=lang_data.get("raw_detected"),
        ),
        category=CategoryResult(
            category=cat_data.get("category", "Unknown"),
            confidence=cat_data.get("confidence", 0.0),
            all_scores=cat_data.get("all_scores", {}),
        ),
        sentiment=SentimentResult(
            sentiment=sent_data.get("sentiment", "Unknown"),
            confidence=sent_data.get("confidence", 0.0),
            all_scores=sent_data.get("all_scores", {}),
        ),
        keywords=KeywordsInfo(
            keywords=[
                KeywordResult(keyword=kw["keyword"], score=kw["score"])
                for kw in kw_data.get("keywords", [])
            ],
            method=kw_data.get("method", "yake"),
            total=kw_data.get("total", 0),
        ),
        entities=EntitiesInfo(
            entities=[
                EntityItem(
                    text=ent["text"],
                    label=ent["label"],
                    start=ent["start"],
                    end=ent["end"],
                    score=ent.get("score"),
                )
                for ent in ent_data.get("entities", [])
            ],
            model=ent_data.get("model", ""),
        ),
    )
