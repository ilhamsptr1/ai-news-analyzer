import re
file_path = 'e:/AI NEWS ANALYZER/ai-news-analyzer/backend/app/ai/multilingual_analyzer.py'
with open(file_path, 'r', encoding='utf-8') as f:
    code = f.read()

# Update signature to accept title
code = re.sub(
    r'def analyze\(\s*self,\s*text:\s*str,\s*language:\s*str\s*\|\s*None\s*=\s*None,\s*top_keywords:\s*int\s*=\s*10,\s*\)\s*->\s*dict:',
    'def analyze(\n        self,\n        text: str,\n        title: str | None = None,\n        language: str | None = None,\n        top_keywords: int = 10,\n    ) -> dict:',
    code
)

# Add clickbait step
clickbait_step = """
        # ------------------------------------------------------------------
        # 7. Clickbait Detection
        # ------------------------------------------------------------------
        clickbait_result = self._detect_clickbait(title, text, lang_code) if title else {"score": 0.0, "reasons": ["No title provided"]}

        return {
            "supported": True,
            "language": lang_info,
            "category": category_result,
            "sentiment": sentiment_result,
            "keywords": keyword_result,
            "entities": entity_result,
            "clickbait": clickbait_result,
        }
"""
code = re.sub(
    r'return \{\s*"supported": True,[\s\S]*?"entities": entity_result,\s*\}',
    clickbait_step.strip(),
    code
)

# Add private helper
private_helper = """
    def _detect_clickbait(self, title: str, text: str, lang: str) -> dict:
        \"\"\"Extract clickbait score.\"\"\"
        try:
            from app.ai.clickbait_detector import get_clickbait_detector
            detector = get_clickbait_detector()
            return detector.detect(title=title, text=text, lang=lang)
        except Exception as exc:
            logger.error("Clickbait detection error (%s): %s", lang, exc, exc_info=True)
            return {"score": 0.0, "reasons": ["Error in detection"]}

# ---------------------------------------------------------------------------
"""
code = re.sub(
    r'# ---------------------------------------------------------------------------[\r\n]+# Singleton',
    private_helper.strip() + '\n\n# ---------------------------------------------------------------------------\n# Singleton',
    code
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(code)

print('Updated multilingual analyzer')
