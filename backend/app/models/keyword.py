"""
Keyword model — stores extracted keywords for an analysis.
"""

from sqlalchemy import Float, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Keyword(Base):
    __tablename__ = "keywords"

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

    # Relationship
    analysis: Mapped["Analysis"] = relationship(  # noqa: F821
        "Analysis",
        back_populates="keywords",
    )

    # Indexes
    __table_args__ = (Index("ix_keywords_keyword", "keyword"),)

    def __repr__(self) -> str:
        return f"<Keyword id={self.id} keyword={self.keyword!r} score={self.score}>"
