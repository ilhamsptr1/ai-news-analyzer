import re

file_path = 'e:/AI NEWS ANALYZER/ai-news-analyzer/backend/app/models/analysis.py'
with open(file_path, 'r', encoding='utf-8') as f:
    code = f.read()

# Add clickbait score after sentiment_confidence
code = re.sub(
    r'sentiment_confidence: Mapped\[float \| None\] = mapped_column\(Float, nullable=True\)',
    'sentiment_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)\n    \n    clickbait_score: Mapped[float | None] = mapped_column(Float, nullable=True)',
    code
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(code)

print('Added clickbait_score to Analysis model')
