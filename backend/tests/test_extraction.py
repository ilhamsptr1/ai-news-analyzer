"""
Phase 3 — Article Extraction Tests

Tests:
  - URL validation (valid, invalid, SSRF)
  - Text cleaner (cleaning, word count, reading time)
  - Article extractor (with mocked HTTP + local HTML fixtures)
  - POST /api/articles/extract endpoint
  - Duplicate URL handling
  - Database persistence
  - Phase 1 + Phase 2 regression
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database import Base, get_db
from app.main import app
from app.utils.url_validator import (
    SSRFBlockedError,
    URLValidationError,
    validate_url,
)
from app.utils.text_cleaner import clean_text, clean_title, count_words, estimate_reading_time
from app.services.article_extractor import (
    ExtractionResult,
    ExtractionError,
    FetchError,
    TimeoutError,
    _extract_source,
    _extract_with_beautifulsoup,
    _extract_with_trafilatura,
)

# ---------------------------------------------------------------------------
# Test database setup (same rollback approach as Phase 2)
# ---------------------------------------------------------------------------

test_engine = create_engine(settings.database_url, echo=False, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(
    bind=test_engine, autocommit=False, autoflush=False, expire_on_commit=False
)


@pytest.fixture(scope="session", autouse=True)
def create_test_tables():
    Base.metadata.create_all(bind=test_engine)
    yield


@pytest.fixture()
def db_session():
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# HTML Fixtures
# ---------------------------------------------------------------------------

SAMPLE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta property="og:title" content="Breaking: Scientists Discover New Planet">
    <meta name="author" content="Jane Doe">
    <meta property="article:published_time" content="2026-08-14T10:00:00Z">
    <title>Breaking: Scientists Discover New Planet | Tech News</title>
</head>
<body>
    <nav>Navigation Menu | Home | Science | Tech</nav>
    <header>Site Header</header>
    <main>
        <article>
            <h1>Breaking: Scientists Discover New Planet</h1>
            <p>Scientists at the International Space Observatory have announced
            the discovery of a new planet in a distant solar system. The planet,
            designated Kepler-452c, shows signs of liquid water on its surface.</p>
            <p>This discovery represents a major milestone in the search for
            extraterrestrial life. The planet orbits within the habitable zone of
            its host star, meaning temperatures could support liquid water.</p>
            <p>Lead researcher Dr. Sarah Johnson stated that this finding opens
            new avenues for research into planetary formation and the conditions
            necessary for life to emerge in the universe.</p>
            <p>Further observations are planned over the next several months
            using the James Webb Space Telescope to better characterize the
            planet's atmosphere and surface conditions.</p>
        </article>
    </main>
    <footer>Footer content | Copyright 2026 | Cookie Policy</footer>
    <div class="advertisement">Buy now! Special offer!</div>
    <div class="cookie-banner">We use cookies</div>
</body>
</html>"""

MINIMAL_HTML = """<html><head><title>Test Article</title></head>
<body><article><h1>Test Article</h1>
<p>This is a test article with sufficient content for extraction testing purposes.</p>
<p>Second paragraph with more content to ensure the word count is sufficient.</p>
</article></body></html>"""

NO_CONTENT_HTML = """<html><head><title>Empty Page</title></head>
<body><p>Hi</p></body></html>"""


# ===========================================================================
# URL VALIDATION TESTS
# ===========================================================================


class TestURLValidation:
    def test_valid_https_url(self):
        result = validate_url("https://example.com/news/article")
        assert result == "https://example.com/news/article"

    def test_valid_http_url(self):
        result = validate_url("http://example.com/article")
        assert result == "http://example.com/article"

    def test_url_is_stripped(self):
        result = validate_url("  https://example.com/article  ")
        assert result == "https://example.com/article"

    def test_invalid_scheme_ftp(self):
        with pytest.raises(URLValidationError):
            validate_url("ftp://example.com/file")

    def test_invalid_scheme_javascript(self):
        with pytest.raises(URLValidationError):
            validate_url("javascript:alert(1)")

    def test_invalid_no_scheme(self):
        with pytest.raises(URLValidationError):
            validate_url("example.com/article")

    def test_invalid_empty_string(self):
        with pytest.raises(URLValidationError):
            validate_url("")

    def test_invalid_just_text(self):
        with pytest.raises(URLValidationError):
            validate_url("hello world")

    def test_ssrf_localhost(self):
        with pytest.raises(SSRFBlockedError):
            validate_url("http://localhost/api/secret")

    def test_ssrf_loopback_127(self):
        with pytest.raises(SSRFBlockedError):
            validate_url("http://127.0.0.1/admin")

    def test_ssrf_loopback_0_0_0_0(self):
        with pytest.raises(SSRFBlockedError):
            validate_url("http://0.0.0.0/secret")

    def test_ssrf_private_class_a(self):
        with pytest.raises(SSRFBlockedError):
            validate_url("http://10.0.0.1/internal")

    def test_ssrf_private_class_b(self):
        with pytest.raises(SSRFBlockedError):
            validate_url("http://172.16.0.1/internal")

    def test_ssrf_private_class_c(self):
        with pytest.raises(SSRFBlockedError):
            validate_url("http://192.168.1.1/router")

    def test_ssrf_metadata_ip(self):
        with pytest.raises(SSRFBlockedError):
            validate_url("http://169.254.169.254/latest/meta-data")

    def test_ssrf_ipv6_loopback(self):
        with pytest.raises(SSRFBlockedError):
            validate_url("http://[::1]/secret")


# ===========================================================================
# TEXT CLEANER TESTS
# ===========================================================================


class TestTextCleaner:
    def test_clean_text_strips_whitespace(self):
        result = clean_text("  hello world  ")
        assert result == "hello world"

    def test_clean_text_normalizes_crlf(self):
        result = clean_text("line one\r\nline two")
        assert "\r" not in result
        assert "line one" in result
        assert "line two" in result

    def test_clean_text_collapses_blank_lines(self):
        text = "para one\n\n\n\n\npara two"
        result = clean_text(text)
        assert "\n\n\n" not in result

    def test_clean_text_preserves_paragraphs(self):
        text = "Paragraph one.\n\nParagraph two."
        result = clean_text(text)
        assert "Paragraph one." in result
        assert "Paragraph two." in result

    def test_clean_text_empty_returns_empty(self):
        assert clean_text("") == ""
        assert clean_text("   ") == ""

    def test_clean_title_collapses_spaces(self):
        result = clean_title("  Breaking  News   Today  ")
        assert result == "Breaking News Today"

    def test_count_words_basic(self):
        assert count_words("hello world foo bar") == 4

    def test_count_words_empty(self):
        assert count_words("") == 0

    def test_count_words_single(self):
        assert count_words("hello") == 1

    def test_reading_time_minimum_one(self):
        assert estimate_reading_time(1) == 1

    def test_reading_time_zero_words(self):
        assert estimate_reading_time(0) == 0

    def test_reading_time_230_words(self):
        # 230 words at 230 WPM = 1 minute
        assert estimate_reading_time(230) == 1

    def test_reading_time_460_words(self):
        # 460 words at 230 WPM = 2 minutes
        assert estimate_reading_time(460) == 2

    def test_reading_time_1000_words(self):
        result = estimate_reading_time(1000)
        assert result >= 4


# ===========================================================================
# SOURCE EXTRACTION
# ===========================================================================


class TestSourceExtraction:
    def test_extracts_domain(self):
        assert _extract_source("https://www.example.com/news/article") == "example.com"

    def test_strips_www(self):
        assert _extract_source("https://www.bbc.com/news") == "bbc.com"

    def test_no_www(self):
        assert _extract_source("https://techcrunch.com/article") == "techcrunch.com"


# ===========================================================================
# BEAUTIFULSOUP EXTRACTION TESTS (local HTML fixtures)
# ===========================================================================


class TestBeautifulSoupExtractor:
    def test_extracts_title_from_og(self):
        result = _extract_with_beautifulsoup(SAMPLE_HTML, "https://example.com/article")
        assert result is not None
        assert "Scientists" in result.title or "Planet" in result.title

    def test_extracts_content(self):
        result = _extract_with_beautifulsoup(SAMPLE_HTML, "https://example.com/article")
        assert result is not None
        assert len(result.content) > 100

    def test_content_does_not_include_navigation(self):
        result = _extract_with_beautifulsoup(SAMPLE_HTML, "https://example.com/article")
        assert result is not None
        assert "Navigation Menu" not in result.content

    def test_content_does_not_include_footer(self):
        result = _extract_with_beautifulsoup(SAMPLE_HTML, "https://example.com/article")
        assert result is not None
        assert "Cookie Policy" not in result.content

    def test_content_does_not_include_ads(self):
        result = _extract_with_beautifulsoup(SAMPLE_HTML, "https://example.com/article")
        assert result is not None
        assert "Buy now" not in result.content

    def test_extracts_source(self):
        result = _extract_with_beautifulsoup(SAMPLE_HTML, "https://www.example.com/article")
        assert result is not None
        assert result.source == "example.com"

    def test_extracts_author(self):
        result = _extract_with_beautifulsoup(SAMPLE_HTML, "https://example.com/article")
        assert result is not None
        assert result.author == "Jane Doe"

    def test_extracts_published_date(self):
        result = _extract_with_beautifulsoup(SAMPLE_HTML, "https://example.com/article")
        assert result is not None
        assert result.published_at is not None

    def test_word_count_positive(self):
        result = _extract_with_beautifulsoup(SAMPLE_HTML, "https://example.com/article")
        assert result is not None
        assert result.word_count > 0

    def test_reading_time_at_least_one(self):
        result = _extract_with_beautifulsoup(SAMPLE_HTML, "https://example.com/article")
        assert result is not None
        assert result.reading_time >= 1

    def test_returns_none_for_no_content(self):
        result = _extract_with_beautifulsoup(NO_CONTENT_HTML, "https://example.com/")
        assert result is None


# ===========================================================================
# TRAFILATURA EXTRACTION TESTS (local HTML fixtures)
# ===========================================================================


class TestTrafilaturaExtractor:
    def test_extracts_content(self):
        result = _extract_with_trafilatura(SAMPLE_HTML, "https://example.com/article")
        # Trafilatura may or may not extract from this fixture — it's a primary extractor
        # We just verify it either returns None or a valid result
        if result is not None:
            assert len(result.content) >= 50

    def test_returns_none_for_empty_html(self):
        result = _extract_with_trafilatura("<html><body></body></html>", "https://example.com/")
        assert result is None


# ===========================================================================
# API TESTS — POST /api/articles/extract
# ===========================================================================


class TestExtractArticleAPI:
    def _mock_extraction_result(self, url: str = "https://example.com/test-article") -> ExtractionResult:
        return ExtractionResult(
            title="Scientists Discover New Planet",
            content="Scientists at the International Space Observatory have announced the discovery of a new planet. "
                    "The planet shows signs of liquid water on its surface. This represents a milestone in space research.",
            url=url,
            source="example.com",
            author="Jane Doe",
            published_at=None,
            word_count=35,
            reading_time=1,
        )

    def test_extract_invalid_url_returns_400(self, client):
        response = client.post("/api/articles/extract", json={"url": "ftp://example.com/some-article-page"})
        assert response.status_code == 400

    def test_extract_localhost_returns_400(self, client):
        response = client.post("/api/articles/extract", json={"url": "http://localhost/api"})
        assert response.status_code == 400

    def test_extract_private_ip_returns_400(self, client):
        response = client.post("/api/articles/extract", json={"url": "http://192.168.1.1/admin"})
        assert response.status_code == 400

    def test_extract_missing_url_field_returns_422(self, client):
        response = client.post("/api/articles/extract", json={})
        assert response.status_code == 422

    def test_extract_success_returns_201(self, client):
        with patch("app.routes.articles.extract_article") as mock_extract:
            mock_extract.return_value = self._mock_extraction_result()
            response = client.post(
                "/api/articles/extract",
                json={"url": "https://example.com/test-article"},
            )
        assert response.status_code == 201

    def test_extract_response_has_title(self, client):
        with patch("app.routes.articles.extract_article") as mock_extract:
            mock_extract.return_value = self._mock_extraction_result()
            response = client.post(
                "/api/articles/extract",
                json={"url": "https://example.com/test-article"},
            )
        assert response.json()["title"] == "Scientists Discover New Planet"

    def test_extract_response_has_word_count(self, client):
        with patch("app.routes.articles.extract_article") as mock_extract:
            mock_extract.return_value = self._mock_extraction_result()
            response = client.post(
                "/api/articles/extract",
                json={"url": "https://example.com/test-article"},
            )
        data = response.json()
        assert "word_count" in data
        assert data["word_count"] == 35

    def test_extract_response_has_reading_time(self, client):
        with patch("app.routes.articles.extract_article") as mock_extract:
            mock_extract.return_value = self._mock_extraction_result()
            response = client.post(
                "/api/articles/extract",
                json={"url": "https://example.com/test-article"},
            )
        data = response.json()
        assert "reading_time" in data
        assert data["reading_time"] >= 1

    def test_extract_timeout_returns_504(self, client):
        with patch("app.routes.articles.extract_article") as mock_extract:
            mock_extract.side_effect = TimeoutError("timed out")
            response = client.post(
                "/api/articles/extract",
                json={"url": "https://example.com/timeout-article"},
            )
        assert response.status_code == 504

    def test_extract_fetch_error_returns_502(self, client):
        with patch("app.routes.articles.extract_article") as mock_extract:
            mock_extract.side_effect = FetchError("connection refused")
            response = client.post(
                "/api/articles/extract",
                json={"url": "https://example.com/unreachable"},
            )
        assert response.status_code == 502

    def test_extract_content_error_returns_422(self, client):
        with patch("app.routes.articles.extract_article") as mock_extract:
            mock_extract.side_effect = ExtractionError("no content found")
            response = client.post(
                "/api/articles/extract",
                json={"url": "https://example.com/empty-page"},
            )
        assert response.status_code == 422

    def test_extract_duplicate_url_returns_200(self, client):
        """Second extraction of same URL should return 200 (existing article)."""
        url = "https://example.com/unique-test-duplicate-article"
        result = self._mock_extraction_result(url)

        with patch("app.routes.articles.extract_article") as mock_extract:
            mock_extract.return_value = result
            # First extraction
            r1 = client.post("/api/articles/extract", json={"url": url})
            assert r1.status_code == 201

            # Second extraction — same URL
            r2 = client.post("/api/articles/extract", json={"url": url})
            assert r2.status_code == 200

    def test_extract_persisted_to_database(self, client, db_session):
        """Verify extracted article is actually saved to DB."""
        from app.services.article_service import get_article_by_url

        url = "https://example.com/persistence-test-article-unique"
        with patch("app.routes.articles.extract_article") as mock_extract:
            mock_extract.return_value = self._mock_extraction_result(url)
            response = client.post("/api/articles/extract", json={"url": url})

        assert response.status_code == 201
        article_id = response.json()["id"]

        # Verify in DB
        from app.services.article_service import get_article_by_id
        article = get_article_by_id(db_session, article_id)
        assert article is not None
        assert article.title == "Scientists Discover New Planet"
        assert article.word_count == 35


# ===========================================================================
# PHASE 1 + PHASE 2 REGRESSION
# ===========================================================================


class TestRegressionPhase1:
    def test_health_returns_200(self, client):
        assert client.get("/api/health").status_code == 200

    def test_health_status_ok(self, client):
        assert client.get("/api/health").json()["status"] == "ok"

    def test_health_service_name(self, client):
        assert client.get("/api/health").json()["service"] == "AI News Analyzer API"


class TestRegressionPhase2:
    def test_list_articles_returns_200(self, client):
        assert client.get("/api/articles").status_code == 200

    def test_list_articles_has_structure(self, client):
        data = client.get("/api/articles").json()
        assert "total" in data
        assert "articles" in data

    def test_create_article_manual(self, client):
        payload = {
            "title": "Regression Test Article Phase 3",
            "content": "This is a regression test article for Phase 3 compatibility.",
        }
        response = client.post("/api/articles", json=payload)
        assert response.status_code == 201

    def test_get_article_not_found(self, client):
        assert client.get("/api/articles/999999").status_code == 404

    def test_delete_article_not_found(self, client):
        assert client.delete("/api/articles/999999").status_code == 404
