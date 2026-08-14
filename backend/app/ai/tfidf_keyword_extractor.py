"""
TF-IDF Keyword Extractor — Fallback for YAKE failures.

Used only when YAKE raises an exception or produces no results.
Score interpretation: HIGHER score = more important keyword.
"""

import re
import unicodedata
from typing import List

from sklearn.feature_extraction.text import TfidfVectorizer

# Stopwords to filter out keyword-only phrases
_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "into", "through", "is", "are",
    "was", "were", "be", "been", "being", "have", "has", "had", "do",
    "does", "did", "will", "would", "could", "should", "may", "might",
    "it", "its", "this", "that", "these", "those", "he", "she", "they",
    "we", "i", "you", "who", "which", "what", "when", "where", "how",
    "not", "so", "if", "then", "than", "also", "about", "their", "there",
    "after", "before", "while", "over", "each", "just", "can", "up",
    "said", "say", "such", "more", "all", "any", "one", "out", "my",
}

_MIN_KEYWORD_LEN = 3
_PUNCTUATION_PATTERN = re.compile(r"^[^a-zA-Z0-9]+$")
_DIGITS_ONLY_PATTERN = re.compile(r"^\d+$")


def _is_valid_keyword(kw: str) -> bool:
    """Return True if keyword passes basic quality filters."""
    kw_stripped = kw.strip()
    if not kw_stripped:
        return False
    if len(kw_stripped) < _MIN_KEYWORD_LEN:
        return False
    if _PUNCTUATION_PATTERN.match(kw_stripped):
        return False
    if _DIGITS_ONLY_PATTERN.match(kw_stripped):
        return False
    # Check if all tokens are stopwords
    tokens = kw_stripped.lower().split()
    if all(t in _STOPWORDS for t in tokens):
        return False
    return True


class TfidfKeywordExtractor:
    """
    Lightweight TF-IDF keyword extractor. Used as fallback when YAKE fails.

    Score: TF-IDF score. Higher = more relevant.
    Note: This is NOT a trained model — it fits on the single input document.
    """

    def __init__(
        self,
        ngram_range: tuple = (1, 3),
        min_df: int = 1,
        max_features: int = 5_000,
    ) -> None:
        self._ngram_range = ngram_range
        self._min_df = min_df
        self._max_features = max_features

    def extract(self, text: str, top_n: int = 10) -> list[dict]:
        """
        Extract top_n keywords from text using TF-IDF on the input document.

        Args:
            text: Input article text.
            top_n: Maximum number of keywords to return.

        Returns:
            List of dicts sorted by score descending:
            [{"keyword": "machine learning", "score": 0.85}, ...]
        """
        if not text or not isinstance(text, str):
            return []

        text = text.strip()
        if not text:
            return []

        try:
            vectorizer = TfidfVectorizer(
                ngram_range=self._ngram_range,
                min_df=self._min_df,
                max_features=self._max_features,
                sublinear_tf=True,
                strip_accents="unicode",
                analyzer="word",
                token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z0-9]+\b",
                stop_words=list(_STOPWORDS),
            )

            tfidf_matrix = vectorizer.fit_transform([text])
            feature_names = vectorizer.get_feature_names_out()
            scores = tfidf_matrix.toarray()[0]

            # Build (keyword, score) pairs, filter, deduplicate
            pairs = sorted(
                ((feature_names[i], float(scores[i])) for i in range(len(feature_names))),
                key=lambda x: x[1],
                reverse=True,  # TF-IDF: higher = more important
            )

            seen_lower: set[str] = set()
            results = []
            for kw, score in pairs:
                if score <= 0:
                    continue
                if not _is_valid_keyword(kw):
                    continue
                kw_lower = kw.lower()
                if kw_lower in seen_lower:
                    continue
                seen_lower.add(kw_lower)
                results.append({"keyword": kw, "score": round(score, 6)})
                if len(results) >= top_n:
                    break

            return results

        except Exception:
            return []
