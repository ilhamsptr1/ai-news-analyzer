"""
Full Analysis Route — Phase 4C (Patched: Fix Unsupported Language Routing).

Endpoints:
    POST /api/analyze
"""

import logging

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from app.ai.multilingual_analyzer import get_multilingual_analyzer
from app.schemas.analyze import (
    AnalyzeRequest,
    AnalyzeResponse,
    CategoryResult,
    ClickbaitResult,
    EntitiesInfo,
    KeywordResult,
    KeywordsInfo,
    LanguageInfo,
    SentimentResult,
    UnsupportedLanguageResponse,
)
from app.schemas.entity import EntityItem

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Analysis"])

_UNSUPPORTED_MSG = (
    "Bahasa artikel tidak didukung. "
    "Saat ini AI News Analyzer mendukung Bahasa Indonesia (id) dan Bahasa Inggris (en)."
)


@router.post(
    "/analyze",
    summary="Full Article Analysis",
    description=(
        "Run the complete NLP analysis pipeline on a text. "
        "Language is auto-detected; pass `language` to override. "
        "If the language is not supported ('id' or 'en'), "
        "returns status='unsupported_language' and does NOT run ML models."
    ),
)
def analyze(request: AnalyzeRequest):
    """
    Full NLP pipeline for a news article.

    - **text**: Article text (min 10 chars, max 500,000 chars).
    - **language**: Optional override ('id' or 'en'). Auto-detected if omitted.
    - **top_keywords**: Number of keywords to extract (default 10).

    Returns `AnalyzeResponse` for supported languages,
    or `UnsupportedLanguageResponse` for unsupported ones.
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

    lang_data = result["language"]
    lang_info = LanguageInfo(
        code=lang_data["code"],
        language_name=lang_data.get("language_name", lang_data["code"].upper()),
        source=lang_data["source"],
        confidence=lang_data.get("confidence"),
        supported=lang_data["supported"],
    )

    # -- Unsupported language: return early, NO ML results ----------------
    if not result["supported"]:
        resp = UnsupportedLanguageResponse(
            status="unsupported_language",
            language=lang_info,
            message=_UNSUPPORTED_MSG,
        )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=resp.model_dump(),
        )

    # -- Supported language: return full analysis -------------------------
    cat_data = result["category"]
    sent_data = result["sentiment"]
    kw_data = result["keywords"]
    ent_data = result["entities"]

    return AnalyzeResponse(
        status="ok",
        language=lang_info,
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
        clickbait=ClickbaitResult(
            score=result.get("clickbait", {}).get("score", 0.0),
            reasons=result.get("clickbait", {}).get("reasons", [])
        )
    )
