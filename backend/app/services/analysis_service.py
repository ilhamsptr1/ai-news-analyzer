"""
Analysis Service — Phase 5A Database operations for analyses.

Handles transactions for saving full AI pipeline results into PostgreSQL,
including nested keywords and entities.
"""

from typing import Sequence

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.analysis import Analysis
from app.models.entity import Entity
from app.models.keyword import Keyword
from app.schemas.analysis import AnalysisCreate


class AnalysisServiceError(Exception):
    """Raised when an operation in AnalysisService fails."""


def create_analysis(db: Session, payload: AnalysisCreate) -> Analysis:
    """
    Create a new analysis record along with its keywords and entities.
    Runs entirely within a transaction. Rolls back if any step fails.
    """
    try:
        # Separate nested relationships from core payload
        payload_dict = payload.model_dump(exclude={"keywords", "entities"})
        
        # 1. Create Core Analysis
        analysis = Analysis(**payload_dict)
        db.add(analysis)
        db.flush()  # Gets the analysis.id without committing

        # 2. Add Keywords
        # We enforce UNIQUE(analysis_id, keyword) in the DB.
        # We also filter duplicates in Python just in case to avoid IntegrityError.
        seen_keywords = set()
        for kw_data in payload.keywords:
            kw_text = kw_data.keyword.strip()
            if kw_text not in seen_keywords:
                seen_keywords.add(kw_text)
                db.add(Keyword(
                    analysis_id=analysis.id,
                    keyword=kw_text,
                    score=kw_data.score,
                    rank=kw_data.rank,
                    method=kw_data.method,
                ))

        # 3. Add Entities
        for ent_data in payload.entities:
            db.add(Entity(
                analysis_id=analysis.id,
                text=ent_data.text,
                label=ent_data.label,
                start_position=ent_data.start_position,
                end_position=ent_data.end_position,
                score=ent_data.score,
                normalized_label=ent_data.normalized_label,
            ))

        db.commit()
        db.refresh(analysis)
        return analysis

    except Exception as exc:
        db.rollback()
        raise AnalysisServiceError(f"Failed to create analysis: {exc}") from exc


def get_analysis(db: Session, analysis_id: int) -> Analysis | None:
    """Return an analysis by its ID, including loaded relationships."""
    return db.get(Analysis, analysis_id)


def get_analyses_by_article(db: Session, article_id: int) -> Sequence[Analysis]:
    """Return all analyses for a given article, ordered by newest first."""
    stmt = (
        select(Analysis)
        .where(Analysis.article_id == article_id)
        .order_by(desc(Analysis.created_at), desc(Analysis.id))
    )
    return db.execute(stmt).scalars().all()


def get_latest_analysis(db: Session, article_id: int) -> Analysis | None:
    """Return the most recent analysis for a given article."""
    stmt = (
        select(Analysis)
        .where(Analysis.article_id == article_id)
        .order_by(desc(Analysis.created_at), desc(Analysis.id))
        .limit(1)
    )
    return db.execute(stmt).scalars().first()


def list_recent_analyses(db: Session, limit: int = 20, offset: int = 0) -> Sequence[Analysis]:
    """Return the most recent analyses across all articles."""
    stmt = (
        select(Analysis)
        .order_by(desc(Analysis.created_at), desc(Analysis.id))
        .offset(offset)
        .limit(limit)
    )
    return db.execute(stmt).scalars().all()


def delete_analysis(db: Session, analysis_id: int) -> bool:
    """Delete an analysis by ID. Returns True if deleted, False if not found.
    Cascade will automatically delete associated keywords and entities.
    """
    analysis = db.get(Analysis, analysis_id)
    if analysis is None:
        return False
    try:
        db.delete(analysis)
        db.commit()
        return True
    except Exception as exc:
        db.rollback()
        raise AnalysisServiceError(f"Failed to delete analysis: {exc}") from exc
