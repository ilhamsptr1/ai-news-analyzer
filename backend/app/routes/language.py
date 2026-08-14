"""
Language Detection Route — Phase 4C.

Endpoints:
    POST /api/language/detect
"""

import logging

from fastapi import APIRouter, HTTPException, status

from app.ai.language_detector import LanguageDetectionError, get_language_detector
from app.schemas.language import LanguageDetectRequest, LanguageDetectResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Language"])


@router.post(
    "/detect",
    response_model=LanguageDetectResponse,
    status_code=status.HTTP_200_OK,
    summary="Detect Language",
    description=(
        "Automatically detect the language of a text. "
        "Returns 'id' (Indonesian) or 'en' (English). "
        "Unsupported languages are mapped to 'en' as default. "
        "Uses langdetect with langid as fallback — 100% local, no API calls."
    ),
)
def detect_language(request: LanguageDetectRequest) -> LanguageDetectResponse:
    """
    Detect the language of the provided text.

    - **text**: Input text (min 10 characters).

    Returns the detected language code, confidence, and detection method.
    """
    detector = get_language_detector()
    try:
        result = detector.detect(request.text)
        return LanguageDetectResponse(**result)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    except LanguageDetectionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error("Language detection error: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Language detection failed. Please try again.",
        )
