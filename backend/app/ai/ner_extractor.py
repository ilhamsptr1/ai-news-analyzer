"""
Named Entity Recognition Extractor (Phase 4B-3)

Multilingual support for Indonesian and English.
- Indonesian: Hugging Face transformers pipeline (cahya/bert-base-indonesian-NER)
- English: spaCy (en_core_web_sm)
"""

import logging
import string
from functools import lru_cache

logger = logging.getLogger(__name__)


class NERExtractor:
    """
    Singleton wrapper for NER models.
    Lazy-loads Indonesian and English models independently to save resources.
    """

    def __init__(self):
        self._id_pipeline = None
        self._en_nlp = None

    def _load_indonesian(self):
        if self._id_pipeline is None:
            logger.info("Loading Indonesian NER model (cahya/bert-base-indonesian-NER)...")
            from transformers import pipeline
            # aggregation_strategy="simple" merges B-PER and I-PER sub-tokens properly
            self._id_pipeline = pipeline(
                "ner",
                model="cahya/bert-base-indonesian-NER",
                aggregation_strategy="simple",
            )
            logger.info("Indonesian NER model loaded.")
        return self._id_pipeline

    def _load_english(self):
        if self._en_nlp is None:
            logger.info("Loading English NER model (en_core_web_sm)...")
            import spacy
            self._en_nlp = spacy.load("en_core_web_sm")
            logger.info("English NER model loaded.")
        return self._en_nlp

    def extract(self, text: str, language: str) -> dict:
        """
        Extract named entities from the given text.

        Args:
            text: The text to analyze.
            language: "id" or "en".

        Returns:
            Dict containing language, model name, and list of entities.
        """
        if not text or not isinstance(text, str):
            raise ValueError("text must be a non-empty string")
        if language not in ("id", "en"):
            raise ValueError("language must be 'id' or 'en'")

        entities = []

        def _is_valid_entity(text: str, label: str) -> bool:
            text = text.strip()
            if len(text) <= 1:
                return False
            # Filter pure digits that are 4 characters or less (often Wikipedia noise like years or brackets)
            if text.isdigit() and len(text) <= 4:
                return False
            # Filter punctuation or whitespace only
            if all(c in string.punctuation or c.isspace() for c in text):
                return False
            return True

        if language == "id":
            model = self._load_indonesian()
            model_name = "cahya/bert-base-indonesian-NER"
            # Limit very long texts to avoid BERT 512 token limits causing crashes
            # 2000 chars is usually safe for ~512 subwords in Indonesian
            safe_text = text[:2000]
            
            raw_ents = model(safe_text)
            for ent in raw_ents:
                start_idx = ent["start"]
                end_idx = ent["end"]
                text_slice = safe_text[start_idx:end_idx]
                label = ent["entity_group"]
                
                if _is_valid_entity(text_slice, label):
                    entities.append({
                        "text": text_slice,
                        "label": label,
                        "start": start_idx,
                        "end": end_idx,
                        "score": round(float(ent["score"]), 4),
                    })
        else:
            model = self._load_english()
            model_name = "en_core_web_sm"
            # spaCy can handle larger texts, up to ~1,000,000 chars by default, but we enforce 500,000 in schema
            doc = model(text)
            for ent in doc.ents:
                if _is_valid_entity(ent.text, ent.label_):
                    entities.append({
                        "text": ent.text,
                        "label": ent.label_,
                        "start": ent.start_char,
                        "end": ent.end_char,
                        "score": None,  # spaCy does not easily expose NER confidence out of the box
                    })

        # Deduplicate entities before returning
        unique_entities = self.get_unique_entities(entities)

        return {
            "language": language,
            "model": model_name,
            "entities": unique_entities,
        }

    @staticmethod
    def get_unique_entities(entities: list[dict]) -> list[dict]:
        """
        Deduplicates a list of entities based on text and label, keeping the one with the highest score.
        Case-insensitive for text matching, but preserves the original casing.
        """
        unique = {}
        for ent in entities:
            # Normalize key for deduplication
            norm_text = ent["text"].strip().lower()
            norm_label = ent["label"].upper()
            key = (norm_text, norm_label)
            
            if key not in unique:
                unique[key] = ent
            else:
                # If existing score is None, or new score is higher, replace
                existing_score = unique[key].get("score")
                new_score = ent.get("score")
                
                if new_score is not None:
                    if existing_score is None or new_score > existing_score:
                        unique[key] = ent

        return list(unique.values())

    @staticmethod
    def group_by_label(entities: list[dict]) -> dict[str, list[str]]:
        """
        Groups unique entity texts by their label.
        
        Returns:
            {"PERSON": ["Prabowo", "Elon Musk"], "ORG": ["Apple"]}
        """
        unique_ents = NERExtractor.get_unique_entities(entities)
        groups = {}
        for ent in unique_ents:
            label = ent["label"]
            if label not in groups:
                groups[label] = []
            if ent["text"] not in groups[label]:
                groups[label].append(ent["text"])
        return groups


@lru_cache(maxsize=1)
def get_ner_extractor() -> NERExtractor:
    """Singleton getter for NERExtractor."""
    return NERExtractor()
