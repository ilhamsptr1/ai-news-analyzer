import re

# Update schemas/analysis.py
f1 = 'e:/AI NEWS ANALYZER/ai-news-analyzer/backend/app/schemas/analysis.py'
with open(f1, 'r', encoding='utf-8') as f:
    code = f.read()

code = re.sub(
    r'sentiment_confidence: float \| None = Field\(default=None, ge=0\.0, le=1\.0\)',
    'sentiment_confidence: float | None = Field(default=None, ge=0.0, le=1.0)\n    clickbait_score: float | None = Field(default=None, ge=0.0, le=1.0)',
    code
)

code = re.sub(
    r'sentiment_confidence: float \| None(\n\s*summary:)',
    'sentiment_confidence: float | None\n    clickbait_score: float | None\1',
    code
)

with open(f1, 'w', encoding='utf-8') as f:
    f.write(code)


# Update schemas/analyze.py
f2 = 'e:/AI NEWS ANALYZER/ai-news-analyzer/backend/app/schemas/analyze.py'
with open(f2, 'r', encoding='utf-8') as f:
    code2 = f.read()

clickbait_schema = """
class ClickbaitResult(BaseModel):
    score: float = Field(..., description="Clickbait score (0 to 1)")
    reasons: list[str] = Field(default_factory=list, description="Reasons for the score")
"""
code2 = re.sub(
    r'class KeywordResult\(BaseModel\):',
    clickbait_schema.strip() + '\n\nclass KeywordResult(BaseModel):',
    code2
)

code2 = re.sub(
    r'entities: EntitiesInfo',
    'entities: EntitiesInfo\n    clickbait: ClickbaitResult | None = None',
    code2
)

with open(f2, 'w', encoding='utf-8') as f:
    f.write(code2)

print('Updated schemas')
