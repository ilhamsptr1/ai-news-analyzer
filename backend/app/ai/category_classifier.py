"""
Category Classifier — Inference module for Phase 4A.

Loads the saved scikit-learn pipeline and exposes a clean predict() API.
No training occurs here — the model must have been saved by train_classifier.py first.

Usage:
    from app.ai.category_classifier import CategoryClassifier
    clf = CategoryClassifier()
    result = clf.predict("Apple announced a new AI chip...")
    # → {"category": "Technology", "confidence": 0.93, "all_scores": {...}}
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
_MODEL_PATH = _BACKEND_DIR / "ml" / "models" / "news_category_model.joblib"
_METADATA_PATH = _BACKEND_DIR / "ml" / "models" / "model_metadata.json"

# Valid categories (used for output validation)
VALID_CATEGORIES = {"Business", "Sports", "Technology", "World"}


# ---------------------------------------------------------------------------
# Classifier class
# ---------------------------------------------------------------------------


class CategoryClassifier:
    """
    Thin wrapper around the saved sklearn Pipeline.

    Lazy-loads the model on first use.
    Thread-safe for read-only inference.
    """

    def __init__(self) -> None:
        self._pipeline = None
        self._metadata: dict = {}

    # ── Loading ──────────────────────────────────────────────────────

    def _load(self) -> None:
        """Load pipeline and metadata from disk (called once on first use)."""
        if self._pipeline is not None:
            return

        if not _MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Model file not found: {_MODEL_PATH}\n"
                "Run 'python ml/scripts/train_classifier.py' first."
            )

        import joblib
        logger.info("Loading category classifier from %s", _MODEL_PATH)
        self._pipeline = joblib.load(_MODEL_PATH)

        if _METADATA_PATH.exists():
            self._metadata = json.loads(_METADATA_PATH.read_text(encoding="utf-8"))
            logger.info(
                "Model loaded: %s  Accuracy=%.4f  MacroF1=%.4f",
                self._metadata.get("model_name"),
                self._metadata.get("accuracy", 0),
                self._metadata.get("macro_f1", 0),
            )

    # ── Public API ────────────────────────────────────────────────────

    def predict(self, text: str) -> dict:
        """
        Predict the news category of an article text.

        Args:
            text: Raw article text (title + body or just body).

        Returns:
            dict with keys:
                category   (str)   — predicted category label
                confidence (float) — probability of predicted category [0.0, 1.0]
                all_scores (dict)  — probability for each category
        """
        self._load()

        if not text or not isinstance(text, str):
            raise ValueError("text must be a non-empty string")

        text = text.strip()
        if len(text) < 5:
            raise ValueError("text is too short to classify")

        # predict_proba is available because LinearSVC uses CalibratedClassifierCV
        # and Logistic Regression / Naive Bayes have built-in predict_proba
        proba = self._pipeline.predict_proba([text])[0]
        classes = self._pipeline.classes_

        # Build score dict
        scores = {str(cls): round(float(p), 4) for cls, p in zip(classes, proba)}

        # Best category
        best_idx = int(proba.argmax())
        predicted = str(classes[best_idx])
        confidence = round(float(proba[best_idx]), 4)

        return {
            "category": predicted,
            "confidence": confidence,
            "all_scores": scores,
        }

    def predict_batch(self, texts: list[str]) -> list[dict]:
        """
        Predict categories for multiple texts.

        Args:
            texts: List of article texts.

        Returns:
            List of prediction dicts (same format as predict()).
        """
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
                "category": str(classes[best_idx]),
                "confidence": round(float(proba[best_idx]), 4),
                "all_scores": scores,
            })
        return results

    @property
    def metadata(self) -> dict:
        """Return model metadata (loads model if needed)."""
        self._load()
        return dict(self._metadata)

    @property
    def categories(self) -> list[str]:
        """Return list of supported category labels."""
        self._load()
        return list(self._pipeline.classes_)

    def is_loaded(self) -> bool:
        """Return True if model has been loaded into memory."""
        return self._pipeline is not None


# ---------------------------------------------------------------------------
# Module-level singleton (lazy)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def get_classifier() -> CategoryClassifier:
    """
    Return a module-level singleton CategoryClassifier.
    Uses lru_cache so model is loaded at most once per process.
    """
    return CategoryClassifier()
