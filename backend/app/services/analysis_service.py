"""
Analysis Service — database operations for analyses.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.analysis import Analysis
from app.schemas.analysis import AnalysisCreate


def create_analysis(db: Session, payload: AnalysisCreate) -> Analysis:
    """Create a new analysis record."""
    analysis = Analysis(**payload.model_dump())
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis


def get_analyses_by_article(db: Session, article_id: int) -> list[Analysis]:
    """Return all analyses for a given article."""
    stmt = select(Analysis).where(Analysis.article_id == article_id)
    return list(db.execute(stmt).scalars().all())


def delete_analysis(db: Session, analysis_id: int) -> bool:
    """Delete an analysis by ID. Returns True if deleted, False if not found."""
    analysis = db.get(Analysis, analysis_id)
    if analysis is None:
        return False
    db.delete(analysis)
    db.commit()
    return True
