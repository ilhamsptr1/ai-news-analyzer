import pytest
from app.utils.text_cleaner import clean_text
from app.ai.keyword_extractor import _is_valid_keyword
from app.ai.ner_extractor import NERExtractor

def test_text_cleaner_wikipedia_artifacts():
    raw_text = "Ini adalah artikel kecerdasan buatan.[sunting] Bagian ini penting.[sunting sumber] Referensi [1] [23] [a] di sini."
    cleaned = clean_text(raw_text)
    assert "[sunting]" not in cleaned
    assert "[sunting sumber]" not in cleaned
    assert "[1]" not in cleaned
    assert "[23]" not in cleaned
    assert "[a]" not in cleaned
    assert "Ini adalah artikel kecerdasan buatan. Bagian ini penting. Referensi    di sini." == cleaned

def test_keyword_stopword_filtering():
    # Indonesian stopwords should be filtered
    assert _is_valid_keyword("dan", "id") is False
    assert _is_valid_keyword("yang", "id") is False
    assert _is_valid_keyword("pada", "id") is False
    
    # English stopwords should be filtered
    assert _is_valid_keyword("the", "en") is False
    assert _is_valid_keyword("and", "en") is False
    
    # Negations should be preserved
    assert _is_valid_keyword("tidak", "id") is True
    assert _is_valid_keyword("bukan", "id") is True
    assert _is_valid_keyword("belum", "id") is True
    assert _is_valid_keyword("jangan", "id") is True
    assert _is_valid_keyword("tanpa", "id") is True
    
    # Valid keywords
    assert _is_valid_keyword("kecerdasan buatan", "id") is True
    assert _is_valid_keyword("artificial intelligence", "en") is True

def test_ner_deduplication_case_insensitive():
    raw_entities = [
        {"text": "Google", "label": "ORG", "start": 0, "end": 6, "score": 0.8},
        {"text": "google", "label": "ORG", "start": 10, "end": 16, "score": 0.95},
        {"text": "GOOGLE", "label": "ORG", "start": 20, "end": 26, "score": 0.9},
        {"text": "Apple", "label": "ORG", "start": 30, "end": 35, "score": 0.99},
    ]
    
    unique = NERExtractor.get_unique_entities(raw_entities)
    assert len(unique) == 2
    
    google_ent = next(e for e in unique if e["text"].lower() == "google")
    assert google_ent["score"] == 0.95  # Highest score is preserved
    
    apple_ent = next(e for e in unique if e["text"] == "Apple")
    assert apple_ent["score"] == 0.99
