"""
Clickbait Detector — Heuristic approach.
"""

import re
import logging

logger = logging.getLogger(__name__)

# Trigger words in Indonesian and English
TRIGGER_WORDS_ID = [
    r"\bmengejutkan\b", r"\bviral\b", r"\bgeger\b", r"\bbikin heboh\b", 
    r"\balasan kenapa\b", r"\binilah\b", r"\bterungkap\b", r"\bbongkar\b",
    r"\bfakta mengejutkan\b", r"\bkamu tidak akan percaya\b", r"\bjangan sampai\b"
]

TRIGGER_WORDS_EN = [
    r"\bshocking\b", r"\bviral\b", r"\bmind-blowing\b", r"\byou won't believe\b",
    r"\bthis is why\b", r"\breason why\b", r"\bsecret to\b", r"\bwhat happens next\b",
    r"\bunbelievable\b", r"\bgone wrong\b"
]

class ClickbaitDetector:
    def detect(self, title: str, text: str, lang: str) -> dict:
        if not title:
            return {"score": 0.0, "reason": "No title provided"}

        score = 0.0
        reasons = []

        # 1. Punctuation Abuse
        if re.search(r"[!]{2,}", title) or re.search(r"[\?]{2,}", title) or re.search(r"\?!", title):
            score += 0.3
            reasons.append("Punctuation abuse (e.g., !!! or ???)")
        elif "?" in title:
            score += 0.1
            reasons.append("Question in title")

        # 2. Capitalization Abuse (All Caps words, excluding small acronyms)
        words = title.split()
        caps_words = [w for w in words if w.isupper() and len(w) > 3]
        if len(caps_words) > 1:
            score += 0.2
            reasons.append("Multiple all-caps words")
        elif title.isupper():
            score += 0.5
            reasons.append("Title is completely capitalized")

        # 3. Provocative trigger words
        triggers = TRIGGER_WORDS_ID if lang == "id" else TRIGGER_WORDS_EN
        title_lower = title.lower()
        trigger_count = sum(1 for pattern in triggers if re.search(pattern, title_lower))
        if trigger_count > 0:
            score += min(0.4, trigger_count * 0.2)
            reasons.append(f"Contains {trigger_count} clickbait trigger word(s)")

        # 4. Length mismatch (Title very long, content very short)
        title_len = len(title)
        text_len = len(text)
        if title_len > 100 and text_len < 500:
            score += 0.2
            reasons.append("Long title but very short content")

        # Normalize score
        final_score = min(1.0, max(0.0, score))
        
        return {
            "score": final_score,
            "reasons": reasons
        }

def get_clickbait_detector() -> ClickbaitDetector:
    return ClickbaitDetector()
