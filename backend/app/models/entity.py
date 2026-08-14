"""
Entity model — stores named entities extracted from an article analysis.
Phase 5A: Updated fields to text, label, start_position, end_position, score, normalized_label.
"""

from sqlalchemy import Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Entity(Base):
    __tablename__ = "analysis_entities"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Foreign key to Analysis
    analysis_id: Mapped[int] = mapped_column(
        ForeignKey("analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Fields
    text: Mapped[str] = mapped_column(
        String(500), nullable=False, comment="The recognized entity text"
    )
    label: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="E.g. PERSON, ORGANIZATION, LOCATION"
    )
    start_position: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="Character start offset in text"
    )
    end_position: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="Character end offset in text"
    )
    score: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="NER confidence score"
    )
    normalized_label: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Normalized/mapped label if any"
    )

    # Relationship
    analysis: Mapped["Analysis"] = relationship(  # noqa: F821
        "Analysis",
        back_populates="entities",
    )

    # Indexes
    __table_args__ = (
        Index("ix_analysis_entities_text", "text"),
        Index("ix_analysis_entities_label", "label"),
    )

    def __repr__(self) -> str:
        return f"<Entity id={self.id} text={self.text!r} label={self.label!r}>"
