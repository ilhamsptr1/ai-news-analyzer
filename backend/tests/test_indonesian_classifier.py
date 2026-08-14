"""
Phase 4A-ID Tests — Indonesian News Category Classification

Test groups:
    1. Text cleaning (indonesian_preprocess)
    2. Indonesian classifier model loading & inference
    3. Phase 1-4B-2 full regression
"""

import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings
from app.database import Base, get_db
from app.main import app
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ml.scripts.indonesian_preprocess import (
    CATEGORIES,
    LABEL_COLUMN,
    TEXT_COLUMN,
    clean_text,
    preprocess_df,
)
from app.ai.indonesian_category_classifier import (
    IndonesianCategoryClassifier,
    get_indonesian_classifier,
    VALID_CATEGORIES,
)

# ---------------------------------------------------------------------------
# DB fixtures
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
# Sample Indonesian texts
# ---------------------------------------------------------------------------

SAMPLE_EKONOMI = (
    "Pemerintah Indonesia mengumumkan kebijakan baru untuk mendorong pertumbuhan "
    "ekonomi nasional. Bank Indonesia juga menurunkan suku bunga acuan guna merangsang "
    "investasi dan konsumsi masyarakat. Kementerian Keuangan berharap pertumbuhan GDP "
    "mencapai 5 persen tahun ini."
)

SAMPLE_OLAHRAGA = (
    "Timnas Indonesia berhasil mengalahkan Vietnam 3-0 dalam pertandingan kualifikasi "
    "Piala Dunia 2026 yang berlangsung di Stadion Gelora Bung Karno. Garuda Muda "
    "tampil dominan dengan tiga gol dari striker muda berbakat."
)

SAMPLE_TEKNOLOGI = (
    "Perusahaan teknologi asal Indonesia meluncurkan aplikasi kecerdasan buatan baru "
    "yang dapat membantu petani mengoptimalkan hasil panen. Aplikasi ini menggunakan "
    "machine learning untuk menganalisis kondisi tanah dan cuaca secara real-time."
)

SAMPLE_POLITIK = (
    "Presiden Republik Indonesia mengadakan rapat kabinet untuk membahas kebijakan "
    "strategis nasional. DPR RI juga menyetujui rancangan undang-undang baru yang "
    "berkaitan dengan reformasi birokrasi pemerintahan."
)


# ===========================================================================
# 1. TEXT CLEANING TESTS
# ===========================================================================

class TestIndonesianTextCleaning:
    def test_clean_basic_whitespace(self):
        assert clean_text("  pemerintah Indonesia  ") == "pemerintah Indonesia"

    def test_clean_html_tags(self):
        result = clean_text("<p>Berita terbaru</p> tentang ekonomi")
        assert "<p>" not in result
        assert "Berita terbaru" in result

    def test_clean_html_entities(self):
        result = clean_text("Ekspor &amp; Impor naik")
        assert "&amp;" not in result

    def test_clean_none_input(self):
        result = clean_text(None)
        assert isinstance(result, str)

    def test_clean_empty_string(self):
        assert clean_text("") == ""

    def test_clean_preserves_negation_words(self):
        """Negation words (tidak, bukan, belum) must be preserved."""
        text = "Pemerintah tidak akan menaikkan pajak"
        result = clean_text(text)
        assert "tidak" in result
        assert "pajak" in result

    def test_clean_unicode_normalization(self):
        """Unicode NFC normalization should work."""
        # composed vs decomposed form
        text = "caf\u00e9"  # precomposed
        result = clean_text(text)
        assert "caf" in result

    def test_clean_control_chars_removed(self):
        text = "Berita\x00penting\x1Ftentang ekonomi"
        result = clean_text(text)
        assert "\x00" not in result
        assert "\x1f" not in result

    def test_preprocess_df_output_columns(self):
        df = pd.DataFrame({
            "title": ["Ekonomi Indonesia tumbuh 5 persen"],
            "content": ["Bank Indonesia memperkirakan pertumbuhan ekonomi yang baik tahun ini."],
            "label": ["EKONOMI_BISNIS"],
        })
        cleaned = preprocess_df(df)
        assert TEXT_COLUMN in cleaned.columns
        assert LABEL_COLUMN in cleaned.columns

    def test_preprocess_df_invalid_label_dropped(self):
        df = pd.DataFrame({
            "title": ["Berita ekonomi", "Berita tidak valid"],
            "content": ["Isi berita ekonomi", "Isi berita tidak valid"],
            "label": ["EKONOMI_BISNIS", "KATEGORI_TIDAK_ADA"],
        })
        cleaned = preprocess_df(df)
        assert len(cleaned) == 1
        assert cleaned.iloc[0][LABEL_COLUMN] == "EKONOMI_BISNIS"

    def test_preprocess_df_removes_duplicates(self):
        same_text = "Ini adalah berita yang sama persis tentang ekonomi Indonesia."
        df = pd.DataFrame({
            "title": [same_text, same_text],
            "content": ["", ""],
            "label": ["EKONOMI_BISNIS", "OLAHRAGA"],
        })
        cleaned = preprocess_df(df)
        assert len(cleaned) == 1

    def test_preprocess_df_no_missing_text_or_label(self):
        df = pd.DataFrame({
            "title": ["Pemerintah umumkan kebijakan baru tentang ekonomi"],
            "content": ["Kebijakan ekonomi baru dirilis pemerintah untuk mendorong pertumbuhan."],
            "label": ["EKONOMI_BISNIS"],
        })
        cleaned = preprocess_df(df)
        assert cleaned[TEXT_COLUMN].isna().sum() == 0
        assert cleaned[LABEL_COLUMN].isna().sum() == 0


# ===========================================================================
# 2. INDONESIAN CLASSIFIER TESTS
# ===========================================================================

class TestIndonesianClassifier:
    @pytest.fixture(autouse=True)
    def skip_if_no_model(self):
        model_path = Path(__file__).parents[1] / "ml" / "models" / "news_category_id_model.joblib"
        if not model_path.exists():
            pytest.skip("Indonesian model not yet trained")

    @pytest.fixture
    def clf(self):
        return get_indonesian_classifier()

    def test_model_file_exists(self):
        model_path = Path(__file__).parents[1] / "ml" / "models" / "news_category_id_model.joblib"
        assert model_path.exists()

    def test_metadata_file_exists(self):
        meta_path = Path(__file__).parents[1] / "ml" / "models" / "news_category_id_metadata.json"
        assert meta_path.exists()

    def test_metadata_has_required_fields(self):
        import json
        meta_path = Path(__file__).parents[1] / "ml" / "models" / "news_category_id_metadata.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        assert "language" in meta
        assert meta["language"] == "id"
        assert "categories" in meta
        assert "accuracy" in meta
        assert "macro_f1" in meta
        assert "label_origin" in meta

    def test_metadata_accuracy_reasonable(self):
        import json
        meta_path = Path(__file__).parents[1] / "ml" / "models" / "news_category_id_metadata.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        # Even with LLM labels, expect at least 60%
        assert meta["accuracy"] >= 0.60, f"Accuracy too low: {meta['accuracy']}"

    def test_singleton_same_instance(self):
        c1 = get_indonesian_classifier()
        c2 = get_indonesian_classifier()
        assert c1 is c2

    def test_predict_returns_dict(self, clf):
        result = clf.predict(SAMPLE_EKONOMI)
        assert isinstance(result, dict)

    def test_predict_has_category_key(self, clf):
        result = clf.predict(SAMPLE_EKONOMI)
        assert "category" in result

    def test_predict_has_confidence_key(self, clf):
        result = clf.predict(SAMPLE_EKONOMI)
        assert "confidence" in result

    def test_predict_has_all_scores_key(self, clf):
        result = clf.predict(SAMPLE_EKONOMI)
        assert "all_scores" in result

    def test_predict_category_is_valid(self, clf):
        for sample in [SAMPLE_EKONOMI, SAMPLE_OLAHRAGA, SAMPLE_TEKNOLOGI, SAMPLE_POLITIK]:
            result = clf.predict(sample)
            assert result["category"] in VALID_CATEGORIES, \
                f"Unexpected category: {result['category']}"

    def test_predict_confidence_in_range(self, clf):
        result = clf.predict(SAMPLE_EKONOMI)
        assert 0.0 <= result["confidence"] <= 1.0

    def test_predict_all_scores_sum_to_one(self, clf):
        result = clf.predict(SAMPLE_EKONOMI)
        total = sum(result["all_scores"].values())
        assert abs(total - 1.0) < 0.01

    def test_predict_all_scores_keys_valid(self, clf):
        result = clf.predict(SAMPLE_EKONOMI)
        for key in result["all_scores"]:
            assert key in VALID_CATEGORIES

    def test_predict_empty_raises(self, clf):
        with pytest.raises(ValueError):
            clf.predict("")

    def test_predict_too_short_raises(self, clf):
        with pytest.raises(ValueError):
            clf.predict("ok")

    def test_predict_batch_returns_list(self, clf):
        results = clf.predict_batch([SAMPLE_EKONOMI, SAMPLE_OLAHRAGA])
        assert isinstance(results, list)
        assert len(results) == 2

    def test_predict_batch_each_valid(self, clf):
        results = clf.predict_batch([SAMPLE_EKONOMI, SAMPLE_TEKNOLOGI, SAMPLE_POLITIK])
        for r in results:
            assert r["category"] in VALID_CATEGORIES

    def test_metadata_property(self, clf):
        meta = clf.metadata
        assert "language" in meta
        assert meta["language"] == "id"

    def test_categories_property(self, clf):
        cats = clf.categories
        assert len(cats) == len(VALID_CATEGORIES)

    def test_performance_single_prediction(self, clf):
        """Single prediction should complete within 2 seconds."""
        start = time.time()
        clf.predict(SAMPLE_EKONOMI)
        elapsed = time.time() - start
        assert elapsed < 2.0, f"Prediction too slow: {elapsed:.2f}s"

    def test_performance_batch_prediction(self, clf):
        """Batch prediction of 10 samples should complete within 5 seconds."""
        samples = [SAMPLE_EKONOMI, SAMPLE_OLAHRAGA, SAMPLE_TEKNOLOGI, SAMPLE_POLITIK] * 3
        start = time.time()
        clf.predict_batch(samples[:10])
        elapsed = time.time() - start
        assert elapsed < 5.0, f"Batch prediction too slow: {elapsed:.2f}s"


# ===========================================================================
# 3. PHASE 1-4B-2 FULL REGRESSION
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
            json={"url": "ftp://example.com/article"},
        ).status_code == 400

    def test_extract_localhost_blocked(self, client):
        assert client.post(
            "/api/articles/extract",
            json={"url": "http://localhost/internal"},
        ).status_code == 400


class TestRegressionPhase4A:
    def test_category_model_exists(self):
        model_path = Path(__file__).parents[1] / "ml" / "models" / "news_category_model.joblib"
        assert model_path.exists(), "English Category model missing"

    def test_category_predict_works(self):
        from app.ai.category_classifier import get_classifier
        clf = get_classifier()
        result = clf.predict("Apple announced a new artificial intelligence chip.")
        assert result["category"] in {"Business", "Sports", "Technology", "World"}


class TestRegressionPhase4B1:
    def test_sentiment_model_exists(self):
        model_path = Path(__file__).parents[1] / "ml" / "models" / "sentiment_model.joblib"
        assert model_path.exists(), "Sentiment model missing"

    def test_sentiment_predict_works(self):
        from app.ai.sentiment_classifier import get_sentiment_classifier
        clf = get_sentiment_classifier()
        result = clf.predict("The company reported record profits this year.")
        assert result["sentiment"] in {"Negative", "Neutral", "Positive"}


class TestRegressionPhase4B2:
    def test_keyword_extraction_works(self, client):
        response = client.post(
            "/api/keywords/extract",
            json={"text": "Apple announced artificial intelligence chip for its devices."},
        )
        assert response.status_code == 200
        data = response.json()
        assert "keywords" in data
        assert data["method"] in ("yake", "tfidf")

    def test_keyword_route_registered(self, client):
        # Confirm route exists
        assert client.post(
            "/api/keywords/extract",
            json={"text": "Pemerintah Indonesia mengumumkan kebijakan ekonomi baru."},
        ).status_code == 200
