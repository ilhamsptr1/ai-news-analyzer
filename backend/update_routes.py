import re

f = 'e:/AI NEWS ANALYZER/ai-news-analyzer/backend/app/routes/articles.py'
with open(f, 'r', encoding='utf-8') as file:
    code = file.read()

# Pass title to analyze
code = re.sub(
    r'analysis_result = analyzer\.analyze\(text=article\.content, top_keywords=payload\.top_keywords\)',
    'analysis_result = analyzer.analyze(text=article.content, title=article.title, top_keywords=payload.top_keywords)',
    code
)

# Add clickbait_score to AnalysisCreate payload
cb_payload = """
    analysis_payload = AnalysisCreate(
        article_id=article.id,
        language_code=analysis_result["language"]["code"],
        language_name=analysis_result["language"]["language_name"],
        language_confidence=analysis_result["language"]["confidence"],
        category=analysis_result["category"]["category"],
        category_confidence=analysis_result["category"]["confidence"],
        sentiment=analysis_result["sentiment"]["sentiment"],
        sentiment_confidence=analysis_result["sentiment"]["confidence"],
        clickbait_score=analysis_result.get("clickbait", {}).get("score", 0.0),
"""
code = re.sub(
    r'analysis_payload = AnalysisCreate\([\s\S]*?sentiment_confidence=analysis_result\["sentiment"\]\["confidence"\],',
    cb_payload.strip(),
    code
)

with open(f, 'w', encoding='utf-8') as file:
    file.write(code)

f2 = 'e:/AI NEWS ANALYZER/ai-news-analyzer/backend/app/routes/analyze.py'
with open(f2, 'r', encoding='utf-8') as file:
    code = file.read()

# Add ClickbaitResult to imports
code = re.sub(
    r'CategoryResult,',
    'CategoryResult,\n    ClickbaitResult,',
    code
)

# Pass title (optional, AnalyzeRequest doesn't have it but if we add it, wait, AnalyzeRequest doesn't have title, but we can just let it be None)
# Add clickbait to AnalyzeResponse
cb_response = """
        entities=EntitiesInfo(
            entities=[
                EntityItem(
                    text=ent["text"],
                    label=ent["label"],
                    start=ent["start"],
                    end=ent["end"],
                    score=ent.get("score"),
                )
                for ent in ent_data.get("entities", [])
            ],
            model=ent_data.get("model", ""),
        ),
        clickbait=ClickbaitResult(
            score=result.get("clickbait", {}).get("score", 0.0),
            reasons=result.get("clickbait", {}).get("reasons", [])
        )
    )
"""
code = re.sub(
    r'entities=EntitiesInfo\([\s\S]*?\),\s*\)',
    cb_response.strip(),
    code
)

with open(f2, 'w', encoding='utf-8') as file:
    file.write(code)

print("Updated routes")
