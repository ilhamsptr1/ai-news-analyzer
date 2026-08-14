"""Models package — imports all models so Alembic can detect them."""

from app.models.analysis import Analysis
from app.models.article import Article
from app.models.entity import Entity
from app.models.keyword import Keyword

__all__ = ["Article", "Analysis", "Keyword", "Entity"]
