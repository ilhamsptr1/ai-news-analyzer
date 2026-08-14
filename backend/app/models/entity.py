"""
Entity model — stores named entities extracted from an article analysis.
Examples: PERSON, ORGANIZATION, LOCATION, COUNTRY, COMPANY
"""

from sqlalchemy import Float, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Entity(Base):
    __tablename__ = "entities"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Foreign key to Analysis
    analysis_id: Mapped[int] = mapped_column(
        ForeignKey("analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Fields — string types (not DB enum) for flexibility in Phase 3
    entity: Mapped[str] = mapped_column(
        String(500), nullable=False, comment="The recognized entity text"
    )
    entity_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="E.g. PERSON, ORGANIZATION, LOCATION, COUNTRY, COMPANY",
    )
    score: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="NER confidence score"
    )

    # Relationship
    analysis: Mapped["Analysis"] = relationship(  # noqa: F821
        "Analysis",
        back_populates="entities",
    )

    # Indexes
    __table_args__ = (
        Index("ix_entities_entity", "entity"),
        Index("ix_entities_entity_type", "entity_type"),
    )

    def __repr__(self) -> str:
        return f"<Entity id={self.id} entity={self.entity!r} type={self.entity_type!r}>"
