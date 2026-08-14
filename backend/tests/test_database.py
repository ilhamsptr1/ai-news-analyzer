"""
Phase 2 — Database Tests

Tests:
  - Database connection
  - Article CRUD (create, read, list, delete)
  - 404 not found
  - Article → Analysis → Keyword/Entity relationship
  - Phase 1 health endpoint regression
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database import Base, get_db
from app.main import app

# ---------------------------------------------------------------------------
# Test database setup
# Uses a separate test schema / transaction rollback approach to keep the
# development database clean.
# ---------------------------------------------------------------------------

# Re-use the same DB but wrap each test in a transaction that is rolled back.
TEST_DATABASE_URL = settings.database_url

test_engine = create_engine(TEST_DATABASE_URL, echo=False, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(
    bind=test_engine, autocommit=False, autoflush=False, expire_on_commit=False
)


@pytest.fixture(scope="session", autouse=True)
def create_test_tables():
    """Ensure all tables exist before running tests."""
    Base.metadata.create_all(bind=test_engine)
    yield
    # Tables are left intact; data is cleaned per-test below.


@pytest.fixture()
def db_session():
    """
    Provide a database session that is rolled back after each test.
    This keeps the dev database clean.
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db_session):
    """FastAPI test client with DB session overridden to use the test session."""

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SAMPLE_ARTICLE = {
    "title": "Test Article: AI Breakthrough",
    "url": "https://example.com/test-article",
    "source": "Test Source",
    "content": "This is the content of a test article used for database testing.",
}


def create_sample_article(client) -> dict:
    """Helper: POST a sample article and return response JSON."""
    response = client.post("/api/articles", json=SAMPLE_ARTICLE)
    assert response.status_code == 201
    return response.json()


# ===========================================================================
# PHASE 1 REGRESSION — Health endpoint must still work
# ===========================================================================


class TestPhase1Regression:
    def test_health_returns_200(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_health_response_has_status(self, client):
        response = client.get("/api/health")
        assert "status" in response.json()

    def test_health_response_has_service(self, client):
        response = client.get("/api/health")
        assert "service" in response.json()

    def test_health_status_is_ok(self, client):
        response = client.get("/api/health")
        assert response.json()["status"] == "ok"

    def test_health_service_name(self, client):
        response = client.get("/api/health")
        assert response.json()["service"] == "AI News Analyzer API"


# ===========================================================================
# DATABASE CONNECTION
# ===========================================================================


class TestDatabaseConnection:
    def test_can_connect_to_postgresql(self):
        """Verify that the engine can execute a simple query."""
        with test_engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1

    def test_tables_exist(self):
        """Verify all required tables were created by Alembic."""
        with test_engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'public'"
                )
            )
            tables = {row[0] for row in result}
        assert "articles" in tables
        assert "analyses" in tables
        assert "analysis_keywords" in tables
        assert "analysis_entities" in tables
        assert "alembic_version" in tables


# ===========================================================================
# CREATE ARTICLE
# ===========================================================================


class TestCreateArticle:
    def test_create_article_returns_201(self, client):
        response = client.post("/api/articles", json=SAMPLE_ARTICLE)
        assert response.status_code == 201

    def test_create_article_response_has_id(self, client):
        data = create_sample_article(client)
        assert "id" in data
        assert isinstance(data["id"], int)

    def test_create_article_title_matches(self, client):
        data = create_sample_article(client)
        assert data["title"] == SAMPLE_ARTICLE["title"]

    def test_create_article_content_matches(self, client):
        data = create_sample_article(client)
        assert data["content"] == SAMPLE_ARTICLE["content"]

    def test_create_article_url_matches(self, client):
        data = create_sample_article(client)
        assert data["url"] == SAMPLE_ARTICLE["url"]

    def test_create_article_source_matches(self, client):
        data = create_sample_article(client)
        assert data["source"] == SAMPLE_ARTICLE["source"]

    def test_create_article_has_timestamps(self, client):
        data = create_sample_article(client)
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_article_without_url(self, client):
        """url is nullable — article can be created with raw text only."""
        payload = {
            "title": "Text-only Article",
            "content": "Pasted text content without a URL.",
        }
        response = client.post("/api/articles", json=payload)
        assert response.status_code == 201
        assert response.json()["url"] is None

    def test_create_article_missing_title_returns_422(self, client):
        payload = {"content": "Some content without a title."}
        response = client.post("/api/articles", json=payload)
        assert response.status_code == 422

    def test_create_article_missing_content_returns_422(self, client):
        payload = {"title": "Title without content"}
        response = client.post("/api/articles", json=payload)
        assert response.status_code == 422

    def test_create_article_empty_content_returns_422(self, client):
        payload = {"title": "Title", "content": "short"}  # less than 10 chars
        response = client.post("/api/articles", json=payload)
        assert response.status_code == 422


# ===========================================================================
# GET ARTICLE BY ID
# ===========================================================================


class TestGetArticle:
    def test_get_article_returns_200(self, client):
        created = create_sample_article(client)
        response = client.get(f"/api/articles/{created['id']}")
        assert response.status_code == 200

    def test_get_article_data_matches(self, client):
        created = create_sample_article(client)
        response = client.get(f"/api/articles/{created['id']}")
        data = response.json()
        assert data["id"] == created["id"]
        assert data["title"] == SAMPLE_ARTICLE["title"]
        assert data["content"] == SAMPLE_ARTICLE["content"]

    def test_get_article_not_found_returns_404(self, client):
        response = client.get("/api/articles/999999")
        assert response.status_code == 404

    def test_get_article_not_found_has_detail(self, client):
        response = client.get("/api/articles/999999")
        assert "detail" in response.json()


# ===========================================================================
# LIST ARTICLES
# ===========================================================================


class TestListArticles:
    def test_list_articles_returns_200(self, client):
        response = client.get("/api/articles")
        assert response.status_code == 200

    def test_list_articles_response_structure(self, client):
        response = client.get("/api/articles")
        data = response.json()
        assert "total" in data
        assert "articles" in data
        assert isinstance(data["articles"], list)

    def test_list_articles_includes_created(self, client):
        created = create_sample_article(client)
        response = client.get("/api/articles")
        ids = [a["id"] for a in response.json()["articles"]]
        assert created["id"] in ids

    def test_list_articles_total_increments(self, client):
        before = client.get("/api/articles").json()["total"]
        create_sample_article(client)
        after = client.get("/api/articles").json()["total"]
        assert after == before + 1

    def test_list_articles_pagination_skip(self, client):
        response = client.get("/api/articles?skip=0&limit=5")
        assert response.status_code == 200
        assert len(response.json()["articles"]) <= 5

    def test_list_articles_invalid_limit_returns_422(self, client):
        response = client.get("/api/articles?limit=0")
        assert response.status_code == 422


# ===========================================================================
# DELETE ARTICLE
# ===========================================================================


class TestDeleteArticle:
    def test_delete_article_returns_204(self, client):
        created = create_sample_article(client)
        response = client.delete(f"/api/articles/{created['id']}")
        assert response.status_code == 204

    def test_delete_article_is_gone(self, client):
        created = create_sample_article(client)
        client.delete(f"/api/articles/{created['id']}")
        response = client.get(f"/api/articles/{created['id']}")
        assert response.status_code == 404

    def test_delete_nonexistent_article_returns_404(self, client):
        response = client.delete("/api/articles/999999")
        assert response.status_code == 404


# ===========================================================================
# RELATIONSHIPS — Article → Analysis → Keyword / Entity
# ===========================================================================


class TestRelationships:
    def test_article_analysis_relationship(self, db_session, client):
        """Create article then manually create analysis via DB — verify FK works."""
        from app.models.analysis import Analysis
        from app.models.article import Article

        article = Article(title="Relationship Test", content="Content for relationship test article.")
        db_session.add(article)
        db_session.flush()

        analysis = Analysis(
            article_id=article.id,
            sentiment="positive",
            word_count=5,
        )
        db_session.add(analysis)
        db_session.flush()

        # Relationship access
        assert analysis.article_id == article.id
        assert analysis.article.title == "Relationship Test"

    def test_analysis_keyword_relationship(self, db_session):
        """Verify Analysis → Keyword FK relationship."""
        from app.models.analysis import Analysis
        from app.models.article import Article
        from app.models.keyword import Keyword

        article = Article(title="Keyword Test", content="Content for keyword relationship test.")
        db_session.add(article)
        db_session.flush()

        analysis = Analysis(article_id=article.id, word_count=4)
        db_session.add(analysis)
        db_session.flush()

        keyword = Keyword(analysis_id=analysis.id, keyword="artificial intelligence", score=0.95)
        db_session.add(keyword)
        db_session.flush()

        assert keyword.analysis_id == analysis.id
        assert keyword.keyword == "artificial intelligence"
        assert keyword.score == pytest.approx(0.95)

    def test_analysis_entity_relationship(self, db_session):
        """Verify Analysis → Entity FK relationship."""
        from app.models.analysis import Analysis
        from app.models.article import Article
        from app.models.entity import Entity

        article = Article(title="Entity Test", content="Content for entity relationship test article.")
        db_session.add(article)
        db_session.flush()

        analysis = Analysis(article_id=article.id, word_count=4)
        db_session.add(analysis)
        db_session.flush()

        entity = Entity(
            analysis_id=analysis.id,
            text="OpenAI",
            label="ORGANIZATION",
            start_position=0,
            end_position=6,
            score=0.99,
        )
        db_session.add(entity)
        db_session.flush()

        assert entity.analysis_id == analysis.id
        assert entity.text == "OpenAI"
        assert entity.label == "ORGANIZATION"

    def test_cascade_delete_article_deletes_analysis(self, db_session):
        """Deleting article must cascade-delete its analyses."""
        from app.models.analysis import Analysis
        from app.models.article import Article

        article = Article(title="Cascade Test", content="Content for cascade delete test article.")
        db_session.add(article)
        db_session.flush()

        analysis = Analysis(article_id=article.id)
        db_session.add(analysis)
        db_session.flush()
        analysis_id = analysis.id

        db_session.delete(article)
        db_session.flush()

        # Analysis must be gone due to CASCADE
        assert db_session.get(Analysis, analysis_id) is None

    def test_cascade_delete_analysis_deletes_keywords(self, db_session):
        """Deleting analysis must cascade-delete its keywords."""
        from app.models.analysis import Analysis
        from app.models.article import Article
        from app.models.keyword import Keyword

        article = Article(title="Cascade Keyword Test", content="Content for cascade keyword delete test.")
        db_session.add(article)
        db_session.flush()

        analysis = Analysis(article_id=article.id)
        db_session.add(analysis)
        db_session.flush()

        keyword = Keyword(analysis_id=analysis.id, keyword="test_keyword")
        db_session.add(keyword)
        db_session.flush()
        keyword_id = keyword.id

        db_session.delete(analysis)
        db_session.flush()

        assert db_session.get(Keyword, keyword_id) is None
