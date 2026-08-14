"""
Text Cleaner — normalizes extracted article content.
Does NOT perform NLP preprocessing (no stemming, tokenization, etc.).
"""

import re
import unicodedata


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

WORDS_PER_MINUTE = 230  # average adult reading speed
MIN_READING_TIME_MINUTES = 1


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def clean_text(text: str) -> str:
    """
    Normalize raw extracted article text.

    Operations performed:
    - Unicode normalization (NFC)
    - Remove null bytes and control characters
    - Normalize line endings (CRLF → LF)
    - Collapse consecutive blank lines (max 2 → 1)
    - Strip leading/trailing whitespace per line
    - Remove lines that are pure whitespace
    - Strip overall leading/trailing whitespace

    Args:
        text: Raw extracted text.

    Returns:
        Cleaned text string.
    """
    if not text:
        return ""

    # Unicode normalization
    text = unicodedata.normalize("NFC", text)

    # Remove null bytes
    text = text.replace("\x00", "")

    # Remove control characters except newline (\n) and tab (\t)
    text = re.sub(r"[\x01-\x08\x0b-\x0c\x0e-\x1f\x7f]", "", text)

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Strip trailing whitespace from each line
    lines = [line.rstrip() for line in text.split("\n")]

    # Collapse runs of more than one blank line into exactly one
    cleaned_lines: list[str] = []
    blank_count = 0
    for line in lines:
        if line == "":
            blank_count += 1
            if blank_count <= 1:
                cleaned_lines.append(line)
        else:
            blank_count = 0
            cleaned_lines.append(line)

    text = "\n".join(cleaned_lines)

    # Final strip
    return text.strip()


def clean_title(title: str) -> str:
    """
    Normalize an article title.

    - Unicode normalization
    - Collapse internal whitespace to single space
    - Strip leading/trailing whitespace

    Args:
        title: Raw title string.

    Returns:
        Cleaned title string.
    """
    if not title:
        return ""
    title = unicodedata.normalize("NFC", title)
    title = re.sub(r"\s+", " ", title)
    return title.strip()


def count_words(text: str) -> int:
    """
    Count words in text using whitespace splitting.

    This is a simple, fast word count — not a linguistic tokenizer.
    NLP tokenization will be applied in Phase 4.

    Args:
        text: Cleaned article text.

    Returns:
        Integer word count.
    """
    if not text:
        return 0
    return len(text.split())


def estimate_reading_time(word_count: int) -> int:
    """
    Estimate reading time in minutes based on word count.

    Assumes average reading speed of 230 words/minute.
    Returns a minimum of 1 minute for any non-empty content.

    Args:
        word_count: Number of words in the article.

    Returns:
        Estimated reading time in minutes (int, min=1).
    """
    if word_count <= 0:
        return 0
    minutes = max(MIN_READING_TIME_MINUTES, round(word_count / WORDS_PER_MINUTE))
    return minutes
