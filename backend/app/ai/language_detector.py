"""
Language Detector — Phase 4C

Automatically detects the language of a given text and routes to the correct
ML pipeline (Indonesian or English).

Strategy:
    langdetect (primary) — probabilistic, seeded for reproducibility
    langid    (fallback)  — rule-based, more robust on short texts

Supported output languages: "id", "en"
Any other detected language falls back to "en".
"""

import logging
import threading
from functools import lru_cache

logger = logging.getLogger(__name__)

# Minimum text length for reliable detection
_MIN_CHARS = 20
# Supported language codes (maps detected lang → normalised lang)
_SUPPORTED = {"id", "en"}
_DEFAULT_LANG = "en"

# langdetect uses global state; protect with a lock for thread safety
_langdetect_lock = threading.Lock()


class LanguageDetectionError(Exception):
    """Raised when language cannot be detected from the given text."""


class LanguageDetector:
    """
    Singleton language detector.

    Lazy-initialises both langdetect and langid on first use.
    Thread-safe for concurrent read inference.
    """

    def __init__(self) -> None:
        self._langid_model = None
        self._initialised = False

    # ── Initialisation ────────────────────────────────────────────────

    def _init(self) -> None:
        if self._initialised:
            return

        # Seed langdetect for deterministic results
        from langdetect import DetectorFactory
        DetectorFactory.seed = 0

        # Pre-load langid classifier (it loads a large model file on import)
        import langid
        langid.set_languages(None)  # no filter — accept all
        self._langid_model = langid

        self._initialised = True
        logger.info("LanguageDetector initialised (langdetect + langid)")

    # ── Public API ────────────────────────────────────────────────────

    def detect(self, text: str) -> dict:
        """
        Detect the language of *text*.

        Args:
            text: Input text. Must be at least 20 characters for reliable results.

        Returns:
            {
                "language":          "id" | "en"   – normalised, always supported,
                "confidence":        float | None   – 0.0–1.0 (langdetect) or None,
                "raw_lang":          str            – raw ISO code from the detector,
                "method":            str            – "langdetect" | "langid",
                "is_supported":      bool,          – True if raw_lang in {"id","en"},
                "fallback_applied":  bool,          – True when mapped to default "en",
            }
        """
        self._init()

        if not text or not isinstance(text, str):
            raise ValueError("text must be a non-empty string")

        text = text.strip()
        if len(text) < _MIN_CHARS:
            raise ValueError(
                f"text is too short for reliable language detection "
                f"(min {_MIN_CHARS} chars, got {len(text)})"
            )

        # -- Primary: langdetect ----------------------------------------
        raw_lang: str | None = None
        confidence: float | None = None
        method = "langdetect"

        try:
            raw_lang, confidence = self._detect_langdetect(text)
        except Exception as exc:
            logger.warning("langdetect failed (%s), falling back to langid", exc)

        # -- Fallback: langid -------------------------------------------
        if raw_lang is None:
            try:
                raw_lang, confidence = self._detect_langid(text)
                method = "langid"
            except Exception as exc:
                logger.error("langid also failed: %s", exc)
                raise LanguageDetectionError(
                    "Could not detect language from the provided text."
                ) from exc

        # -- Normalise --------------------------------------------------
        is_supported = raw_lang in _SUPPORTED
        fallback_applied = not is_supported
        normalised = raw_lang if is_supported else _DEFAULT_LANG

        return {
            "language": normalised,
            "confidence": round(confidence, 4) if confidence is not None else None,
            "raw_lang": raw_lang,
            "method": method,
            "is_supported": is_supported,
            "fallback_applied": fallback_applied,
        }

    def detect_language_code(self, text: str) -> str:
        """Convenience method — returns just the normalised language code."""
        return self.detect(text)["language"]

    @staticmethod
    def is_supported(lang: str) -> bool:
        """Return True if *lang* is a supported language code."""
        return lang in _SUPPORTED

    # ── Internal helpers ──────────────────────────────────────────────

    def _detect_langdetect(self, text: str) -> tuple[str, float]:
        """Run langdetect and return (lang_code, confidence)."""
        from langdetect import detect_langs

        with _langdetect_lock:
            results = detect_langs(text)

        if not results:
            raise LanguageDetectionError("langdetect returned empty results")

        top = results[0]
        return top.lang, float(top.prob)

    def _detect_langid(self, text: str) -> tuple[str, float | None]:
        """Run langid and return (lang_code, confidence)."""
        lang, score = self._langid_model.classify(text)
        # langid score is a log-probability — convert to a pseudo-confidence
        # by using None (we don't fake a probability range)
        return lang, None


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def get_language_detector() -> LanguageDetector:
    """Return the module-level singleton LanguageDetector."""
    return LanguageDetector()
