"""
Article Service — database operations for articles.
Handles all CRUD operations. Routes delegate business logic here.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.article import Article
from app.schemas.article import ArticleCreate, ArticleUpdate


def create_article(db: Session, payload: ArticleCreate) -> Article:
    """
    Insert a new article into the database.

    Args:
        db: Active database session.
        payload: Validated ArticleCreate schema.

    Returns:
        The newly created Article ORM instance.
    """
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


def get_article_by_id(db: Session, article_id: int) -> Article | None:
    """Return a single article by primary key, or None if not found."""
    return db.get(Article, article_id)


def get_articles(
    db: Session,
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[Article], int]:
    """
    Return a paginated list of articles and the total count.

    Args:
        db: Active database session.
        skip: Number of records to skip (offset).
        limit: Maximum number of records to return.

    Returns:
        Tuple of (articles list, total count).
    """
    count_stmt = select(Article)
    all_articles = db.execute(count_stmt).scalars().all()
    total = len(all_articles)

    stmt = select(Article).order_by(Article.created_at.desc()).offset(skip).limit(limit)
    articles = list(db.execute(stmt).scalars().all())

    return articles, total


def delete_article(db: Session, article_id: int) -> bool:
    """
    Delete an article by ID.

    Returns:
        True if deleted, False if article was not found.
    """
    article = db.get(Article, article_id)
    if article is None:
        return False
    db.delete(article)
    db.commit()
    return True
