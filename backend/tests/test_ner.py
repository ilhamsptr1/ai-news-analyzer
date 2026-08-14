"""
Phase 4B-3 Tests — Multilingual Named Entity Recognition (NER)
"""

import sys
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app
from app.ai.ner_extractor import get_ner_extractor, NERExtractor

client = TestClient(app)

# ---------------------------------------------------------------------------
# Test Data
# ---------------------------------------------------------------------------

TEXT_ID_SHORT = "Presiden Prabowo bertemu dengan Elon Musk di Jakarta."
TEXT_EN_SHORT = "Apple CEO Tim Cook announced a new product in California."
TEXT_NO_ENTITY = "Hari ini cuacanya sangat cerah."
TEXT_DUPLICATES = "Tim Cook bekerja di Apple. Ya, Apple."


# ===========================================================================
# 1. Extractor Core Logic Tests
# ===========================================================================

class TestNERExtractorCore:
    @pytest.fixture(scope="class")
    def extractor(self):
        # We use singleton
        return get_ner_extractor()

    def test_singleton(self, extractor):
        ext2 = get_ner_extractor()
        assert extractor is ext2

    def test_extract_invalid_inputs(self, extractor):
        with pytest.raises(ValueError):
            extractor.extract("", language="id")
        
        with pytest.raises(ValueError):
            extractor.extract("Hello", language="fr")

    def test_extract_indonesian_entities(self, extractor):
        # Check extraction
        res = extractor.extract(TEXT_ID_SHORT, language="id")
        assert res["language"] == "id"
        assert res["model"] == "cahya/bert-base-indonesian-NER"
        
        ents = res["entities"]
        assert len(ents) > 0
        
        labels = [e["label"] for e in ents]
        # Should detect PER (Prabowo, Elon Musk), GPE/LOC (Jakarta)
        assert "PER" in labels
        assert "GPE" in labels or "LOC" in labels
        
        # Verify span exactly matches text
        for ent in ents:
            assert TEXT_ID_SHORT[ent["start"]:ent["end"]] == ent["text"]
            assert ent["score"] is not None

    def test_extract_english_entities(self, extractor):
        res = extractor.extract(TEXT_EN_SHORT, language="en")
        assert res["language"] == "en"
        assert res["model"] == "en_core_web_sm"
        
        ents = res["entities"]
        assert len(ents) > 0
        
        labels = [e["label"] for e in ents]
        # Tim Cook -> PERSON, Apple -> ORG, California -> GPE
        assert "PERSON" in labels
        assert "ORG" in labels
        assert "GPE" in labels
        
        for ent in ents:
            assert TEXT_EN_SHORT[ent["start"]:ent["end"]] == ent["text"]
            assert ent["score"] is None

    def test_extract_no_entity(self, extractor):
        res = extractor.extract(TEXT_NO_ENTITY, language="id")
        assert len(res["entities"]) == 0

    def test_duplicates_retained(self, extractor):
        res = extractor.extract(TEXT_DUPLICATES, language="en")
        # Apple appears twice
        apple_ents = [e for e in res["entities"] if e["text"] == "Apple"]
        assert len(apple_ents) == 2
        # Different spans
        assert apple_ents[0]["start"] != apple_ents[1]["start"]

    def test_get_unique_entities(self, extractor):
        res = extractor.extract(TEXT_DUPLICATES, language="en")
        unique = NERExtractor.get_unique_entities(res["entities"])
        apple_ents = [e for e in unique if e["text"] == "Apple"]
        # Should be deduplicated
        assert len(apple_ents) == 1

    def test_group_by_label(self, extractor):
        res = extractor.extract(TEXT_EN_SHORT, language="en")
        groups = NERExtractor.group_by_label(res["entities"])
        
        assert "PERSON" in groups
        assert "Tim Cook" in groups["PERSON"]
        
        assert "ORG" in groups
        assert "Apple" in groups["ORG"]
        
        assert "GPE" in groups
        assert "California" in groups["GPE"]

    def test_performance_indonesian(self, extractor):
        # We ensure it runs within 3 seconds for a short text
        start = time.time()
        extractor.extract(TEXT_ID_SHORT, language="id")
        elapsed = time.time() - start
        assert elapsed < 3.0

    def test_performance_english(self, extractor):
        # We ensure spaCy is fast
        start = time.time()
        extractor.extract(TEXT_EN_SHORT, language="en")
        elapsed = time.time() - start
        assert elapsed < 1.0


# ===========================================================================
# 2. API Endpoint Tests
# ===========================================================================

class TestNERApi:
    def test_extract_entities_id(self):
        response = client.post("/api/entities/extract", json={
            "text": TEXT_ID_SHORT,
            "language": "id"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["language"] == "id"
        assert data["model"] == "cahya/bert-base-indonesian-NER"
        assert len(data["entities"]) > 0
        
        # Check struct
        ent = data["entities"][0]
        assert "text" in ent
        assert "label" in ent
        assert "start" in ent
        assert "end" in ent
        assert "score" in ent

    def test_extract_entities_en(self):
        response = client.post("/api/entities/extract", json={
            "text": TEXT_EN_SHORT,
            "language": "en"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["language"] == "en"
        assert data["model"] == "en_core_web_sm"
        assert len(data["entities"]) > 0

    def test_extract_entities_invalid_language(self):
        response = client.post("/api/entities/extract", json={
            "text": TEXT_ID_SHORT,
            "language": "fr"
        })
        assert response.status_code == 422 # Pydantic validation error

    def test_extract_entities_empty_text(self):
        response = client.post("/api/entities/extract", json={
            "text": "",
            "language": "id"
        })
        assert response.status_code == 422 # min_length=3
