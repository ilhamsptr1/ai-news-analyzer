"""
Phase 4C Tests — Automatic Language Detection & Multilingual Analyzer
(Patched: Fix Unsupported Language Routing)
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

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
TEXT_FR = "Le gouvernement français a annoncé de nouvelles mesures économiques pour relancer la croissance."
TEXT_ES = "El gobierno de España ha anunciado nuevas medidas para combatir el cambio climático este año."
TEXT_DE = "Die deutsche Bundesregierung hat neue wirtschaftliche Maßnahmen angekündigt um das Wachstum zu fördern."
TEXT_JA = "日本政府は経済成長を促進するための新しい政策を発表しました。東京での記者会見で首相が述べました。"
TEXT_ZH = "中国政府宣布了一系列新的经济政策，旨在促进国内消费和经济增长，稳定金融市场。"
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

    # -- Supported languages ------------------------------------------------

    def test_detect_indonesian_returns_id(self, detector):
        result = detector.detect(TEXT_ID_SHORT)
        assert result["language"] == "id"
        assert result["supported"] is True
        assert result["language_name"] == "Indonesian"

    def test_detect_indonesian_long(self, detector):
        result = detector.detect(TEXT_ID_LONG)
        assert result["language"] == "id"
        assert result["supported"] is True

    def test_detect_english_returns_en(self, detector):
        result = detector.detect(TEXT_EN_SHORT)
        assert result["language"] == "en"
        assert result["supported"] is True
        assert result["language_name"] == "English"

    def test_detect_english_long(self, detector):
        result = detector.detect(TEXT_EN_LONG)
        assert result["language"] == "en"
        assert result["supported"] is True

    # -- Unsupported languages — raw code preserved, supported=False --------

    def test_detect_french_is_fr(self, detector):
        result = detector.detect(TEXT_FR)
        assert result["language"] == "fr", f"Expected 'fr', got '{result['language']}'"
        assert result["supported"] is False
        # CRITICAL: must NOT be converted to "en"
        assert result["language"] != "en"

    def test_detect_spanish_is_es(self, detector):
        result = detector.detect(TEXT_ES)
        assert result["language"] == "es", f"Expected 'es', got '{result['language']}'"
        assert result["supported"] is False
        assert result["language"] != "en"

    def test_detect_german_is_de(self, detector):
        result = detector.detect(TEXT_DE)
        assert result["language"] == "de", f"Expected 'de', got '{result['language']}'"
        assert result["supported"] is False
        assert result["language"] != "en"

    def test_detect_japanese_is_ja(self, detector):
        result = detector.detect(TEXT_JA)
        assert result["language"] == "ja", f"Expected 'ja', got '{result['language']}'"
        assert result["supported"] is False
        assert result["language"] != "en"

    def test_detect_chinese_is_zh(self, detector):
        result = detector.detect(TEXT_ZH)
        # langdetect may return zh-cn or zh-tw or zh
        lang = result["language"]
        assert lang.startswith("zh"), f"Expected zh*, got '{lang}'"
        assert result["supported"] is False
        assert result["language"] != "en"

    # -- Schema validation --------------------------------------------------

    def test_detect_returns_required_keys(self, detector):
        result = detector.detect(TEXT_EN_SHORT)
        required_keys = {"language", "language_name", "confidence", "method", "supported"}
        assert required_keys.issubset(result.keys())

    def test_detect_no_fallback_applied_key(self, detector):
        """Old 'fallback_applied' key must not exist — it was removed."""
        result = detector.detect(TEXT_EN_SHORT)
        assert "fallback_applied" not in result

    def test_detect_no_raw_lang_key(self, detector):
        """Old 'raw_lang' key must not exist — replaced by 'language'."""
        result = detector.detect(TEXT_EN_SHORT)
        assert "raw_lang" not in result

    def test_detect_method_is_valid(self, detector):
        result = detector.detect(TEXT_ID_LONG)
        assert result["method"] in ("langdetect", "langid")

    def test_detect_confidence_range_or_none(self, detector):
        result = detector.detect(TEXT_EN_LONG)
        if result["confidence"] is not None:
            assert 0.0 <= result["confidence"] <= 1.0

    def test_detect_too_short_raises(self, detector):
        with pytest.raises(ValueError, match="too short"):
            detector.detect(TEXT_TOO_SHORT)

    def test_detect_empty_raises(self, detector):
        with pytest.raises(ValueError):
            detector.detect("")

    def test_is_supported_true(self):
        assert LanguageDetector.is_supported("id") is True
        assert LanguageDetector.is_supported("en") is True

    def test_is_supported_false(self):
        for lang in ("es", "fr", "de", "ja", "zh", "ko", "ar"):
            assert LanguageDetector.is_supported(lang) is False

    def test_detect_language_code_returns_raw(self, detector):
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
        assert data["supported"] is True
        assert data["language_name"] == "Indonesian"

    def test_detect_english(self):
        resp = client.post("/api/language/detect", json={"text": TEXT_EN_LONG})
        assert resp.status_code == 200
        data = resp.json()
        assert data["language"] == "en"
        assert data["supported"] is True

    def test_detect_french_preserved(self):
        resp = client.post("/api/language/detect", json={"text": TEXT_FR})
        assert resp.status_code == 200
        data = resp.json()
        assert data["language"] == "fr"
        assert data["supported"] is False
        # Must NOT be silently converted
        assert data["language"] != "en"

    def test_detect_spanish_preserved(self):
        resp = client.post("/api/language/detect", json={"text": TEXT_ES})
        assert resp.status_code == 200
        data = resp.json()
        assert data["language"] == "es"
        assert data["supported"] is False

    def test_detect_german_preserved(self):
        resp = client.post("/api/language/detect", json={"text": TEXT_DE})
        assert resp.status_code == 200
        data = resp.json()
        assert data["language"] == "de"
        assert data["supported"] is False

    def test_detect_japanese_preserved(self):
        resp = client.post("/api/language/detect", json={"text": TEXT_JA})
        assert resp.status_code == 200
        data = resp.json()
        lang = data["language"]
        assert lang == "ja"
        assert data["supported"] is False

    def test_detect_chinese_preserved(self):
        resp = client.post("/api/language/detect", json={"text": TEXT_ZH})
        assert resp.status_code == 200
        data = resp.json()
        assert data["language"].startswith("zh")
        assert data["supported"] is False

    def test_detect_too_short(self):
        resp = client.post("/api/language/detect", json={"text": "Hi"})
        assert resp.status_code == 422

    def test_detect_response_schema(self):
        resp = client.post("/api/language/detect", json={"text": TEXT_EN_SHORT})
        assert resp.status_code == 200
        data = resp.json()
        for key in ("language", "language_name", "method", "supported"):
            assert key in data
        # Old fields must be gone
        assert "fallback_applied" not in data
        assert "is_supported" not in data


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

    # -- Supported languages -----------------------------------------------

    def test_analyze_id_auto_detect(self, analyzer):
        result = analyzer.analyze(TEXT_ID_LONG)
        assert result["supported"] is True
        assert result["language"]["code"] == "id"
        assert result["language"]["source"] == "auto"
        assert isinstance(result["category"]["category"], str)
        assert len(result["category"]["category"]) > 0

    def test_analyze_en_auto_detect(self, analyzer):
        result = analyzer.analyze(TEXT_EN_LONG)
        assert result["supported"] is True
        assert result["language"]["code"] == "en"

    def test_analyze_with_language_override_id(self, analyzer):
        result = analyzer.analyze(TEXT_ID_LONG, language="id")
        assert result["supported"] is True
        assert result["language"]["code"] == "id"
        assert result["language"]["source"] == "provided"
        assert result["language"]["confidence"] is None

    def test_analyze_with_language_override_en(self, analyzer):
        result = analyzer.analyze(TEXT_EN_SHORT, language="en")
        assert result["supported"] is True
        assert result["language"]["code"] == "en"
        assert result["language"]["source"] == "provided"

    def test_analyze_returns_all_keys_for_supported(self, analyzer):
        result = analyzer.analyze(TEXT_EN_SHORT, language="en")
        for key in ("supported", "language", "category", "sentiment", "keywords", "entities"):
            assert key in result

    # -- Unsupported languages: NO ML models called ------------------------

    def test_analyze_french_returns_unsupported(self, analyzer):
        result = analyzer.analyze(TEXT_FR)
        assert result["supported"] is False
        assert result["language"]["code"] == "fr"
        assert result["language"]["supported"] is False
        # No ML results
        assert "category" not in result
        assert "sentiment" not in result
        assert "entities" not in result

    def test_analyze_spanish_returns_unsupported(self, analyzer):
        result = analyzer.analyze(TEXT_ES)
        assert result["supported"] is False
        assert result["language"]["code"] == "es"

    def test_analyze_german_returns_unsupported(self, analyzer):
        result = analyzer.analyze(TEXT_DE)
        assert result["supported"] is False
        assert result["language"]["code"] == "de"

    def test_analyze_japanese_returns_unsupported(self, analyzer):
        result = analyzer.analyze(TEXT_JA)
        assert result["supported"] is False
        assert result["language"]["code"] == "ja"

    def test_analyze_chinese_returns_unsupported(self, analyzer):
        result = analyzer.analyze(TEXT_ZH)
        assert result["supported"] is False
        lang = result["language"]["code"]
        assert lang.startswith("zh")

    def test_unsupported_does_not_call_english_classifier(self, analyzer):
        """English classifier must NOT be called for unsupported language."""
        with patch("app.ai.category_classifier.get_classifier") as mock_clf:
            result = analyzer.analyze(TEXT_FR)
            mock_clf.assert_not_called()
        assert result["supported"] is False

    def test_unsupported_does_not_call_indonesian_classifier(self, analyzer):
        """Indonesian classifier must NOT be called for unsupported language."""
        with patch("app.ai.indonesian_category_classifier.get_indonesian_classifier") as mock_clf:
            result = analyzer.analyze(TEXT_ES)
            mock_clf.assert_not_called()
        assert result["supported"] is False

    def test_unsupported_does_not_call_ner(self, analyzer):
        """NER extractor must NOT be called for unsupported language."""
        with patch("app.ai.ner_extractor.get_ner_extractor") as mock_ner:
            result = analyzer.analyze(TEXT_DE)
            mock_ner.assert_not_called()
        assert result["supported"] is False

    # -- Other validations -------------------------------------------------

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
    # -- Supported languages -----------------------------------------------

    def test_analyze_english_auto(self):
        resp = client.post("/api/analyze", json={"text": TEXT_EN_LONG})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["language"]["code"] == "en"
        assert data["language"]["source"] == "auto"
        assert data["language"]["supported"] is True
        for key in ("category", "sentiment", "keywords", "entities"):
            assert key in data

    def test_analyze_indonesian_auto(self):
        resp = client.post("/api/analyze", json={"text": TEXT_ID_LONG})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["language"]["code"] == "id"
        assert data["language"]["supported"] is True

    def test_analyze_with_language_override(self):
        resp = client.post("/api/analyze", json={
            "text": TEXT_EN_SHORT,
            "language": "en"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["language"]["source"] == "provided"
        assert data["status"] == "ok"

    def test_analyze_top_keywords_param(self):
        resp = client.post("/api/analyze", json={
            "text": TEXT_EN_LONG,
            "top_keywords": 5,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["keywords"]["total"] <= 5

    # -- Unsupported languages: must return unsupported_language -----------

    def test_analyze_french_returns_unsupported_language(self):
        resp = client.post("/api/analyze", json={"text": TEXT_FR})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "unsupported_language"
        assert data["language"]["code"] == "fr"
        assert data["language"]["supported"] is False
        assert "message" in data
        # Must NOT have ML results
        assert "category" not in data
        assert "sentiment" not in data
        assert "entities" not in data

    def test_analyze_spanish_returns_unsupported_language(self):
        resp = client.post("/api/analyze", json={"text": TEXT_ES})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "unsupported_language"
        assert data["language"]["code"] == "es"

    def test_analyze_german_returns_unsupported_language(self):
        resp = client.post("/api/analyze", json={"text": TEXT_DE})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "unsupported_language"
        assert data["language"]["code"] == "de"

    def test_analyze_japanese_returns_unsupported_language(self):
        resp = client.post("/api/analyze", json={"text": TEXT_JA})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "unsupported_language"
        assert data["language"]["code"] == "ja"

    def test_analyze_chinese_returns_unsupported_language(self):
        resp = client.post("/api/analyze", json={"text": TEXT_ZH})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "unsupported_language"
        assert data["language"]["code"].startswith("zh")

    def test_analyze_unsupported_message_in_indonesian(self):
        resp = client.post("/api/analyze", json={"text": TEXT_FR})
        assert resp.status_code == 200
        data = resp.json()
        msg = data.get("message", "")
        assert len(msg) > 0
        # Message should mention supported languages
        assert "Indonesia" in msg or "Inggris" in msg

    # -- Validation errors -------------------------------------------------

    def test_analyze_invalid_language_override(self):
        resp = client.post("/api/analyze", json={
            "text": TEXT_EN_SHORT,
            "language": "fr"   # fr not allowed as override (schema validates id|en only)
        })
        assert resp.status_code == 422

    def test_analyze_too_short_text(self):
        resp = client.post("/api/analyze", json={"text": "Hi"})
        assert resp.status_code == 422

    # -- Schema validation for supported response --------------------------

    def test_analyze_response_has_status_ok(self):
        resp = client.post("/api/analyze", json={"text": TEXT_EN_LONG})
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_analyze_response_language_has_language_name(self):
        resp = client.post("/api/analyze", json={"text": TEXT_EN_LONG})
        data = resp.json()
        assert "language_name" in data["language"]
        assert data["language"]["language_name"] == "English"

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
