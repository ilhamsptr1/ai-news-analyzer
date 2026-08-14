"""
Phase 4A Tests — News Category Classifier

Test groups:
  1. Dataset / preprocessing (offline — no internet needed for unit tests)
  2. Model loading
  3. Inference validation
  4. Phase 1, 2, 3 regression
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure backend/ on path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# ---------------------------------------------------------------------------
# Test fixtures — reuse existing DB client setup
# ---------------------------------------------------------------------------
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.config import settings
from app.database import Base, get_db
from app.main import app
from ml.scripts.preprocess import (
    CATEGORIES,
    LABEL_COLUMN,
    LABEL_MAP,
    TEXT_COLUMN,
    clean_text,
    preprocess_df,
)

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


# ===========================================================================
# 1. PREPROCESSING TESTS (no internet, no model needed)
# ===========================================================================


class TestTextCleaning:
    def test_clean_text_basic(self):
        assert clean_text("  hello world  ") == "hello world"

    def test_clean_text_html_removed(self):
        result = clean_text("<p>News article content</p>")
        assert "<p>" not in result
        assert "News article content" in result

    def test_clean_text_html_entities(self):
        result = clean_text("AT&amp;T announces &quot;new deal&quot;")
        assert "&amp;" not in result

    def test_clean_text_whitespace_normalized(self):
        result = clean_text("Tech   news\n\nfrom   Apple")
        assert "  " not in result
        assert "Tech" in result

    def test_clean_text_none_handled(self):
        result = clean_text(None)
        assert isinstance(result, str)

    def test_clean_text_non_string_handled(self):
        result = clean_text(12345)
        assert isinstance(result, str)

    def test_clean_text_empty(self):
        assert clean_text("") == ""

    def test_clean_text_unicode_normalized(self):
        # NFC normalization shouldn't crash
        result = clean_text("caf\u00e9")
        assert isinstance(result, str)


class TestLabelMapping:
    def test_label_map_has_four_entries(self):
        assert len(LABEL_MAP) == 4

    def test_label_map_keys_are_ints(self):
        assert all(isinstance(k, int) for k in LABEL_MAP)

    def test_label_map_values(self):
        assert set(LABEL_MAP.values()) == {"World", "Sports", "Business", "Technology"}

    def test_categories_sorted(self):
        assert CATEGORIES == sorted(CATEGORIES)

    def test_categories_match_label_map(self):
        assert set(CATEGORIES) == set(LABEL_MAP.values())


class TestPreprocessDf:
    """Tests using synthetic DataFrames — no internet required."""

    def _make_df(self, n: int = 20):
        import pandas as pd
        import numpy as np
        rng = np.random.default_rng(42)
        labels = rng.integers(0, 4, n)
        texts = [
            f"This is a sample news article about topic {i} with enough words to pass the filter."
            for i in range(n)
        ]
        return pd.DataFrame({"text": texts, "label": labels})

    def test_preprocessed_has_text_column(self):
        df = preprocess_df(self._make_df())
        assert TEXT_COLUMN in df.columns

    def test_preprocessed_has_label_column(self):
        df = preprocess_df(self._make_df())
        assert LABEL_COLUMN in df.columns

    def test_no_missing_labels_after_preprocess(self):
        df = preprocess_df(self._make_df())
        assert df[LABEL_COLUMN].isna().sum() == 0

    def test_no_missing_text_after_preprocess(self):
        df = preprocess_df(self._make_df())
        assert df[TEXT_COLUMN].isna().sum() == 0

    def test_all_labels_valid(self):
        df = preprocess_df(self._make_df())
        assert set(df[LABEL_COLUMN].unique()).issubset(set(LABEL_MAP.values()))

    def test_duplicate_texts_removed(self):
        import pandas as pd
        # Create 10 rows with 5 duplicate texts
        texts = ["Duplicate news article text for testing purposes."] * 5 + [
            f"Unique article number {i} about politics and economy." for i in range(5)
        ]
        labels = [0, 1, 2, 3, 0, 1, 2, 3, 0, 1]
        df = pd.DataFrame({"text": texts, "label": labels})
        cleaned = preprocess_df(df)
        assert cleaned[TEXT_COLUMN].duplicated().sum() == 0

    def test_only_two_columns_returned(self):
        df = preprocess_df(self._make_df())
        assert list(df.columns) == [TEXT_COLUMN, LABEL_COLUMN]

    def test_short_texts_removed(self):
        import pandas as pd
        df = pd.DataFrame({"text": ["Hi", "A", ""], "label": [0, 1, 2]})
        cleaned = preprocess_df(df)
        # All texts are too short (< 10 chars) — should be empty or only valid ones
        assert all(len(t) > 10 for t in cleaned[TEXT_COLUMN])


# ===========================================================================
# 2. MODEL LOADING TEST
# ===========================================================================


class TestModelLoading:
    def test_model_file_exists(self):
        model_path = Path(__file__).parent.parent / "ml" / "models" / "news_category_model.joblib"
        assert model_path.exists(), (
            f"Model not found at {model_path}. "
            "Run: python ml/scripts/train_classifier.py"
        )

    def test_metadata_file_exists(self):
        meta_path = Path(__file__).parent.parent / "ml" / "models" / "model_metadata.json"
        assert meta_path.exists(), "model_metadata.json not found"

    def test_metadata_has_required_fields(self):
        import json
        meta_path = Path(__file__).parent.parent / "ml" / "models" / "model_metadata.json"
        if not meta_path.exists():
            pytest.skip("Metadata file not yet generated")
        meta = json.loads(meta_path.read_text())
        assert "model_name" in meta
        assert "categories" in meta
        assert "accuracy" in meta
        assert "macro_f1" in meta
        assert "weighted_f1" in meta
        assert "version" in meta

    def test_metadata_categories_valid(self):
        import json
        meta_path = Path(__file__).parent.parent / "ml" / "models" / "model_metadata.json"
        if not meta_path.exists():
            pytest.skip("Metadata file not yet generated")
        meta = json.loads(meta_path.read_text())
        assert len(meta["categories"]) >= 4

    def test_metadata_accuracy_reasonable(self):
        import json
        meta_path = Path(__file__).parent.parent / "ml" / "models" / "model_metadata.json"
        if not meta_path.exists():
            pytest.skip("Metadata file not yet generated")
        meta = json.loads(meta_path.read_text())
        assert meta["accuracy"] > 0.5, "Accuracy suspiciously low"
        assert meta["accuracy"] <= 1.0, "Accuracy > 1.0 is impossible"

    def test_classifier_can_be_instantiated(self):
        model_path = Path(__file__).parent.parent / "ml" / "models" / "news_category_model.joblib"
        if not model_path.exists():
            pytest.skip("Model not yet trained")
        from app.ai.category_classifier import CategoryClassifier
        clf = CategoryClassifier()
        assert not clf.is_loaded()

    def test_classifier_loads_on_first_predict(self):
        model_path = Path(__file__).parent.parent / "ml" / "models" / "news_category_model.joblib"
        if not model_path.exists():
            pytest.skip("Model not yet trained")
        from app.ai.category_classifier import CategoryClassifier
        clf = CategoryClassifier()
        result = clf.predict("Apple announced a new artificial intelligence chip for the iPhone.")
        assert clf.is_loaded()
        assert "category" in result


# ===========================================================================
# 3. INFERENCE TESTS
# ===========================================================================


VALID_CATEGORIES = {"Business", "Sports", "Technology", "World"}


class TestInference:
    @pytest.fixture(autouse=True)
    def skip_if_no_model(self):
        model_path = Path(__file__).parent.parent / "ml" / "models" / "news_category_model.joblib"
        if not model_path.exists():
            pytest.skip("Model not yet trained — run train_classifier.py first")

    @pytest.fixture
    def clf(self):
        from app.ai.category_classifier import CategoryClassifier
        return CategoryClassifier()

    def test_predict_returns_dict(self, clf):
        result = clf.predict("Scientists discover a new exoplanet with signs of water.")
        assert isinstance(result, dict)

    def test_predict_has_category_key(self, clf):
        result = clf.predict("The stock market rose sharply on strong earnings reports.")
        assert "category" in result

    def test_predict_has_confidence_key(self, clf):
        result = clf.predict("Manchester United won the Premier League championship.")
        assert "confidence" in result

    def test_predict_has_all_scores_key(self, clf):
        result = clf.predict("The government passed a new economic policy bill.")
        assert "all_scores" in result

    def test_predict_category_is_valid(self, clf):
        result = clf.predict("Apple introduced a new artificial intelligence chip for its devices.")
        assert result["category"] in VALID_CATEGORIES, (
            f"Unexpected category: {result['category']}"
        )

    def test_predict_confidence_in_range(self, clf):
        result = clf.predict("The team scored three goals in the final quarter.")
        assert 0.0 <= result["confidence"] <= 1.0

    def test_predict_all_scores_sum_to_one(self, clf):
        result = clf.predict("Scientists announced a breakthrough in cancer treatment.")
        total = sum(result["all_scores"].values())
        assert abs(total - 1.0) < 0.01, f"Probabilities sum to {total}, not 1.0"

    def test_predict_all_scores_categories_valid(self, clf):
        result = clf.predict("The economy grew by three percent this quarter.")
        assert set(result["all_scores"].keys()).issubset(VALID_CATEGORIES)

    def test_predict_batch_returns_list(self, clf):
        texts = [
            "Apple announced new AI features for iPhone.",
            "The team won the championship with a late goal.",
        ]
        results = clf.predict_batch(texts)
        assert isinstance(results, list)
        assert len(results) == 2

    def test_predict_batch_each_valid(self, clf):
        texts = [
            "The central bank raised interest rates again.",
            "World leaders met to discuss climate change.",
        ]
        results = clf.predict_batch(texts)
        for r in results:
            assert r["category"] in VALID_CATEGORIES

    def test_predict_empty_string_raises(self, clf):
        with pytest.raises((ValueError, Exception)):
            clf.predict("")

    def test_predict_too_short_raises(self, clf):
        with pytest.raises((ValueError, Exception)):
            clf.predict("Hi")

    def test_categories_property(self, clf):
        cats = clf.categories
        assert isinstance(cats, list)
        assert len(cats) >= 4
        for c in cats:
            assert c in VALID_CATEGORIES

    def test_metadata_property_returns_dict(self, clf):
        meta = clf.metadata
        assert isinstance(meta, dict)
        assert "model_name" in meta

    def test_singleton_get_classifier(self):
        from app.ai.category_classifier import get_classifier
        clf1 = get_classifier()
        clf2 = get_classifier()
        # lru_cache should return same object
        assert clf1 is clf2


# ===========================================================================
# 4. PHASE 1–3 REGRESSION
# ===========================================================================


class TestRegressionPhase1:
    def test_health_returns_200(self, client):
        assert client.get("/api/health").status_code == 200

    def test_health_status_ok(self, client):
        assert client.get("/api/health").json()["status"] == "ok"

    def test_health_service_name(self, client):
        data = client.get("/api/health").json()
        assert data["service"] == "AI News Analyzer API"


class TestRegressionPhase2:
    def test_list_articles_returns_200(self, client):
        assert client.get("/api/articles").status_code == 200

    def test_list_articles_has_structure(self, client):
        data = client.get("/api/articles").json()
        assert "total" in data
        assert "articles" in data

    def test_create_article_manual(self, client):
        payload = {
            "title": "Phase 4A Regression Test Article",
            "content": "This is a regression test article verifying Phase 2 CRUD still works.",
        }
        assert client.post("/api/articles", json=payload).status_code == 201

    def test_get_article_not_found(self, client):
        assert client.get("/api/articles/999999").status_code == 404

    def test_delete_article_not_found(self, client):
        assert client.delete("/api/articles/999999").status_code == 404


class TestRegressionPhase3:
    def test_extract_invalid_scheme_returns_400(self, client):
        response = client.post(
            "/api/articles/extract",
            json={"url": "ftp://example.com/some-long-article-path"},
        )
        assert response.status_code == 400

    def test_extract_localhost_blocked(self, client):
        response = client.post(
            "/api/articles/extract",
            json={"url": "http://localhost/api/internal"},
        )
        assert response.status_code == 400

    def test_extract_private_ip_blocked(self, client):
        response = client.post(
            "/api/articles/extract",
            json={"url": "http://192.168.1.1/router-admin"},
        )
        assert response.status_code == 400

    def test_extract_missing_url_returns_422(self, client):
        assert client.post("/api/articles/extract", json={}).status_code == 422
