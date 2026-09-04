import re

f = 'e:/AI NEWS ANALYZER/ai-news-analyzer/frontend/src/components/AnalysisResult.jsx'
with open(f, 'r', encoding='utf-8') as file:
    code = file.read()

# Add import
code = re.sub(
    r'import EntityList from \'./EntityList\';',
    'import EntityList from \'./EntityList\';\nimport ClickbaitCard from \'./ClickbaitCard\';',
    code
)

# Add Clickbait rendering
cb_render = """
      {/* 2-column top row: Language + Category */}
      <div className="analysis-cards-grid analysis-cards-grid--2">
        <LanguageCard language={language} />
        <CategoryCard category={category} />
      </div>

      {/* Clickbait full-width */}
      <ClickbaitCard score={analysis.clickbait_score || analysis?.clickbait?.score || 0} reasons={analysis?.clickbait?.reasons || []} />
"""
code = re.sub(
    r'\{/\* 2-column top row: Language \+ Category \*/\}[\s\S]*?<CategoryCard category=\{category\} />\s*</div>',
    cb_render.strip(),
    code
)

with open(f, 'w', encoding='utf-8') as file:
    file.write(code)

print("Updated AnalysisResult.jsx")
