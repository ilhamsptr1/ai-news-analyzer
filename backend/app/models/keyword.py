"""
Keyword model — stores extracted keywords for an analysis.
Phase 5A: Added rank, method, and unique constraint.
"""

from sqlalchemy import Float, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Keyword(Base):
    __tablename__ = "analysis_keywords"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Foreign key to Analysis
    analysis_id: Mapped[int] = mapped_column(
        ForeignKey("analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Fields
    keyword: Mapped[str] = mapped_column(String(255), nullable=False)
    score: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Relevance score from NLP model"
    )
    rank: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Ranking position (1 is best)"
    )
    method: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="Method used for extraction (e.g. yake)"
    )

    # Relationship
    analysis: Mapped["Analysis"] = relationship(  # noqa: F821
        "Analysis",
        back_populates="keywords",
    )

    # Indexes and constraints
    __table_args__ = (
        Index("ix_analysis_keywords_keyword", "keyword"),
        UniqueConstraint("analysis_id", "keyword", name="uq_analysis_keywords_analysis_id_keyword"),
    )

    def __repr__(self) -> str:
        return f"<Keyword id={self.id} keyword={self.keyword!r} score={self.score}>"
