"""
Dashboard analytics endpoint.
Phase 6: GET /api/dashboard/stats

Uses SQL aggregation — never loads article content.
Handles empty database gracefully.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, distinct, desc, text
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.analysis import Analysis
from app.models.article import Article
from app.schemas.dashboard import (
    CategoryStat,
    DashboardStats,
    LanguageStat,
    OverviewStats,
    RecentAnalysisItem,
    SentimentStat,
    SourceStat,
    TrendPoint,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/stats",
    response_model=DashboardStats,
    summary="Dashboard Statistics",
    description=(
        "Aggregated statistics for the analytics dashboard. "
        "Uses SQL GROUP BY — does not load article content. "
        "Returns empty/zero values when the database has no data."
    ),
)
def get_dashboard_stats(db: Session = Depends(get_db)) -> DashboardStats:
    # ── 1. Overview counts ──────────────────────────────────────────────────
    total_articles: int = db.query(func.count(Article.id)).scalar() or 0
    total_analyses: int = db.query(func.count(Analysis.id)).scalar() or 0

    indonesian_articles: int = (
        db.query(func.count(Analysis.id))
        .filter(Analysis.language_code == "id")
        .scalar()
        or 0
    )
    english_articles: int = (
        db.query(func.count(Analysis.id))
        .filter(Analysis.language_code == "en")
        .scalar()
        or 0
    )
    total_sources: int = (
        db.query(func.count(distinct(Article.source)))
        .filter(Article.source.isnot(None), Article.source != "")
        .scalar()
        or 0
    )

    overview = OverviewStats(
        total_articles=total_articles,
        total_analyses=total_analyses,
        indonesian_articles=indonesian_articles,
        english_articles=english_articles,
        total_sources=total_sources,
    )

    # ── 2. Category distribution ────────────────────────────────────────────
    cat_rows = (
        db.query(Analysis.category, func.count(Analysis.id).label("cnt"))
        .filter(Analysis.category.isnot(None))
        .group_by(Analysis.category)
        .order_by(desc("cnt"))
        .all()
    )
    cat_total = sum(r.cnt for r in cat_rows) or 1  # avoid div/0
    category_distribution = [
        CategoryStat(
            category=r.category,
            count=r.cnt,
            percentage=round(r.cnt / cat_total * 100, 1),
        )
        for r in cat_rows
    ]

    # ── 3. Sentiment distribution ───────────────────────────────────────────
    sent_rows = (
        db.query(Analysis.sentiment, func.count(Analysis.id).label("cnt"))
        .filter(Analysis.sentiment.isnot(None))
        .group_by(Analysis.sentiment)
        .order_by(desc("cnt"))
        .all()
    )
    sent_total = sum(r.cnt for r in sent_rows) or 1
    sentiment_distribution = [
        SentimentStat(
            sentiment=r.sentiment,
            count=r.cnt,
            percentage=round(r.cnt / sent_total * 100, 1),
        )
        for r in sent_rows
    ]

    # ── 4. Language distribution ────────────────────────────────────────────
    lang_rows = (
        db.query(
            Analysis.language_code,
            Analysis.language_name,
            func.count(Analysis.id).label("cnt"),
        )
        .filter(Analysis.language_code.isnot(None))
        .group_by(Analysis.language_code, Analysis.language_name)
        .order_by(desc("cnt"))
        .all()
    )
    language_distribution = [
        LanguageStat(
            language_code=r.language_code,
            language_name=r.language_name or r.language_code,
            count=r.cnt,
        )
        for r in lang_rows
    ]

    # ── 5. Top sources ──────────────────────────────────────────────────────
    source_rows = (
        db.query(Article.source, func.count(Article.id).label("cnt"))
        .filter(Article.source.isnot(None), Article.source != "")
        .group_by(Article.source)
        .order_by(desc("cnt"))
        .limit(10)
        .all()
    )
    top_sources = [
        SourceStat(source=r.source, count=r.cnt) for r in source_rows
    ]

    # ── 6. Recent analyses (no content loaded) ──────────────────────────────
    recent_rows = (
        db.query(
            Analysis.id,
            Analysis.article_id,
            Analysis.language_code,
            Analysis.category,
            Analysis.sentiment,
            Analysis.sentiment_confidence,
            Analysis.category_confidence,
            Analysis.created_at,
            Article.title.label("article_title"),
            Article.source.label("article_source"),
        )
        .join(Article, Analysis.article_id == Article.id, isouter=True)
        .order_by(desc(Analysis.created_at), desc(Analysis.id))
        .limit(10)
        .all()
    )
    recent_analyses = [
        RecentAnalysisItem(
            id=r.id,
            article_id=r.article_id,
            article_title=r.article_title,
            article_source=r.article_source,
            language_code=r.language_code,
            category=r.category,
            sentiment=r.sentiment,
            sentiment_confidence=r.sentiment_confidence,
            category_confidence=r.category_confidence,
            created_at=r.created_at,
        )
        for r in recent_rows
    ]

    # ── 7. Trend — analyses per day, last 30 days ───────────────────────────
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    trend_rows = (
        db.query(
            func.date_trunc("day", Analysis.created_at).label("day"),
            func.count(Analysis.id).label("cnt"),
        )
        .filter(Analysis.created_at >= thirty_days_ago)
        .group_by("day")
        .order_by("day")
        .all()
    )
    trend = [
        TrendPoint(
            date=r.day.strftime("%Y-%m-%d") if r.day else "",
            count=r.cnt,
        )
        for r in trend_rows
    ]

    return DashboardStats(
        overview=overview,
        category_distribution=category_distribution,
        sentiment_distribution=sentiment_distribution,
        language_distribution=language_distribution,
        top_sources=top_sources,
        recent_analyses=recent_analyses,
        trend=trend,
    )
