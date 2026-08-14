"""
Phase 4B-2 Tests — Keyword Extraction

Test groups:
    1. Text cleaning
    2. Keyword quality filtering
    3. TF-IDF extractor
    4. KeywordExtractor (YAKE primary)
    5. Fallback mechanism
    6. API endpoint
    7. Performance
    8. Phase 1-3 + 4A + 4B-1 regression
"""

import time
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings
from app.database import Base, get_db
from app.main import app
from app.ai.keyword_extractor import (
    KeywordExtractor,
    _clean_text,
    _is_valid_keyword,
    _deduplicate,
    MIN_TOP_N,
    MAX_TOP_N,
    MAX_TEXT_LENGTH,
    get_keyword_extractor,
)
from app.ai.tfidf_keyword_extractor import TfidfKeywordExtractor

# ---------------------------------------------------------------------------
# DB fixtures (reuse pattern from other phases)
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
# Sample texts
# ---------------------------------------------------------------------------

SHORT_TEXT = "Apple announced AI."

MEDIUM_TEXT = (
    "Apple announced a new artificial intelligence system for its latest devices. "
    "The machine learning chip is designed to improve Siri and on-device processing. "
    "Chief Executive Tim Cook said the technology will revolutionize the smartphone industry."
)

LONG_TEXT = (
    "The United States Federal Reserve raised interest rates by 25 basis points on Wednesday, "
    "citing persistent inflation and a resilient labor market. Federal Reserve Chairman Jerome Powell "
    "stated that the central bank remains committed to bringing inflation back to its 2% target. "
    "Financial markets reacted with volatility, with the S&P 500 falling 1.2% and the Nasdaq "
    "dropping 1.8%. Economists warn that continued rate hikes could trigger a recession in 2025. "
    "Meanwhile, Treasury yields climbed to their highest levels since 2007, as bond investors "
    "priced in higher-for-longer monetary policy. The housing market has already shown signs of "
    "stress, with mortgage applications falling to a 30-year low. Small businesses are also "
    "feeling the squeeze as borrowing costs rise sharply. The decision was unanimous among the "
    "Federal Open Market Committee members."
) * 5  # repeat to make it long


# ===========================================================================
# 1. TEXT CLEANING TESTS
# ===========================================================================

class TestTextCleaning:
    def test_clean_basic_whitespace(self):
        assert _clean_text("  hello world  ") == "hello world"

    def test_clean_html_tags(self):
        result = _clean_text("<p>News article</p> about AI")
        assert "<p>" not in result
        assert "News article" in result

    def test_clean_html_entities(self):
        result = _clean_text("Apple &amp; Google announced a deal")
        assert "&amp;" not in result

    def test_clean_none_input(self):
        result = _clean_text(None)
        assert isinstance(result, str)

    def test_clean_empty_string(self):
        assert _clean_text("") == ""

    def test_clean_multiple_newlines(self):
        result = _clean_text("Line one\n\n\n\nLine two")
        assert "\n\n\n" not in result


# ===========================================================================
# 2. KEYWORD QUALITY FILTER TESTS
# ===========================================================================

class TestKeywordFiltering:
    def test_valid_keyword(self):
        assert _is_valid_keyword("artificial intelligence") is True

    def test_valid_single_word(self):
        assert _is_valid_keyword("technology") is True

    def test_invalid_empty(self):
        assert _is_valid_keyword("") is False

    def test_invalid_too_short(self):
        assert _is_valid_keyword("ai") is False

    def test_invalid_punctuation_only(self):
        assert _is_valid_keyword("---") is False

    def test_invalid_digits_only(self):
        assert _is_valid_keyword("1234") is False

    def test_invalid_stopword_only(self):
        assert _is_valid_keyword("the and or") is False

    def test_valid_multi_word(self):
        assert _is_valid_keyword("machine learning model") is True


class TestDeduplication:
    def test_dedup_case_insensitive(self):
        items = [
            {"keyword": "AI", "score": 0.1},
            {"keyword": "ai", "score": 0.2},
            {"keyword": "Machine Learning", "score": 0.3},
        ]
        result = _deduplicate(items)
        assert len(result) == 2
        assert result[0]["keyword"] == "AI"  # first occurrence preserved

    def test_dedup_preserves_order(self):
        items = [
            {"keyword": "apple", "score": 0.05},
            {"keyword": "APPLE", "score": 0.1},
            {"keyword": "google", "score": 0.15},
        ]
        result = _deduplicate(items)
        assert result[0]["keyword"] == "apple"
        assert result[1]["keyword"] == "google"


# ===========================================================================
# 3. TF-IDF EXTRACTOR TESTS
# ===========================================================================

class TestTfidfExtractor:
    @pytest.fixture
    def extractor(self):
        return TfidfKeywordExtractor()

    def test_returns_list(self, extractor):
        result = extractor.extract(MEDIUM_TEXT, top_n=5)
        assert isinstance(result, list)

    def test_top_n_respected(self, extractor):
        result = extractor.extract(LONG_TEXT, top_n=5)
        assert len(result) <= 5

    def test_top_10_respected(self, extractor):
        result = extractor.extract(LONG_TEXT, top_n=10)
        assert len(result) <= 10

    def test_each_item_has_keyword(self, extractor):
        result = extractor.extract(MEDIUM_TEXT, top_n=5)
        for item in result:
            assert "keyword" in item
            assert len(item["keyword"]) > 0

    def test_each_item_has_score(self, extractor):
        result = extractor.extract(MEDIUM_TEXT, top_n=5)
        for item in result:
            assert "score" in item
            assert isinstance(item["score"], float)

    def test_score_descending_order(self, extractor):
        """TF-IDF: higher score = higher relevance, should be sorted descending."""
        result = extractor.extract(LONG_TEXT, top_n=10)
        if len(result) > 1:
            scores = [item["score"] for item in result]
            assert scores == sorted(scores, reverse=True), "TF-IDF scores must be descending"

    def test_empty_text(self, extractor):
        result = extractor.extract("", top_n=5)
        assert result == []

    def test_none_input(self, extractor):
        result = extractor.extract(None, top_n=5)
        assert result == []

    def test_short_text_no_crash(self, extractor):
        result = extractor.extract(SHORT_TEXT, top_n=10)
        assert isinstance(result, list)

    def test_no_duplicate_keywords(self, extractor):
        # Text with a repeated term
        text = "machine learning machine learning machine learning applied to news analysis and news reporting"
        result = extractor.extract(text, top_n=10)
        kw_lower = [item["keyword"].lower() for item in result]
        assert len(kw_lower) == len(set(kw_lower)), "Duplicate keywords found in TF-IDF output"


# ===========================================================================
# 4. KEYWORD EXTRACTOR (YAKE) TESTS
# ===========================================================================

class TestKeywordExtractor:
    @pytest.fixture
    def extractor(self):
        return KeywordExtractor()

    def test_returns_dict(self, extractor):
        result = extractor.extract(MEDIUM_TEXT)
        assert isinstance(result, dict)

    def test_has_keywords_key(self, extractor):
        result = extractor.extract(MEDIUM_TEXT)
        assert "keywords" in result

    def test_has_method_key(self, extractor):
        result = extractor.extract(MEDIUM_TEXT)
        assert "method" in result

    def test_method_is_yake(self, extractor):
        result = extractor.extract(MEDIUM_TEXT)
        assert result["method"] == "yake"

    def test_keywords_is_list(self, extractor):
        result = extractor.extract(MEDIUM_TEXT)
        assert isinstance(result["keywords"], list)

    def test_each_keyword_has_keyword_field(self, extractor):
        result = extractor.extract(MEDIUM_TEXT)
        for item in result["keywords"]:
            assert "keyword" in item
            assert len(item["keyword"]) >= 1

    def test_each_keyword_has_score_field(self, extractor):
        result = extractor.extract(MEDIUM_TEXT)
        for item in result["keywords"]:
            assert "score" in item
            assert isinstance(item["score"], float)

    def test_yake_score_ascending(self, extractor):
        """YAKE: lower score = higher relevance, sorted ascending."""
        result = extractor.extract(LONG_TEXT, top_n=10)
        scores = [item["score"] for item in result["keywords"]]
        if len(scores) > 1:
            assert scores == sorted(scores), "YAKE scores must be ascending"

    def test_top_n_5(self, extractor):
        result = extractor.extract(LONG_TEXT, top_n=5)
        assert len(result["keywords"]) <= 5

    def test_top_n_10(self, extractor):
        result = extractor.extract(LONG_TEXT, top_n=10)
        assert len(result["keywords"]) <= 10

    def test_top_n_validation_zero_raises(self, extractor):
        with pytest.raises(ValueError):
            extractor.extract(MEDIUM_TEXT, top_n=0)

    def test_top_n_validation_negative_raises(self, extractor):
        with pytest.raises(ValueError):
            extractor.extract(MEDIUM_TEXT, top_n=-1)

    def test_top_n_validation_too_large_raises(self, extractor):
        with pytest.raises(ValueError):
            extractor.extract(MEDIUM_TEXT, top_n=MAX_TOP_N + 1)

    def test_empty_text_returns_empty_list(self, extractor):
        result = extractor.extract("")
        assert result["keywords"] == []

    def test_none_text_returns_empty_list(self, extractor):
        result = extractor.extract(None)
        assert result["keywords"] == []

    def test_short_text_no_crash(self, extractor):
        result = extractor.extract(SHORT_TEXT)
        assert isinstance(result["keywords"], list)
        # May return fewer than top_n keywords — that is expected

    def test_no_duplicate_keywords(self, extractor):
        text = (
            "Artificial Intelligence and artificial intelligence research. "
            "AI systems, AI models, and machine learning AI applications."
        )
        result = extractor.extract(text, top_n=10)
        kw_lower = [item["keyword"].lower() for item in result["keywords"]]
        assert len(kw_lower) == len(set(kw_lower)), "Duplicate keywords in YAKE output"

    def test_text_too_long_raises(self, extractor):
        too_long = "a" * (MAX_TEXT_LENGTH + 1)
        with pytest.raises(ValueError, match="maximum length"):
            extractor.extract(too_long)

    def test_singleton_same_instance(self):
        e1 = get_keyword_extractor()
        e2 = get_keyword_extractor()
        assert e1 is e2


# ===========================================================================
# 5. FALLBACK MECHANISM TEST
# ===========================================================================

class TestFallback:
    @pytest.fixture
    def extractor(self):
        return KeywordExtractor()

    def test_fallback_to_tfidf_when_yake_raises(self, extractor):
        """When YAKE's _extract_yake raises an exception, TF-IDF fallback is used."""
        # yake is lazily imported inside _extract_yake, so we patch _extract_yake directly
        with patch.object(extractor, "_extract_yake", side_effect=RuntimeError("YAKE crashed")):
            result = extractor.extract(MEDIUM_TEXT, top_n=5)
            assert result["method"] == "tfidf"
            assert isinstance(result["keywords"], list)

    def test_fallback_keywords_not_empty_for_good_text(self, extractor):
        with patch.object(extractor, "_extract_yake", side_effect=RuntimeError("YAKE crashed")):
            result = extractor.extract(MEDIUM_TEXT, top_n=5)
            # TF-IDF on a reasonable text should produce some keywords
            assert len(result["keywords"]) > 0

    def test_fallback_score_descending(self, extractor):
        """When using TF-IDF fallback, scores must be descending."""
        with patch.object(extractor, "_extract_yake", side_effect=RuntimeError("YAKE crashed")):
            result = extractor.extract(LONG_TEXT, top_n=10)
            scores = [item["score"] for item in result["keywords"]]
            if len(scores) > 1:
                assert scores == sorted(scores, reverse=True)


# ===========================================================================
# 6. API ENDPOINT TESTS
# ===========================================================================

class TestKeywordAPI:
    def test_extract_endpoint_exists(self, client):
        response = client.post(
            "/api/keywords/extract",
            json={"text": MEDIUM_TEXT},
        )
        assert response.status_code == 200

    def test_extract_returns_keywords(self, client):
        response = client.post(
            "/api/keywords/extract",
            json={"text": MEDIUM_TEXT},
        )
        data = response.json()
        assert "keywords" in data
        assert isinstance(data["keywords"], list)

    def test_extract_returns_method(self, client):
        response = client.post(
            "/api/keywords/extract",
            json={"text": MEDIUM_TEXT},
        )
        data = response.json()
        assert "method" in data
        assert data["method"] in ("yake", "tfidf")

    def test_extract_returns_total(self, client):
        response = client.post(
            "/api/keywords/extract",
            json={"text": MEDIUM_TEXT},
        )
        data = response.json()
        assert "total" in data
        assert data["total"] == len(data["keywords"])

    def test_extract_returns_note(self, client):
        response = client.post(
            "/api/keywords/extract",
            json={"text": MEDIUM_TEXT},
        )
        data = response.json()
        assert "note" in data
        # Note should mention score is NOT a probability for YAKE
        if data["method"] == "yake":
            assert "NOT" in data["note"] or "not" in data["note"].lower()

    def test_extract_top_n_respected(self, client):
        response = client.post(
            "/api/keywords/extract",
            json={"text": LONG_TEXT, "top_n": 5},
        )
        data = response.json()
        assert len(data["keywords"]) <= 5

    def test_extract_default_top_n_10(self, client):
        response = client.post(
            "/api/keywords/extract",
            json={"text": LONG_TEXT},
        )
        data = response.json()
        assert len(data["keywords"]) <= 10

    def test_extract_empty_text_returns_422(self, client):
        response = client.post(
            "/api/keywords/extract",
            json={"text": ""},
        )
        assert response.status_code == 422

    def test_extract_missing_text_returns_422(self, client):
        response = client.post(
            "/api/keywords/extract",
            json={},
        )
        assert response.status_code == 422

    def test_extract_top_n_zero_returns_422(self, client):
        response = client.post(
            "/api/keywords/extract",
            json={"text": MEDIUM_TEXT, "top_n": 0},
        )
        assert response.status_code == 422

    def test_extract_top_n_negative_returns_422(self, client):
        response = client.post(
            "/api/keywords/extract",
            json={"text": MEDIUM_TEXT, "top_n": -5},
        )
        assert response.status_code == 422

    def test_extract_top_n_too_large_returns_422(self, client):
        response = client.post(
            "/api/keywords/extract",
            json={"text": MEDIUM_TEXT, "top_n": 100},
        )
        assert response.status_code == 422

    def test_extract_whitespace_only_returns_422(self, client):
        response = client.post(
            "/api/keywords/extract",
            json={"text": "   \n\t  "},
        )
        assert response.status_code == 422

    def test_keyword_items_have_keyword_and_score(self, client):
        response = client.post(
            "/api/keywords/extract",
            json={"text": MEDIUM_TEXT},
        )
        for item in response.json()["keywords"]:
            assert "keyword" in item
            assert "score" in item
            assert isinstance(item["score"], float)

    def test_extract_short_text_no_crash(self, client):
        response = client.post(
            "/api/keywords/extract",
            json={"text": SHORT_TEXT},
        )
        assert response.status_code == 200


# ===========================================================================
# 7. PERFORMANCE TEST
# ===========================================================================

class TestPerformance:
    def test_yake_extraction_speed(self):
        """YAKE on a long article should complete within 10 seconds."""
        extractor = KeywordExtractor()
        start = time.time()
        result = extractor.extract(LONG_TEXT, top_n=10)
        elapsed = time.time() - start
        assert elapsed < 10.0, f"YAKE took too long: {elapsed:.2f}s"
        assert isinstance(result["keywords"], list)

    def test_tfidf_extraction_speed(self):
        """TF-IDF fallback on a long article should complete within 10 seconds."""
        extractor = TfidfKeywordExtractor()
        start = time.time()
        result = extractor.extract(LONG_TEXT, top_n=10)
        elapsed = time.time() - start
        assert elapsed < 10.0, f"TF-IDF took too long: {elapsed:.2f}s"
        assert isinstance(result, list)


# ===========================================================================
# 8. PHASE 1-3 + 4A + 4B-1 REGRESSION
# ===========================================================================

class TestRegressionPhase1:
    def test_health_200(self, client):
        assert client.get("/api/health").status_code == 200

    def test_health_status_ok(self, client):
        assert client.get("/api/health").json()["status"] == "ok"

    def test_health_service_name(self, client):
        assert client.get("/api/health").json()["service"] == "AI News Analyzer API"


class TestRegressionPhase2:
    def test_list_articles_200(self, client):
        assert client.get("/api/articles").status_code == 200

    def test_articles_has_structure(self, client):
        data = client.get("/api/articles").json()
        assert "total" in data
        assert "articles" in data

    def test_article_not_found(self, client):
        assert client.get("/api/articles/999999").status_code == 404


class TestRegressionPhase3:
    def test_extract_bad_scheme(self, client):
        assert client.post(
            "/api/articles/extract",
            json={"url": "ftp://example.com/long-path-article"},
        ).status_code == 400

    def test_extract_localhost_blocked(self, client):
        assert client.post(
            "/api/articles/extract",
            json={"url": "http://localhost/internal"},
        ).status_code == 400


class TestRegressionPhase4A:
    def test_category_classifier_importable(self):
        from app.ai.category_classifier import CategoryClassifier
        clf = CategoryClassifier()
        assert not clf.is_loaded()

    def test_category_model_exists(self):
        model_path = Path(__file__).parents[1] / "ml" / "models" / "news_category_model.joblib"
        assert model_path.exists(), "Category model file missing"

    def test_category_predict_works(self):
        from app.ai.category_classifier import get_classifier
        clf = get_classifier()
        result = clf.predict("Apple announced a new artificial intelligence chip.")
        assert result["category"] in {"Business", "Sports", "Technology", "World"}
        assert 0.0 <= result["confidence"] <= 1.0


class TestRegressionPhase4B1:
    def test_sentiment_classifier_importable(self):
        from app.ai.sentiment_classifier import SentimentClassifier
        clf = SentimentClassifier()
        assert not clf.is_loaded()

    def test_sentiment_model_exists(self):
        model_path = Path(__file__).parents[1] / "ml" / "models" / "sentiment_model.joblib"
        assert model_path.exists(), "Sentiment model file missing"

    def test_sentiment_predict_works(self):
        from app.ai.sentiment_classifier import get_sentiment_classifier
        clf = get_sentiment_classifier()
        result = clf.predict("The company reported record profits this year.")
        assert result["sentiment"] in {"Negative", "Neutral", "Positive"}
        assert 0.0 <= result["confidence"] <= 1.0
