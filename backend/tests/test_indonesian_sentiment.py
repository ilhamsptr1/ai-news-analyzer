"""
Phase 4B-1-ID Tests — Indonesian Sentiment Classification
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

from ml.scripts.indonesian_sentiment_preprocess import (
    CLASSES,
    LABEL_COLUMN,
    TEXT_COLUMN,
    clean_text,
    preprocess_df,
)
from app.ai.sentiment_id_classifier import (
    IndonesianSentimentClassifier,
    get_indonesian_sentiment_classifier,
    VALID_SENTIMENTS,
)

# ---------------------------------------------------------------------------
# Sample Indonesian Texts
# ---------------------------------------------------------------------------

SAMPLE_POS = "Pemerintah berhasil meningkatkan pertumbuhan ekonomi nasional."
SAMPLE_NEG = "Program tersebut gagal mencapai target yang telah ditetapkan."
SAMPLE_NEU = "Pemerintah mengumumkan kebijakan baru pada hari Senin."


# ===========================================================================
# 1. TEXT CLEANING & PREPROCESSING TESTS
# ===========================================================================

class TestIndonesianSentimentCleaning:
    def test_clean_basic_whitespace(self):
        assert clean_text("  harga saham   naik  ") == "harga saham naik"

    def test_clean_html_tags(self):
        result = clean_text("<b>Rugi bersih</b> kuartal ini turun")
        assert "<b>" not in result
        assert "Rugi bersih" in result

    def test_clean_html_entities(self):
        result = clean_text("Laba &amp; rugi")
        assert "&amp;" not in result

    def test_clean_preserves_negation(self):
        """CRITICAL: Negation words must NOT be removed."""
        text = "Kebijakan tersebut sama sekali tidak bagus dan belum memberikan hasil."
        result = clean_text(text)
        assert "tidak" in result
        assert "bagus" in result
        assert "belum" in result
        assert "memberikan" in result
        
    def test_clean_empty(self):
        assert clean_text("") == ""
        
    def test_preprocess_df_drops_invalid_labels(self):
        df = pd.DataFrame({
            "text": ["Panjang 1", "Panjang 2", "Panjang 3"],
            "label": [0, 1, 99], # 0,1,2 mapped to Neg,Neu,Pos
        })
        cleaned = preprocess_df(df)
        assert len(cleaned) == 2
        assert cleaned.iloc[0][LABEL_COLUMN] == "Negative"
        assert cleaned.iloc[1][LABEL_COLUMN] == "Neutral"


# ===========================================================================
# 2. INDONESIAN SENTIMENT CLASSIFIER TESTS
# ===========================================================================

class TestIndonesianSentimentClassifier:
    @pytest.fixture(autouse=True)
    def skip_if_no_model(self):
        model_path = Path(__file__).parents[1] / "ml" / "models" / "sentiment_id_model.joblib"
        if not model_path.exists():
            pytest.skip("Indonesian Sentiment model not yet trained")

    @pytest.fixture
    def clf(self):
        return get_indonesian_sentiment_classifier()

    def test_model_files_exist(self):
        model_path = Path(__file__).parents[1] / "ml" / "models" / "sentiment_id_model.joblib"
        meta_path = Path(__file__).parents[1] / "ml" / "models" / "sentiment_id_metadata.json"
        assert model_path.exists()
        assert meta_path.exists()

    def test_metadata_has_required_fields(self):
        import json
        meta_path = Path(__file__).parents[1] / "ml" / "models" / "sentiment_id_metadata.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        assert meta["language"] == "id"
        assert "accuracy" in meta
        assert "macro_f1" in meta
        assert "label_origin" in meta

    def test_singleton_same_instance(self):
        c1 = get_indonesian_sentiment_classifier()
        c2 = get_indonesian_sentiment_classifier()
        assert c1 is c2

    def test_predict_returns_dict(self, clf):
        result = clf.predict(SAMPLE_NEU)
        assert isinstance(result, dict)

    def test_predict_has_keys(self, clf):
        result = clf.predict(SAMPLE_NEU)
        assert "sentiment" in result
        assert "confidence" in result
        assert "all_scores" in result

    def test_predict_sentiment_is_valid(self, clf):
        for sample in [SAMPLE_POS, SAMPLE_NEG, SAMPLE_NEU]:
            result = clf.predict(sample)
            assert result["sentiment"] in VALID_SENTIMENTS

    def test_predict_confidence_in_range(self, clf):
        result = clf.predict(SAMPLE_POS)
        assert 0.0 <= result["confidence"] <= 1.0

    def test_predict_all_scores_sum_to_one(self, clf):
        result = clf.predict(SAMPLE_NEG)
        total = sum(result["all_scores"].values())
        assert abs(total - 1.0) < 0.01

    def test_predict_empty_raises(self, clf):
        with pytest.raises(ValueError):
            clf.predict("")

    def test_predict_batch_returns_list(self, clf):
        results = clf.predict_batch([SAMPLE_POS, SAMPLE_NEG])
        assert isinstance(results, list)
        assert len(results) == 2

    def test_predict_batch_each_valid(self, clf):
        results = clf.predict_batch([SAMPLE_POS, SAMPLE_NEG, SAMPLE_NEU])
        for r in results:
            assert r["sentiment"] in VALID_SENTIMENTS

    def test_performance_single_prediction(self, clf):
        start = time.time()
        clf.predict(SAMPLE_POS)
        elapsed = time.time() - start
        assert elapsed < 2.0

    def test_performance_batch_prediction(self, clf):
        samples = [SAMPLE_POS, SAMPLE_NEG, SAMPLE_NEU] * 5
        start = time.time()
        clf.predict_batch(samples[:10])
        elapsed = time.time() - start
        assert elapsed < 5.0
