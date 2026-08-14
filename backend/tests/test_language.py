"""
Phase 4C Tests — Automatic Language Detection & Multilingual Analyzer
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app
from app.ai.language_detector import get_language_detector, LanguageDetector

client = TestClient(app)

# ---------------------------------------------------------------------------
# Test Data
# ---------------------------------------------------------------------------

TEXT_ID_SHORT = "Presiden Prabowo bertemu dengan Elon Musk di Jakarta hari ini."
TEXT_ID_LONG = (
    "Pemerintah Indonesia mengumumkan kebijakan baru untuk mendorong pertumbuhan "
    "ekonomi nasional. Menteri Keuangan Sri Mulyani menyatakan bahwa anggaran "
    "negara tahun depan akan difokuskan pada infrastruktur dan pendidikan. "
    "Bank Indonesia mempertahankan suku bunga acuan untuk menjaga stabilitas rupiah."
)
TEXT_EN_SHORT = "Apple CEO Tim Cook announced a major new AI product in California."
TEXT_EN_LONG = (
    "The United States Federal Reserve kept interest rates steady this week, "
    "citing ongoing concerns about inflation and labor market dynamics. "
    "Federal Reserve Chair Jerome Powell emphasized that the central bank remains "
    "committed to bringing inflation down to its 2% target. Wall Street reacted "
    "positively to the news, with the S&P 500 closing up 1.2%."
)
TEXT_ES = "El gobierno de España ha anunciado nuevas medidas para combatir el cambio climático."
TEXT_TOO_SHORT = "Hello"


# ===========================================================================
# 1. Language Detector Core Tests
# ===========================================================================

class TestLanguageDetectorCore:
    @pytest.fixture(scope="class")
    def detector(self):
        return get_language_detector()

    def test_singleton(self, detector):
        det2 = get_language_detector()
        assert detector is det2

    def test_detect_indonesian_short(self, detector):
        result = detector.detect(TEXT_ID_SHORT)
        assert result["language"] == "id"
        assert result["is_supported"] is True
        assert result["fallback_applied"] is False

    def test_detect_indonesian_long(self, detector):
        result = detector.detect(TEXT_ID_LONG)
        assert result["language"] == "id"

    def test_detect_english_short(self, detector):
        result = detector.detect(TEXT_EN_SHORT)
        assert result["language"] == "en"
        assert result["is_supported"] is True
        assert result["fallback_applied"] is False

    def test_detect_english_long(self, detector):
        result = detector.detect(TEXT_EN_LONG)
        assert result["language"] == "en"

    def test_detect_unsupported_falls_back_to_en(self, detector):
        result = detector.detect(TEXT_ES)
        # Spanish is not supported → must fall back to "en"
        assert result["language"] == "en"
        assert result["fallback_applied"] is True
        assert result["is_supported"] is False
        assert result["raw_lang"] != "en"

    def test_detect_returns_required_keys(self, detector):
        result = detector.detect(TEXT_EN_SHORT)
        required_keys = {"language", "confidence", "raw_lang", "method", "is_supported", "fallback_applied"}
        assert required_keys.issubset(result.keys())

    def test_detect_method_is_valid(self, detector):
        result = detector.detect(TEXT_ID_LONG)
        assert result["method"] in ("langdetect", "langid")

    def test_detect_confidence_range(self, detector):
        result = detector.detect(TEXT_EN_LONG)
        if result["confidence"] is not None:
            assert 0.0 <= result["confidence"] <= 1.0

    def test_detect_too_short_raises(self, detector):
        with pytest.raises(ValueError, match="too short"):
            detector.detect(TEXT_TOO_SHORT)

    def test_detect_empty_raises(self, detector):
        with pytest.raises(ValueError):
            detector.detect("")

    def test_is_supported_true(self, detector):
        assert LanguageDetector.is_supported("id") is True
        assert LanguageDetector.is_supported("en") is True

    def test_is_supported_false(self, detector):
        assert LanguageDetector.is_supported("es") is False
        assert LanguageDetector.is_supported("fr") is False
        assert LanguageDetector.is_supported("zh") is False

    def test_detect_language_code_convenience(self, detector):
        code = detector.detect_language_code(TEXT_ID_SHORT)
        assert code == "id"


# ===========================================================================
# 2. Language Detection API Tests
# ===========================================================================

class TestLanguageDetectApi:
    def test_detect_indonesian(self):
        resp = client.post("/api/language/detect", json={"text": TEXT_ID_LONG})
        assert resp.status_code == 200
        data = resp.json()
        assert data["language"] == "id"
        assert data["is_supported"] is True
        assert data["fallback_applied"] is False

    def test_detect_english(self):
        resp = client.post("/api/language/detect", json={"text": TEXT_EN_LONG})
        assert resp.status_code == 200
        data = resp.json()
        assert data["language"] == "en"

    def test_detect_unsupported_language(self):
        resp = client.post("/api/language/detect", json={"text": TEXT_ES})
        assert resp.status_code == 200
        data = resp.json()
        assert data["language"] == "en"
        assert data["fallback_applied"] is True

    def test_detect_too_short(self):
        resp = client.post("/api/language/detect", json={"text": "Hi"})
        assert resp.status_code == 422

    def test_detect_response_schema(self):
        resp = client.post("/api/language/detect", json={"text": TEXT_EN_SHORT})
        assert resp.status_code == 200
        data = resp.json()
        for key in ("language", "raw_lang", "method", "is_supported", "fallback_applied"):
            assert key in data


# ===========================================================================
# 3. MultilingualAnalyzer Tests
# ===========================================================================

class TestMultilingualAnalyzer:
    @pytest.fixture(scope="class")
    def analyzer(self):
        from app.ai.multilingual_analyzer import get_multilingual_analyzer
        return get_multilingual_analyzer()

    def test_singleton(self, analyzer):
        from app.ai.multilingual_analyzer import get_multilingual_analyzer
        assert analyzer is get_multilingual_analyzer()

    def test_analyze_id_auto_detect(self, analyzer):
        result = analyzer.analyze(TEXT_ID_LONG)
        assert result["language"]["code"] == "id"
        assert result["language"]["source"] == "auto"
        # Category must be a known label
        assert isinstance(result["category"]["category"], str)
        assert len(result["category"]["category"]) > 0
        # Sentiment must be valid
        assert result["sentiment"]["sentiment"] in ("Positive", "Negative", "Neutral",
                                                     "positif", "negatif", "netral")

    def test_analyze_en_auto_detect(self, analyzer):
        result = analyzer.analyze(TEXT_EN_LONG)
        assert result["language"]["code"] == "en"
        assert result["language"]["source"] == "auto"

    def test_analyze_with_language_override_id(self, analyzer):
        result = analyzer.analyze(TEXT_ID_LONG, language="id")
        assert result["language"]["code"] == "id"
        assert result["language"]["source"] == "provided"
        assert result["language"]["confidence"] is None

    def test_analyze_with_language_override_en(self, analyzer):
        result = analyzer.analyze(TEXT_EN_SHORT, language="en")
        assert result["language"]["code"] == "en"
        assert result["language"]["source"] == "provided"

    def test_analyze_returns_all_keys(self, analyzer):
        result = analyzer.analyze(TEXT_EN_SHORT, language="en")
        for key in ("language", "category", "sentiment", "keywords", "entities"):
            assert key in result

    def test_analyze_keywords_extracted(self, analyzer):
        result = analyzer.analyze(TEXT_EN_LONG, language="en")
        kw = result["keywords"]
        assert "keywords" in kw
        assert "method" in kw
        assert kw["total"] >= 0

    def test_analyze_entities_extracted(self, analyzer):
        result = analyzer.analyze(TEXT_EN_SHORT, language="en")
        ent = result["entities"]
        assert "entities" in ent
        assert "model" in ent
        assert isinstance(ent["entities"], list)

    def test_analyze_confidence_ranges(self, analyzer):
        result = analyzer.analyze(TEXT_EN_LONG, language="en")
        cat_conf = result["category"]["confidence"]
        sent_conf = result["sentiment"]["confidence"]
        assert 0.0 <= cat_conf <= 1.0
        assert 0.0 <= sent_conf <= 1.0

    def test_analyze_empty_text_raises(self, analyzer):
        with pytest.raises(ValueError):
            analyzer.analyze("")

    def test_analyze_too_short_raises(self, analyzer):
        with pytest.raises(ValueError):
            analyzer.analyze("Hi")


# ===========================================================================
# 4. Full Analysis API Tests
# ===========================================================================

class TestAnalyzeApi:
    def test_analyze_english_auto(self):
        resp = client.post("/api/analyze", json={"text": TEXT_EN_LONG})
        assert resp.status_code == 200
        data = resp.json()
        assert data["language"]["code"] == "en"
        assert data["language"]["source"] == "auto"
        assert "category" in data
        assert "sentiment" in data
        assert "keywords" in data
        assert "entities" in data

    def test_analyze_indonesian_auto(self):
        resp = client.post("/api/analyze", json={"text": TEXT_ID_LONG})
        assert resp.status_code == 200
        data = resp.json()
        assert data["language"]["code"] == "id"

    def test_analyze_with_language_override(self):
        resp = client.post("/api/analyze", json={
            "text": TEXT_EN_SHORT,
            "language": "en"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["language"]["source"] == "provided"

    def test_analyze_top_keywords_param(self):
        resp = client.post("/api/analyze", json={
            "text": TEXT_EN_LONG,
            "top_keywords": 5,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["keywords"]["total"] <= 5

    def test_analyze_invalid_language(self):
        resp = client.post("/api/analyze", json={
            "text": TEXT_EN_SHORT,
            "language": "fr"
        })
        assert resp.status_code == 422

    def test_analyze_too_short_text(self):
        resp = client.post("/api/analyze", json={"text": "Hi"})
        assert resp.status_code == 422

    def test_analyze_response_schema_category(self):
        resp = client.post("/api/analyze", json={"text": TEXT_EN_LONG})
        assert resp.status_code == 200
        cat = resp.json()["category"]
        assert "category" in cat
        assert "confidence" in cat
        assert "all_scores" in cat

    def test_analyze_response_schema_sentiment(self):
        resp = client.post("/api/analyze", json={"text": TEXT_EN_LONG})
        assert resp.status_code == 200
        sent = resp.json()["sentiment"]
        assert "sentiment" in sent
        assert "confidence" in sent
        assert "all_scores" in sent

    def test_analyze_response_schema_entities(self):
        resp = client.post("/api/analyze", json={"text": TEXT_EN_SHORT})
        assert resp.status_code == 200
        ents = resp.json()["entities"]
        assert "entities" in ents
        assert "model" in ents
        assert ents["model"] == "en_core_web_sm"
