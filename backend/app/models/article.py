"""
Article model — represents a news article stored in the database.
Phase 3: Added author, word_count, reading_time fields.
"""

from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Article(Base):
    __tablename__ = "articles"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Core fields
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Phase 3: Extraction metadata
    author: Mapped[str | None] = mapped_column(String(500), nullable=True)
    word_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reading_time: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Estimated reading time in minutes"
    )

    # Timestamps
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    analyses: Mapped[list["Analysis"]] = relationship(  # noqa: F821
        "Analysis",
        back_populates="article",
        cascade="all, delete-orphan",
        lazy="select",
    )

    # Indexes + unique constraint on URL
    __table_args__ = (
        Index("ix_articles_created_at", "created_at"),
        UniqueConstraint("url", name="uq_articles_url"),
    )

    def __repr__(self) -> str:
        return f"<Article id={self.id} title={self.title!r}>"
