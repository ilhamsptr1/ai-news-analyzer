"""
Analysis model — stores AI/NLP analysis results for an article.
Phase 5A: Added language, confidence scores, and model_versions.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
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

    # Language fields
    language_code: Mapped[str | None] = mapped_column(String(10), nullable=True, index=True)
    language_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    language_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    # AI/NLP output fields
    category: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    category_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    sentiment: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    sentiment_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Keeping old fields for backwards compatibility
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    sentiment_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    topic: Mapped[str | None] = mapped_column(String(200), nullable=True)
    word_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    character_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reading_time: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Estimated reading time in seconds"
    )

    # Model versions tracking
    model_versions: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False
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

    def __repr__(self) -> str:
        return f"<Analysis id={self.id} article_id={self.article_id} language={self.language_code!r} category={self.category!r} sentiment={self.sentiment!r}>"
