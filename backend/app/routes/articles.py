"""
AI News Analyzer — Articles Router

Endpoints:
    POST   /api/articles/extract   Extract & save article from URL
    POST   /api/articles           Create article manually
    GET    /api/articles           List articles (paginated)
    GET    /api/articles/{id}      Get article by ID
    DELETE /api/articles/{id}      Delete article by ID
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.article import (
    ArticleCreate,
    ArticleExtractRequest,
    ArticleListResponse,
    ArticleResponse,
)
from app.services.article_extractor import (
    ExtractionError,
    FetchError,
    TimeoutError,
    extract_article,
)
from app.services.article_service import (
    create_article,
    create_article_from_extraction,
    delete_article,
    get_article_by_id,
    get_articles,
)
from app.utils.url_validator import SSRFBlockedError, URLValidationError, validate_url

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# POST /api/articles/extract
# ---------------------------------------------------------------------------


@router.post(
    "/extract",
    response_model=ArticleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Extract Article from URL",
    description=(
        "Fetch a public news article URL, extract its content using Trafilatura "
        "(with BeautifulSoup fallback), and persist it to the database. "
        "Returns 200 if the URL was already extracted previously."
    ),
    tags=["Articles"],
    responses={
        201: {"description": "Article extracted and saved"},
        200: {"description": "Article already exists (duplicate URL)"},
        400: {"description": "Invalid or blocked URL"},
        422: {"description": "Content could not be extracted"},
        502: {"description": "Remote server error"},
        504: {"description": "Request timed out"},
    },
)
def extract_article_endpoint(
    payload: ArticleExtractRequest,
    db: Session = Depends(get_db),
):
    """
    Route handler for article extraction.

    - Validates URL (scheme, SSRF)
    - Fetches + extracts article
    - Saves to database (or returns existing if duplicate)
    """
    # Step 1 — URL validation + SSRF protection
    try:
        safe_url = validate_url(payload.url)
    except SSRFBlockedError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"URL not allowed: {exc}",
        )
    except URLValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid URL: {exc}",
        )

    # Step 2 — Fetch + extract
    try:
        result = extract_article(safe_url)
    except TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="The request to the article URL timed out. Please try again later.",
        )
    except FetchError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not reach the article URL. The server may be unavailable.",
        )
    except ExtractionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Article content could not be extracted. "
                "The page may require JavaScript, be behind a paywall, "
                "or have a non-standard layout."
            ),
        )
    except Exception as exc:
        logger.error("Unexpected extraction error for %s: %s", safe_url, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during extraction.",
        )

    # Step 3 — Persist (handle duplicates)
    try:
        article, created = create_article_from_extraction(db, result)
    except Exception as exc:
        logger.error("Database error saving article %s: %s", safe_url, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save article to the database.",
        )

    # Return 200 for existing articles, 201 for new ones
    if not created:
        from fastapi.responses import JSONResponse
        from app.schemas.article import ArticleResponse as AR
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=AR.model_validate(article).model_dump(mode="json"),
        )

    return article


# ---------------------------------------------------------------------------
# POST /api/articles  (manual creation)
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=ArticleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Article",
    description="Manually store a news article in the database.",
    tags=["Articles"],
)
def create_article_endpoint(
    payload: ArticleCreate,
    db: Session = Depends(get_db),
) -> ArticleResponse:
    try:
        article = create_article(db, payload)
        return article
    except Exception as exc:
        logger.error("Error creating article: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create article.",
        )


# ---------------------------------------------------------------------------
# GET /api/articles
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=ArticleListResponse,
    summary="List Articles",
    description="Retrieve a paginated list of all stored articles.",
    tags=["Articles"],
)
def list_articles_endpoint(
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=20, ge=1, le=100, description="Max records to return"),
    db: Session = Depends(get_db),
) -> ArticleListResponse:
    articles, total = get_articles(db, skip=skip, limit=limit)
    return ArticleListResponse(total=total, articles=articles)


# ---------------------------------------------------------------------------
# GET /api/articles/{id}
# ---------------------------------------------------------------------------


@router.get(
    "/{article_id}",
    response_model=ArticleResponse,
    summary="Get Article",
    description="Retrieve a single article by its ID.",
    tags=["Articles"],
)
def get_article_endpoint(
    article_id: int,
    db: Session = Depends(get_db),
) -> ArticleResponse:
    article = get_article_by_id(db, article_id)
    if article is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article with id={article_id} not found.",
        )
    return article


# ---------------------------------------------------------------------------
# DELETE /api/articles/{id}
# ---------------------------------------------------------------------------


@router.delete(
    "/{article_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Article",
    description="Delete an article and all its associated analyses.",
    tags=["Articles"],
)
def delete_article_endpoint(
    article_id: int,
    db: Session = Depends(get_db),
) -> None:
    deleted = delete_article(db, article_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article with id={article_id} not found.",
        )
