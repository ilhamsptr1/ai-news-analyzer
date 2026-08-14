"""
Keyword Extractor — Primary module for Phase 4B-2.

Primary algorithm : YAKE (Yet Another Keyword Extractor)
Fallback algorithm: TF-IDF

Score interpretation:
  YAKE  : LOWER score = higher relevance (output sorted ascending)
  TF-IDF: HIGHER score = higher relevance (output sorted descending)

The "score" field in the response always reflects the raw algorithm score.
Do NOT interpret YAKE scores as probability or confidence.
"""

import logging
import re
import unicodedata

from app.ai.tfidf_keyword_extractor import TfidfKeywordExtractor

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_TEXT_LENGTH = 500_000   # characters
MIN_KEYWORD_LEN = 3
DEFAULT_TOP_N = 10
MIN_TOP_N = 1
MAX_TOP_N = 20

# YAKE configuration
_YAKE_LANGUAGE = "en"
_YAKE_MAX_NGRAM = 3          # allow up to trigrams
_YAKE_DEDUP_LIM = 0.9        # deduplication threshold
_YAKE_DEDUP_FUNC = "seqm"    # string sequence matching for dedup
_YAKE_WINDOW_SIZE = 1        # word window for context

# Stopwords for final filtering (catches edge cases YAKE misses)
_STOPWORD_EN = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "into", "this", "that", "is", "are",
    "was", "were", "it", "its", "he", "she", "they", "we", "who", "which",
    "said", "such", "more", "all", "any", "one", "also", "just", "so",
}

# Indonesian stopwords
_STOPWORD_ID = {
    "dan", "yang", "pada", "dari", "untuk", "dengan", "adalah", "atau",
    "di", "ke", "dalam", "ini", "itu", "sebuah", "suatu", "sebagai",
    "oleh", "kepada", "saat", "bahwa", "serta", "karena", "bagi",
    "seperti", "telah", "akan", "dapat", "bisa", "harus", "ada",
    "tersebut", "tentang", "setelah", "jika", "lagi", "namun", "ketika",
}

_PUNCT_ONLY = re.compile(r"^[^a-zA-Z0-9]+$")
_DIGITS_ONLY = re.compile(r"^\d+$")


# ---------------------------------------------------------------------------
# Text preprocessing
# ---------------------------------------------------------------------------

def _clean_text(text: str) -> str:
    """Minimal cleaning suitable for keyword extraction (preserve context)."""
    if not isinstance(text, str):
        text = str(text) if text is not None else ""

    # Unicode NFC normalisation
    text = unicodedata.normalize("NFC", text)

    # Remove obvious HTML tags
    text = re.sub(r"<[^>]+>", " ", text)

    # Remove HTML entities
    text = re.sub(r"&[a-z]+;", " ", text)
    text = re.sub(r"&#\d+;", " ", text)

    # Normalize whitespace / empty lines
    text = re.sub(r"\r\n|\r", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)

    return text.strip()


# ---------------------------------------------------------------------------
# Keyword quality filtering
# ---------------------------------------------------------------------------

def _is_valid_keyword(kw: str, language: str = "en") -> bool:
    """Check if a keyword passes basic quality filters."""
    kw = kw.strip()
    if not kw or len(kw) < MIN_KEYWORD_LEN:
        return False
    if _PUNCT_ONLY.match(kw):
        return False
    if _DIGITS_ONLY.match(kw):
        return False
    
    # All tokens are stopwords?
    tokens = kw.lower().split()
    stopword_set = _STOPWORD_ID if language == "id" else _STOPWORD_EN
    
    # Exclude negation words from being treated as pure stopword keywords
    # if they somehow end up alone, but usually they are filtered if all tokens are stopwords.
    if all(t in stopword_set for t in tokens):
        return False
        
    return True


def _deduplicate(keywords: list[dict]) -> list[dict]:
    """
    Remove case-insensitive duplicate keywords.
    Preserves the first (highest-ranked) occurrence.
    """
    seen: set[str] = set()
    result = []
    for item in keywords:
        kw_lower = item["keyword"].lower()
        if kw_lower not in seen:
            seen.add(kw_lower)
            result.append(item)
    return result


# ---------------------------------------------------------------------------
# Main KeywordExtractor class
# ---------------------------------------------------------------------------

class KeywordExtractor:
    """
    Extracts keywords and keyphrases from article text.

    Primary  : YAKE — unsupervised, no training required.
    Fallback : TF-IDF — used if YAKE raises an exception.

    Usage:
        extractor = KeywordExtractor()
        result = extractor.extract("Apple announced AI chip...", top_n=10)
        # -> {"keywords": [...], "method": "yake"}
    """

    def __init__(self) -> None:
        self._tfidf = TfidfKeywordExtractor(
            ngram_range=(1, 3),
            min_df=1,
            max_features=5_000,
        )

    def extract(self, text: str, top_n: int = DEFAULT_TOP_N, language: str = "en") -> dict:
        """
        Extract keywords from text.

        Args:
            text     : Article text (plain or lightly HTML-mixed).
            top_n    : Maximum keywords to return (1-20).
            language : Language of the text ("id" or "en").

        Returns:
            {
              "keywords": [{"keyword": str, "score": float}, ...],
              "method"  : "yake" | "tfidf"
            }

        Score semantics:
            YAKE  : lower score = higher relevance (sorted ascending)
            TF-IDF: higher score = higher relevance (sorted descending)
        """
        # ── Validate top_n ────────────────────────────────────────────
        if not isinstance(top_n, int) or top_n < MIN_TOP_N or top_n > MAX_TOP_N:
            raise ValueError(
                f"top_n must be an integer between {MIN_TOP_N} and {MAX_TOP_N}, got {top_n!r}"
            )

        # ── Validate / clean input text ────────────────────────────────
        if not text or not isinstance(text, str):
            return {"keywords": [], "method": "yake"}

        if len(text) > MAX_TEXT_LENGTH:
            raise ValueError(
                f"Input text exceeds maximum length of {MAX_TEXT_LENGTH:,} characters."
            )

        cleaned = _clean_text(text)
        if not cleaned:
            return {"keywords": [], "method": "yake"}

        # ── Try YAKE ──────────────────────────────────────────────────
        try:
            keywords = self._extract_yake(cleaned, top_n, language)
            return {"keywords": keywords, "method": "yake"}

        except Exception as exc:
            logger.warning(
                "YAKE extraction failed (%s); falling back to TF-IDF.", exc
            )

        # ── TF-IDF fallback ──────────────────────────────────────────
        try:
            keywords = self._tfidf.extract(cleaned, top_n)
            return {"keywords": keywords, "method": "tfidf"}
        except Exception as exc:
            logger.error("TF-IDF fallback also failed: %s", exc)
            return {"keywords": [], "method": "tfidf"}

    # ── Private: YAKE ──────────────────────────────────────────────────

    def _extract_yake(self, text: str, top_n: int, language: str) -> list[dict]:
        """Run YAKE on text and return filtered, deduplicated results."""
        import yake  # lazy import so module loads even if yake not installed

        extractor = yake.KeywordExtractor(
            lan=_YAKE_LANGUAGE,
            n=_YAKE_MAX_NGRAM,
            dedupLim=_YAKE_DEDUP_LIM,
            dedupFunc=_YAKE_DEDUP_FUNC,
            windowsSize=_YAKE_WINDOW_SIZE,
            top=top_n * 3,  # request more; we'll filter/deduplicate ourselves
        )

        raw_keywords: list[tuple[str, float]] = extractor.extract_keywords(text)

        if not raw_keywords:
            return []

        # Build, filter, deduplicate, then trim to top_n
        items = [
            {"keyword": kw, "score": round(float(score), 6)}
            for kw, score in raw_keywords
            if _is_valid_keyword(kw, language)
        ]

        # YAKE: sort ascending (lower score = more important)
        items.sort(key=lambda x: x["score"])
        items = _deduplicate(items)
        return items[:top_n]


# ---------------------------------------------------------------------------
# Module-level singleton (optional — extractor is lightweight)
# ---------------------------------------------------------------------------

_extractor: KeywordExtractor | None = None


def get_keyword_extractor() -> KeywordExtractor:
    """Return (or create) a module-level KeywordExtractor singleton."""
    global _extractor
    if _extractor is None:
        _extractor = KeywordExtractor()
    return _extractor
