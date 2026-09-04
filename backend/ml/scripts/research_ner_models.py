"""
Research NER Models for Indonesian and English.
"""
import io, sys, time
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import spacy
from transformers import pipeline

def test_english():
    print("Testing English SpaCy (en_core_web_sm)...")
    try:
        nlp_en = spacy.load("en_core_web_sm")
        text = "Apple CEO Tim Cook announced a new product in California."
        t0 = time.time()
        doc = nlp_en(text)
        t1 = time.time()
        print(f"Time: {t1-t0:.4f}s")
        for ent in doc.ents:
            print(f"  {ent.text} -> {ent.label_}")
    except Exception as e:
        print(f"Failed to load en_core_web_sm: {e}")

def test_indonesian_hf():
    print("\nTesting Indonesian Hugging Face (cahya/bert-base-indonesian-NER)...")
    try:
        ner_id = pipeline("ner", model="cahya/bert-base-indonesian-NER", aggregation_strategy="simple")
        text = "Presiden Prabowo bertemu dengan Elon Musk di Jakarta."
        t0 = time.time()
        res = ner_id(text)
        t1 = time.time()
        print(f"Time: {t1-t0:.4f}s")
        for ent in res:
            print(f"  {ent['word']} -> {ent['entity_group']} ({ent['score']:.4f})")
    except Exception as e:
        print(f"Failed HF model: {e}")
        
if __name__ == "__main__":
    test_english()
    test_indonesian_hf()
