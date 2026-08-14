"""
AI News Analyzer — Articles Router

Endpoints:
    POST   /api/articles          Create a new article
    GET    /api/articles          List articles (paginated)
    GET    /api/articles/{id}     Get article by ID
    DELETE /api/articles/{id}     Delete article by ID
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.article import ArticleCreate, ArticleListResponse, ArticleResponse
from app.services.article_service import (
    create_article,
    delete_article,
    get_article_by_id,
    get_articles,
)

router = APIRouter()


@router.post(
    "",
    response_model=ArticleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Article",
    description="Store a new news article in the database.",
    tags=["Articles"],
)
def create_article_endpoint(
    payload: ArticleCreate,
    db: Session = Depends(get_db),
) -> ArticleResponse:
    """Create and persist a new article."""
    try:
        article = create_article(db, payload)
        return article
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create article. Please try again.",
        ) from exc


@router.get(
    "",
    response_model=ArticleListResponse,
    summary="List Articles",
    description="Retrieve a paginated list of all articles.",
    tags=["Articles"],
)
def list_articles_endpoint(
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=20, ge=1, le=100, description="Max records to return"),
    db: Session = Depends(get_db),
) -> ArticleListResponse:
    """Return paginated list of articles."""
    articles, total = get_articles(db, skip=skip, limit=limit)
    return ArticleListResponse(total=total, articles=articles)


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
    """Return article by ID or raise 404."""
    article = get_article_by_id(db, article_id)
    if article is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article with id={article_id} not found.",
        )
    return article


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
    """Delete article by ID or raise 404."""
    deleted = delete_article(db, article_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article with id={article_id} not found.",
        )
