"""
Language Detector — Phase 4C (Patched: Fix Unsupported Language Routing)

Automatically detects the language of a given text.

Strategy:
    langdetect (primary) — probabilistic, seeded for reproducibility
    langid    (fallback)  — rule-based, more robust on short texts

Supported pipeline languages: "id", "en"
Unsupported languages are returned as-is with supported=False.
They are NEVER silently converted to "en".
"""

import logging
import threading
from functools import lru_cache

logger = logging.getLogger(__name__)

# Minimum text length for reliable detection
_MIN_CHARS = 20

# Languages the AI pipeline can handle
_SUPPORTED = {"id", "en"}

# Human-readable names for ISO 639-1 codes (common subset)
_LANGUAGE_NAMES: dict[str, str] = {
    "id": "Indonesian",
    "en": "English",
    "af": "Afrikaans",
    "ar": "Arabic",
    "bg": "Bulgarian",
    "bn": "Bengali",
    "ca": "Catalan",
    "cs": "Czech",
    "cy": "Welsh",
    "da": "Danish",
    "de": "German",
    "el": "Greek",
    "es": "Spanish",
    "et": "Estonian",
    "fa": "Persian",
    "fi": "Finnish",
    "fr": "French",
    "gu": "Gujarati",
    "he": "Hebrew",
    "hi": "Hindi",
    "hr": "Croatian",
    "hu": "Hungarian",
    "hy": "Armenian",
    "it": "Italian",
    "ja": "Japanese",
    "ka": "Georgian",
    "kn": "Kannada",
    "ko": "Korean",
    "lt": "Lithuanian",
    "lv": "Latvian",
    "mk": "Macedonian",
    "ml": "Malayalam",
    "mr": "Marathi",
    "ms": "Malay",
    "nl": "Dutch",
    "no": "Norwegian",
    "pl": "Polish",
    "pt": "Portuguese",
    "ro": "Romanian",
    "ru": "Russian",
    "sk": "Slovak",
    "sl": "Slovenian",
    "so": "Somali",
    "sq": "Albanian",
    "sv": "Swedish",
    "sw": "Swahili",
    "ta": "Tamil",
    "te": "Telugu",
    "th": "Thai",
    "tl": "Filipino",
    "tr": "Turkish",
    "uk": "Ukrainian",
    "ur": "Urdu",
    "vi": "Vietnamese",
    "zh-cn": "Chinese (Simplified)",
    "zh-tw": "Chinese (Traditional)",
    "zh": "Chinese",
}

# langdetect uses global state; protect with a lock for thread safety
_langdetect_lock = threading.Lock()


class LanguageDetectionError(Exception):
    """Raised when language cannot be detected from the given text."""


class LanguageDetector:
    """
    Singleton language detector.

    Lazy-initialises both langdetect and langid on first use.
    Thread-safe for concurrent read inference.

    IMPORTANT: Unsupported languages are returned with supported=False.
    They are NEVER silently converted or routed to English models.
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

        # Pre-load langid classifier
        import langid
        langid.set_languages(None)  # no filter — accept all languages
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
                "language":      str        – raw ISO code (e.g. "fr", "id", "en"),
                "language_name": str        – human-readable name (e.g. "French"),
                "confidence":    float|None – 0.0–1.0 from langdetect, or None,
                "method":        str        – "langdetect" or "langid",
                "supported":     bool       – True only if language in {"id", "en"},
            }

        NOTE: "language" is ALWAYS the raw detected code. Unsupported languages
        are returned as-is with supported=False. They are never mapped to "en".
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

        supported = raw_lang in _SUPPORTED
        language_name = _LANGUAGE_NAMES.get(raw_lang, raw_lang.upper())

        return {
            "language": raw_lang,
            "language_name": language_name,
            "confidence": round(confidence, 4) if confidence is not None else None,
            "method": method,
            "supported": supported,
        }

    def detect_language_code(self, text: str) -> str:
        """Convenience method — returns the raw detected language code."""
        return self.detect(text)["language"]

    @staticmethod
    def is_supported(lang: str) -> bool:
        """Return True if *lang* is a supported language code."""
        return lang in _SUPPORTED

    @staticmethod
    def get_language_name(lang: str) -> str:
        """Return human-readable name for a language code."""
        return _LANGUAGE_NAMES.get(lang, lang.upper())

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

    def _detect_langid(self, text: str) -> tuple[str, None]:
        """Run langid and return (lang_code, None).

        langid returns a log-probability score — we do NOT convert it to a
        pseudo-confidence to avoid fabricating data.
        """
        lang, _score = self._langid_model.classify(text)
        return lang, None


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def get_language_detector() -> LanguageDetector:
    """Return the module-level singleton LanguageDetector."""
    return LanguageDetector()
