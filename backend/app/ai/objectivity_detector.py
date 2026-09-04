import re
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

OPINION_MARKERS_ID = [
    r"\bmenurut saya\b", r"\bmenurut kami\b", r"\bopini\b", r"\bpendapat\b", 
    r"\bseharusnya\b", r"\bsemestinya\b", r"\bsebaiknya\b", r"\bmungkin\b", 
    r"\bdiduga\b", r"\bsepertinya\b", r"\btampaknya\b", r"\bdiyakini\b",
    r"\bsangat buruk\b", r"\bmengerikan\b", r"\bluar biasa\b", r"\bmemalukan\b",
    r"\bhebat\b", r"\bterbaik\b", r"\bterburuk\b", r"\bgila\b", r"\bbodoh\b"
]

FACTUAL_MARKERS_ID = [
    r"\bberdasarkan data\b", r"\bmenurut laporan\b", r"\bmengatakan bahwa\b",
    r"\bmenyatakan\b", r"\bmelaporkan\b", r"\bdikutip dari\b", r"\bdilansir\b",
    r"\btahun 20\d\d\b", r"\b\d+\%\b", r"\brp\s?\d+\b", r"\bsekitar \d+\b",
    r"\btanggal \d+\b"
]

OPINION_MARKERS_EN = [
    r"\bin my opinion\b", r"\bi think\b", r"\bi believe\b", r"\bwe think\b",
    r"\bshould\b", r"\bprobably\b", r"\ballegedly\b", r"\bseems like\b", 
    r"\bappears to\b", r"\bterrible\b", r"\bawful\b", r"\bamazing\b", r"\bshameful\b",
    r"\bgreatest\b", r"\bworst\b", r"\bcrazy\b", r"\bstupid\b", r"\bawesome\b"
]

FACTUAL_MARKERS_EN = [
    r"\baccording to data\b", r"\breported\b", r"\bstated\b", r"\bannounced\b",
    r"\bcited\b", r"\bresearch shows\b", r"\bin 20\d\d\b", r"\b\d+\%\b",
    r"\b\$\d+\b", r"\bapproximate\b", r"\bon \w+ \d+\b"
]

class ObjectivityDetector:
    def detect(self, text: str, lang: str) -> dict:
        if not text:
            return {"score": 0.5, "details": {"opinion_count": 0, "factual_count": 0, "reason": "No text provided"}}

        text_lower = text.lower()
        
        op_markers = OPINION_MARKERS_ID if lang == "id" else OPINION_MARKERS_EN
        fact_markers = FACTUAL_MARKERS_ID if lang == "id" else FACTUAL_MARKERS_EN

        opinion_hits = []
        factual_hits = []

        for marker in op_markers:
            matches = re.finditer(marker, text_lower)
            for m in matches:
                opinion_hits.append(m.group(0))

        for marker in fact_markers:
            matches = re.finditer(marker, text_lower)
            for m in matches:
                factual_hits.append(m.group(0))

        # Basic quotation check as factual indicator
        quotes = len(re.findall(r'["\'](.*?)["\']', text))
        if quotes > 0:
            factual_hits.append(f"{quotes} kutipan langsung")

        opinion_count = len(opinion_hits)
        factual_count = len(factual_hits)
        
        # Calculate ratio. 
        # Base is 0.5 (Neutral). Each factual marker pushes towards 1.0. Each opinion marker pushes towards 0.0.
        score = 0.5
        score += (factual_count * 0.1)
        score -= (opinion_count * 0.15) # Opinion markers are weighed more heavily
        
        # Clamp between 0.0 and 1.0
        score = max(0.0, min(1.0, score))
        
        reasons = []
        if score >= 0.7:
            reasons.append("Teks menggunakan banyak kutipan langsung dan/atau referensi data.")
        elif score <= 0.4:
            reasons.append("Teks mengandung bahasa subjektif atau opini personal yang kuat.")
        else:
            reasons.append("Teks memiliki campuran antara gaya pelaporan faktual dan opini.")

        return {
            "score": round(score, 2),
            "details": {
                "opinion_count": opinion_count,
                "factual_count": factual_count,
                "opinion_indicators_found": list(set(opinion_hits)),
                "factual_indicators_found": list(set(factual_hits)),
                "reasons": reasons
            }
        }

@lru_cache(maxsize=1)
def get_objectivity_detector() -> ObjectivityDetector:
    return ObjectivityDetector()
