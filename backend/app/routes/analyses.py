import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models.analysis import Analysis
from app.schemas.analysis import (
    AnalysisDetailResponse,
    AnalysisListResponse,
    AnalysisListItem,
)
from app.schemas.article import ArticleResponse

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get(
    "",
    response_model=AnalysisListResponse,
    summary="List Analysis History",
    description="Retrieve a paginated list of analysis history with optional filters.",
)
def list_analyses_endpoint(
    language: str | None = Query(None, description="Filter by language code (e.g. 'id', 'en')"),
    category: str | None = Query(None, description="Filter by category"),
    sentiment: str | None = Query(None, description="Filter by sentiment"),
    limit: int = Query(20, ge=1, le=100, description="Max records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    db: Session = Depends(get_db),
):
    query = db.query(Analysis).options(selectinload(Analysis.article))
    
    if language:
        query = query.filter(Analysis.language_code == language)
    if category:
        query = query.filter(Analysis.category == category)
    if sentiment:
        query = query.filter(Analysis.sentiment == sentiment)
        
    total = query.count()
    
    # Ordering: newest first, ID secondary
    query = query.order_by(desc(Analysis.created_at), desc(Analysis.id))
    
    analyses = query.offset(offset).limit(limit).all()
    
    # Map to AnalysisListItem
    items = []
    for a in analyses:
        items.append(AnalysisListItem(
            id=a.id,
            article_id=a.article_id,
            created_at=a.created_at,
            language_code=a.language_code,
            language_name=a.language_name,
            category=a.category,
            sentiment=a.sentiment,
            sentiment_confidence=a.sentiment_confidence,
            category_confidence=a.category_confidence,
            language_confidence=a.language_confidence,
            article_title=a.article.title if a.article else None,
            article_source=a.article.source if a.article else None,
            article_published_at=a.article.published_at if a.article else None,
        ))
        
    return AnalysisListResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=items
    )

@router.get(
    "/{analysis_id}",
    response_model=AnalysisDetailResponse,
    summary="Get Analysis Detail",
    description="Retrieve full details for an analysis, including its article, keywords, and entities.",
)
def get_analysis_detail_endpoint(
    analysis_id: int,
    db: Session = Depends(get_db),
):
    # Load analysis with all relations
    analysis = db.query(Analysis).options(
        selectinload(Analysis.article),
        selectinload(Analysis.keywords),
        selectinload(Analysis.entities)
    ).filter(Analysis.id == analysis_id).first()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis with id={analysis_id} not found."
        )
        
    if not analysis.article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated article not found."
        )
        
    return AnalysisDetailResponse(
        analysis=analysis,
        article=ArticleResponse.model_validate(analysis.article)
    )
