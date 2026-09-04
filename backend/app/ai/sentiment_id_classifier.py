"""
Indonesian Sentiment Classifier — Inference module for Phase 4B-1-ID.

Loads the saved Indonesian sentiment sklearn pipeline and exposes predict().

Architecture:
    language = "id"  ->  IndonesianSentimentClassifier
    language = "en"  ->  SentimentClassifier (Phase 4B-1)
"""

import json
import logging
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_BACKEND_DIR = Path(__file__).resolve().parents[2]
_MODEL_PATH = _BACKEND_DIR / "ml" / "models" / "sentiment_id_model.joblib"
_METADATA_PATH = _BACKEND_DIR / "ml" / "models" / "sentiment_id_metadata.json"

VALID_SENTIMENTS = {"Positive", "Neutral", "Negative"}

# ---------------------------------------------------------------------------
# Classifier class
# ---------------------------------------------------------------------------

class IndonesianSentimentClassifier:
    """
    Wrapper around the saved sklearn Pipeline for Indonesian sentiment classification.

    Lazy-loads on first use. Thread-safe for read-only inference.
    Classes: Negative, Neutral, Positive.
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
                f"Indonesian Sentiment Model not found: {_MODEL_PATH}\n"
                "Run 'python ml/scripts/train_indonesian_sentiment.py' first."
            )

        import joblib
        logger.info("Loading Indonesian sentiment classifier from %s", _MODEL_PATH)
        self._pipeline = joblib.load(_MODEL_PATH)

        if _METADATA_PATH.exists():
            self._metadata = json.loads(_METADATA_PATH.read_text(encoding="utf-8"))
            logger.info(
                "Indonesian sentiment model loaded: %s  Accuracy=%.4f  MacroF1=%.4f",
                self._metadata.get("model_name"),
                self._metadata.get("accuracy", 0),
                self._metadata.get("macro_f1", 0),
            )

    def predict(self, text: str) -> dict:
        """
        Predict the sentiment of an Indonesian text.

        Args:
            text: Indonesian text.

        Returns:
            dict with keys:
                sentiment   (str)   -- "Negative", "Neutral", or "Positive"
                confidence (float) -- probability from calibrated classifier [0.0, 1.0]
                all_scores (dict)  -- probability per class
        """
        self._load()

        if not text or not isinstance(text, str):
            raise ValueError("text must be a non-empty string")
        text = text.strip()
        if len(text) < 3:
            raise ValueError("text is too short to classify")

        # Assume predict_proba exists (because we mandate CalibratedClassifierCV if SVM)
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
            "model": self._metadata.get("model_name", "Unknown"),
        }

    def predict_batch(self, texts: list[str]) -> list[dict]:
        """Predict sentiment for a list of texts."""
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
                "model": self._metadata.get("model_name", "Unknown"),
            })
        return results

    @property
    def metadata(self) -> dict:
        self._load()
        return dict(self._metadata)

    def is_loaded(self) -> bool:
        return self._pipeline is not None


@lru_cache(maxsize=1)
def get_indonesian_sentiment_classifier() -> IndonesianSentimentClassifier:
    """Module-level singleton lazy loader."""
    return IndonesianSentimentClassifier()
