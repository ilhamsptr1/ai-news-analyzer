"""
Article Service — database operations for articles.
Handles CRUD + extraction + duplicate URL logic.
"""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.article import Article
from app.schemas.article import ArticleCreate
from app.services.article_extractor import ExtractionResult


# ---------------------------------------------------------------------------
# CRUD helpers
# ---------------------------------------------------------------------------


def create_article(db: Session, payload: ArticleCreate) -> Article:
    """Insert a new article from a manual payload."""
    article = Article(
        title=payload.title,
        url=payload.url,
        source=payload.source,
        content=payload.content,
        published_at=payload.published_at,
    )
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


def create_article_from_extraction(
    db: Session, result: ExtractionResult
) -> tuple[Article, bool]:
    """
    Save an ExtractionResult to the database.

    Handles duplicate URL:
    - If URL already exists → returns existing article + created=False
    - If URL is new → inserts, returns new article + created=True

    Returns:
        Tuple of (Article, created: bool).
    """
    # Check for existing article with same URL
    existing = get_article_by_url(db, result.url)
    if existing:
        return existing, False

    article = Article(
        title=result.title,
        url=result.url,
        source=result.source,
        content=result.content,
        author=result.author,
        published_at=result.published_at,
        word_count=result.word_count,
        reading_time=result.reading_time,
    )
    db.add(article)
    try:
        db.commit()
        db.refresh(article)
        return article, True
    except IntegrityError:
        db.rollback()
        # Race condition: another request saved the same URL first
        existing = get_article_by_url(db, result.url)
        if existing:
            return existing, False
        raise


def get_article_by_id(db: Session, article_id: int) -> Article | None:
    """Return a single article by primary key, or None if not found."""
    return db.get(Article, article_id)


def get_article_by_url(db: Session, url: str) -> Article | None:
    """Return an article by URL, or None if not found."""
    stmt = select(Article).where(Article.url == url)
    return db.execute(stmt).scalar_one_or_none()


def get_articles(
    db: Session,
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[Article], int]:
    """Return paginated list of articles and total count."""
    total_stmt = select(Article)
    total = len(db.execute(total_stmt).scalars().all())

    stmt = select(Article).order_by(Article.created_at.desc()).offset(skip).limit(limit)
    articles = list(db.execute(stmt).scalars().all())
    return articles, total


def delete_article(db: Session, article_id: int) -> bool:
    """Delete article by ID. Returns True if deleted, False if not found."""
    article = db.get(Article, article_id)
    if article is None:
        return False
    db.delete(article)
    db.commit()
    return True
