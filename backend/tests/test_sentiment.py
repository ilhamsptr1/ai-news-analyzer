"""
Phase 4B-1 Tests -- Sentiment Analysis

Test groups:
  1. Dataset preprocessing
  2. Model loading
  3. Inference validation
"""

import sys
from pathlib import Path
import pytest
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ml.scripts.sentiment_preprocess import clean_text, preprocess_df, LABEL_COLUMN, TEXT_COLUMN, LABEL_MAP
from app.ai.sentiment_classifier import get_sentiment_classifier, SentimentClassifier

# ===========================================================================
# 1. PREPROCESSING TESTS
# ===========================================================================

class TestSentimentCleaning:
    def test_clean_text_basic(self):
        assert clean_text("  good news  ") == "good news"

    def test_clean_text_url_removed(self):
        res = clean_text("Stock is up! https://t.co/xyz123 Check it out http://example.com")
        assert "http" not in res
        assert "Stock is up!" in res
        assert "Check it out" in res

    def test_clean_text_html_entities(self):
        assert clean_text("Profit &amp; Loss") == "Profit Loss"

    def test_preprocess_df(self):
        df = pd.DataFrame({
            "text": ["A great day", "A great day", "Terrible news http://url.com", ""],
            "label": [1, 1, 0, 2] # 1=Positive, 0=Negative, 2=Neutral
        })
        cleaned = preprocess_df(df)
        
        # Empty text dropped, duplicates dropped
        assert len(cleaned) == 2
        
        # Check mapping
        assert cleaned.iloc[0][LABEL_COLUMN] == "Positive"
        assert cleaned.iloc[1][LABEL_COLUMN] == "Negative"
        
        # Check URL removal in cleaned data
        assert "http" not in cleaned.iloc[1][TEXT_COLUMN]

# ===========================================================================
# 2. MODEL LOADING & INFERENCE TESTS
# ===========================================================================

VALID_SENTIMENTS = {"Negative", "Neutral", "Positive"}

class TestSentimentInference:
    @pytest.fixture(autouse=True)
    def skip_if_no_model(self):
        model_path = Path(__file__).parents[1] / "ml" / "models" / "sentiment_model.joblib"
        if not model_path.exists():
            pytest.skip("Sentiment model not yet trained")

    @pytest.fixture
    def clf(self):
        return get_sentiment_classifier()

    def test_singleton_loads(self, clf):
        assert isinstance(clf, SentimentClassifier)

    def test_predict_returns_dict(self, clf):
        res = clf.predict("The company reported a massive profit increase.")
        assert "sentiment" in res
        assert "confidence" in res
        assert "all_scores" in res

    def test_predict_valid_sentiment(self, clf):
        res = clf.predict("Stock market crashes following new economic data.")
        assert res["sentiment"] in VALID_SENTIMENTS

    def test_confidence_range(self, clf):
        res = clf.predict("The quarterly report is out.")
        assert 0.0 <= res["confidence"] <= 1.0
        assert sum(res["all_scores"].values()) == pytest.approx(1.0, 0.01)

    def test_smoke_test_positive(self, clf):
        # A very obvious positive statement
        res = clf.predict("The company reported record profits and massive growth this year, exceeding all expectations!")
        assert res["sentiment"] == "Positive"

    def test_smoke_test_negative(self, clf):
        # A very obvious negative statement
        res = clf.predict("The company went bankrupt and lost all its money after terrible earnings.")
        assert res["sentiment"] == "Negative"

    def test_predict_batch(self, clf):
        res = clf.predict_batch(["Good news", "Bad news", "Okay news"])
        assert len(res) == 3
        for r in res:
            assert r["sentiment"] in VALID_SENTIMENTS

    def test_predict_empty_raises(self, clf):
        with pytest.raises(ValueError):
            clf.predict("")
        with pytest.raises(ValueError):
            clf.predict("Hi")

    def test_metadata_available(self, clf):
        meta = clf.metadata
        assert "model_name" in meta
        assert "accuracy" in meta
        assert "macro_f1" in meta
        assert "dataset" in meta
