"""
Multilingual Analyzer — Phase 4C (Patched: Fix Unsupported Language Routing)

Orchestrates all AI pipelines in a single call, routing to the correct
language-specific model based on auto-detected or provided language.

CRITICAL:
    Unsupported languages (anything other than "id" or "en") MUST NOT be
    routed to any ML model. analyze() returns an unsupported-language result
    with supported=False so the route layer can return the correct response.

Supported routing:
    "id" → IndonesianCategoryClassifier + IndonesianSentimentClassifier + Indonesian NER
    "en" → CategoryClassifier           + SentimentClassifier           + English NER
    Both → KeywordExtractor (language-agnostic)

Unsupported (any other lang):
    → No category, no sentiment, no NER
    → Returns {"supported": False, "language": {...}}
"""

import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

_SUPPORTED_LANGS = {"id", "en"}


class MultilingualAnalyzer:
    """
    Single entry point for the full NLP analysis pipeline.

    - Accepts optional `language` override; auto-detects if None.
    - Lazy-loads models only when first called for that language.
    - Thread-safe (all underlying models use read-only inference).
    - Unsupported languages are NEVER routed to English or Indonesian models.
    """

    def analyze(
        self,
        text: str,
        language: str | None = None,
        top_keywords: int = 10,
    ) -> dict:
        """
        Run the full analysis pipeline on *text*.

        Args:
            text:         Article or document text (≥10 chars recommended).
            language:     Optional "id" or "en" override.
                          If None, language is auto-detected.
            top_keywords: Max keywords to extract (1–20).

        Returns (supported language):
            {
                "supported": True,
                "language": {
                    "code": "id",
                    "language_name": "Indonesian",
                    "source": "auto"|"provided",
                    "confidence": 0.99|None,
                    "supported": True,
                },
                "category":  {...},
                "sentiment": {...},
                "keywords":  {...},
                "entities":  {...},
            }

        Returns (unsupported language):
            {
                "supported": False,
                "language": {
                    "code": "fr",
                    "language_name": "French",
                    "source": "auto",
                    "confidence": 0.99,
                    "supported": False,
                },
            }
        """
        if not text or not isinstance(text, str):
            raise ValueError("text must be a non-empty string")
        text = text.strip()
        if len(text) < 5:
            raise ValueError("text is too short to analyse")

        # ------------------------------------------------------------------
        # 1. Language resolution
        # ------------------------------------------------------------------
        lang_info = self._resolve_language(text, language)

        # ------------------------------------------------------------------
        # 2. Gate: if language not supported, stop here — run NO models
        # ------------------------------------------------------------------
        if not lang_info["supported"]:
            return {
                "supported": False,
                "language": lang_info,
            }

        lang_code = lang_info["code"]

        # ------------------------------------------------------------------
        # 3. Category classification
        # ------------------------------------------------------------------
        category_result = self._classify_category(text, lang_code)

        # ------------------------------------------------------------------
        # 4. Sentiment analysis
        # ------------------------------------------------------------------
        sentiment_result = self._classify_sentiment(text, lang_code)

        # ------------------------------------------------------------------
        # 5. Keyword extraction (language-agnostic)
        # ------------------------------------------------------------------
        keyword_result = self._extract_keywords(text, top_keywords)

        # ------------------------------------------------------------------
        # 6. Named Entity Recognition
        # ------------------------------------------------------------------
        entity_result = self._extract_entities(text, lang_code)

        return {
            "supported": True,
            "language": lang_info,
            "category": category_result,
            "sentiment": sentiment_result,
            "keywords": keyword_result,
            "entities": entity_result,
        }

    # ── Private helpers ───────────────────────────────────────────────

    def _resolve_language(self, text: str, language: str | None) -> dict:
        """Resolve the language to use — auto-detect or use provided value."""
        from app.ai.language_detector import get_language_detector, _LANGUAGE_NAMES

        if language is not None:
            # Caller-provided; always treated as supported (schema validates "id"|"en")
            return {
                "code": language,
                "language_name": _LANGUAGE_NAMES.get(language, language.upper()),
                "source": "provided",
                "confidence": None,
                "supported": True,
            }

        detector = get_language_detector()

        try:
            detection = detector.detect(text)
            return {
                "code": detection["language"],
                "language_name": detection["language_name"],
                "source": "auto",
                "confidence": detection["confidence"],
                "supported": detection["supported"],
            }
        except Exception as exc:
            logger.warning(
                "Language detection failed (%s), treating as unsupported", exc
            )
            # Detection failure → treat as unsupported, don't silently default to "en"
            return {
                "code": "unknown",
                "language_name": "Unknown",
                "source": "auto",
                "confidence": None,
                "supported": False,
            }

    def _classify_category(self, text: str, lang: str) -> dict:
        """Route to the correct category classifier (only "id" or "en")."""
        try:
            if lang == "id":
                from app.ai.indonesian_category_classifier import get_indonesian_classifier
                clf = get_indonesian_classifier()
            else:
                from app.ai.category_classifier import get_classifier
                clf = get_classifier()
            return clf.predict(text)
        except Exception as exc:
            logger.error("Category classification error (%s): %s", lang, exc, exc_info=True)
            return {"category": "Unknown", "confidence": 0.0, "all_scores": {}}

    def _classify_sentiment(self, text: str, lang: str) -> dict:
        """Route to the correct sentiment classifier (only "id" or "en")."""
        try:
            if lang == "id":
                from app.ai.sentiment_id_classifier import get_indonesian_sentiment_classifier
                clf = get_indonesian_sentiment_classifier()
            else:
                from app.ai.sentiment_classifier import get_sentiment_classifier
                clf = get_sentiment_classifier()
            return clf.predict(text)
        except Exception as exc:
            logger.error("Sentiment classification error (%s): %s", lang, exc, exc_info=True)
            return {"sentiment": "Unknown", "confidence": 0.0, "all_scores": {}}

    def _extract_keywords(self, text: str, top_n: int) -> dict:
        """Extract keywords (language-agnostic)."""
        try:
            from app.ai.keyword_extractor import get_keyword_extractor
            extractor = get_keyword_extractor()
            result = extractor.extract(text=text, top_n=top_n)
            return {
                "keywords": result.get("keywords", []),
                "method": result.get("method", "yake"),
                "total": len(result.get("keywords", [])),
            }
        except Exception as exc:
            logger.error("Keyword extraction error: %s", exc, exc_info=True)
            return {"keywords": [], "method": "error", "total": 0}

    def _extract_entities(self, text: str, lang: str) -> dict:
        """Extract named entities (only "id" or "en")."""
        try:
            from app.ai.ner_extractor import get_ner_extractor
            extractor = get_ner_extractor()
            result = extractor.extract(text=text, language=lang)
            return {
                "entities": result.get("entities", []),
                "model": result.get("model", ""),
            }
        except Exception as exc:
            logger.error("NER extraction error (%s): %s", lang, exc, exc_info=True)
            return {"entities": [], "model": "error"}


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def get_multilingual_analyzer() -> MultilingualAnalyzer:
    """Return the module-level singleton MultilingualAnalyzer."""
    return MultilingualAnalyzer()
