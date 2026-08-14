"""
Sentiment Classifier -- Inference module for Phase 4B-1.

Loads the saved sentiment scikit-learn pipeline and exposes a predict() API.
"""

import json
import logging
from pathlib import Path
from functools import lru_cache

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_BACKEND_DIR = Path(__file__).resolve().parents[2]
_MODEL_PATH = _BACKEND_DIR / "ml" / "models" / "sentiment_model.joblib"
_METADATA_PATH = _BACKEND_DIR / "ml" / "models" / "sentiment_model_metadata.json"

VALID_CATEGORIES = {"Negative", "Neutral", "Positive"}

# ---------------------------------------------------------------------------
# Classifier class
# ---------------------------------------------------------------------------

class SentimentClassifier:
    """
    Wrapper around the saved sklearn Pipeline for Sentiment.
    Lazy-loads on first use. Thread-safe for read-only inference.
    """

    def __init__(self) -> None:
        self._pipeline = None
        self._metadata: dict = {}

    def _load(self) -> None:
        """Load pipeline and metadata from disk."""
        if self._pipeline is not None:
            return

        if not _MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Sentiment Model file not found: {_MODEL_PATH}\n"
                "Run 'python ml/scripts/train_sentiment.py' first."
            )

        import joblib
        logger.info("Loading sentiment classifier from %s", _MODEL_PATH)
        self._pipeline = joblib.load(_MODEL_PATH)

        if _METADATA_PATH.exists():
            self._metadata = json.loads(_METADATA_PATH.read_text(encoding="utf-8"))
            logger.info(
                "Sentiment Model loaded: %s  Accuracy=%.4f",
                self._metadata.get("model_name"),
                self._metadata.get("accuracy", 0),
            )

    def predict(self, text: str) -> dict:
        """
        Predict sentiment of an article/text.

        Args:
            text: Raw article text.

        Returns:
            dict with keys:
                sentiment  (str)   -- 'Negative', 'Neutral', 'Positive'
                confidence (float) -- probability [0.0, 1.0]
                all_scores (dict)  -- probability per class
        """
        self._load()

        if not text or not isinstance(text, str):
            raise ValueError("text must be a non-empty string")

        text = text.strip()
        if len(text) < 5:
            raise ValueError("text is too short to classify sentiment")

        # predict_proba is supported by LogisticRegression, NaiveBayes, CalibratedClassifierCV
        proba = self._pipeline.predict_proba([text])[0]
        classes = self._pipeline.classes_

        scores = {str(cls): round(float(p), 4) for cls, p in zip(classes, proba)}

        best_idx = int(proba.argmax())
        predicted = str(classes[best_idx])
        confidence = round(float(proba[best_idx]), 4)

        return {
            "sentiment": predicted,
            "confidence": confidence,
            "all_scores": scores,
        }

    def predict_batch(self, texts: list[str]) -> list[dict]:
        self._load()
        if not texts:
            return []

        proba_matrix = self._pipeline.predict_proba(texts)
        classes = self._pipeline.classes_

        results = []
        for proba in proba_matrix:
            best_idx = int(proba.argmax())
            scores = {str(cls): round(float(p), 4) for cls, p in zip(classes, proba)}
            results.append({
                "sentiment": str(classes[best_idx]),
                "confidence": round(float(proba[best_idx]), 4),
                "all_scores": scores,
            })
        return results

    @property
    def metadata(self) -> dict:
        self._load()
        return dict(self._metadata)

    @property
    def categories(self) -> list[str]:
        self._load()
        return list(self._pipeline.classes_)

    def is_loaded(self) -> bool:
        return self._pipeline is not None

@lru_cache(maxsize=1)
def get_sentiment_classifier() -> SentimentClassifier:
    """Module-level singleton lazy loader."""
    return SentimentClassifier()
