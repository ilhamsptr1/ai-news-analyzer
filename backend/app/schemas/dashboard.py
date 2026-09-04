"""
Pydantic schemas for the Dashboard statistics endpoint.
Phase 6: Dashboard & Analytics
"""
from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel


class OverviewStats(BaseModel):
    total_articles: int
    total_analyses: int
    indonesian_articles: int
    english_articles: int
    total_sources: int


class CategoryStat(BaseModel):
    category: str
    count: int
    percentage: float


class SentimentStat(BaseModel):
    sentiment: str
    count: int
    percentage: float


class LanguageStat(BaseModel):
    language_code: str
    language_name: str
    count: int


class SourceStat(BaseModel):
    source: str
    count: int


class RecentAnalysisItem(BaseModel):
    id: int
    article_id: int
    article_title: str | None
    article_source: str | None
    language_code: str | None
    category: str | None
    sentiment: str | None
    sentiment_confidence: float | None
    category_confidence: float | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TrendPoint(BaseModel):
    date: str          # ISO date string "YYYY-MM-DD"
    count: int


class DashboardStats(BaseModel):
    overview: OverviewStats
    category_distribution: list[CategoryStat]
    sentiment_distribution: list[SentimentStat]
    language_distribution: list[LanguageStat]
    top_sources: list[SourceStat]
    recent_analyses: list[RecentAnalysisItem]
    trend: list[TrendPoint]
