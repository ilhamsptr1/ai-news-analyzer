"""
Analysis model — stores AI/NLP analysis results for an article.
Will be populated by the AI pipeline in Phase 3.
"""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Analysis(Base):
    __tablename__ = "analyses"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Foreign key to Article
    article_id: Mapped[int] = mapped_column(
        ForeignKey("articles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # AI/NLP output fields (nullable — filled by Phase 3 pipeline)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    sentiment: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sentiment_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    topic: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Computed metrics
    word_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    character_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reading_time: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Estimated reading time in seconds"
    )

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    article: Mapped["Article"] = relationship(  # noqa: F821
        "Article",
        back_populates="analyses",
    )

    keywords: Mapped[list["Keyword"]] = relationship(  # noqa: F821
        "Keyword",
        back_populates="analysis",
        cascade="all, delete-orphan",
        lazy="select",
    )

    entities: Mapped[list["Entity"]] = relationship(  # noqa: F821
        "Entity",
        back_populates="analysis",
        cascade="all, delete-orphan",
        lazy="select",
    )

    # Indexes
    __table_args__ = (
        Index("ix_analyses_sentiment", "sentiment"),
        Index("ix_analyses_category", "category"),
        Index("ix_analyses_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Analysis id={self.id} article_id={self.article_id} sentiment={self.sentiment!r}>"
