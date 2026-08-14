/**
 * AnalysisResult.jsx — Combines all AI analysis cards for supported languages.
 */

import { useState } from 'react';
import LanguageCard from './LanguageCard';
import CategoryCard from './CategoryCard';
import SentimentCard from './SentimentCard';
import KeywordList from './KeywordList';
import EntityList from './EntityList';

function formatDate(dateStr) {
  if (!dateStr) return null;
  try {
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric', month: 'long', day: 'numeric',
    }).format(new Date(dateStr));
  } catch {
    return null;
  }
}

function ArticleSummary({ article }) {
  const [expanded, setExpanded] = useState(false);
  const previewLength = 500;
  const content = article.content || '';
  const isLong = content.length > previewLength;
  const displayContent = expanded || !isLong
    ? content
    : content.slice(0, previewLength) + '…';

  return (
    <div className="analysis-article-card" role="article">
      {/* Source row */}
      <div className="article-result-source-row">
        <span className="article-source-badge">🌐 {article.source || 'Unknown'}</span>
        {article.author && (
          <span className="article-author-badge">✍️ {article.author}</span>
        )}
        <span className="article-source-badge" style={{ marginLeft: 'auto' }}>
          ID #{article.id}
        </span>
      </div>

      <h2 className="article-result-title">{article.title}</h2>

      {/* Meta row */}
      <div className="article-meta-grid">
        {formatDate(article.published_at) && (
          <div className="meta-chip">
            <span className="meta-chip-icon">📅</span>
            <div>
              <div className="meta-chip-label">Published</div>
              <div className="meta-chip-value">{formatDate(article.published_at)}</div>
            </div>
          </div>
        )}
        {article.word_count != null && (
          <div className="meta-chip">
            <span className="meta-chip-icon">📝</span>
            <div>
              <div className="meta-chip-label">Words</div>
              <div className="meta-chip-value">{article.word_count.toLocaleString()}</div>
            </div>
          </div>
        )}
        {article.reading_time != null && (
          <div className="meta-chip">
            <span className="meta-chip-icon">⏱️</span>
            <div>
              <div className="meta-chip-label">Read time</div>
              <div className="meta-chip-value">{article.reading_time} min</div>
            </div>
          </div>
        )}
      </div>

      <a
        href={article.url}
        target="_blank"
        rel="noopener noreferrer"
        className="article-source-link"
        aria-label="Open original article in new tab"
      >
        View original article ↗
      </a>

      <div className="article-result-divider" />

      {/* Article content preview */}
      <h3 className="article-content-label">Article Content</h3>
      <div className="article-content-text" aria-live="polite">
        {displayContent.split('\n').map((para, i) =>
          para.trim() ? <p key={i}>{para.trim()}</p> : null
        )}
      </div>
      {isLong && (
        <button
          className="article-expand-btn"
          onClick={() => setExpanded(v => !v)}
          aria-expanded={expanded}
        >
          {expanded ? '▲ Show less' : '▼ Read full article'}
        </button>
      )}
    </div>
  );
}

export default function AnalysisResult({ data }) {
  const { article, analysis } = data;

  // Build language object from flat analysis fields
  const language = {
    code: analysis.language_code || 'unknown',
    language_name: analysis.language_name || 'Unknown',
    confidence: analysis.language_confidence,
    source: 'auto',
    supported: true,
  };

  const category = {
    category: analysis.category || 'Unknown',
    confidence: analysis.category_confidence || 0,
  };

  const sentiment = {
    sentiment: analysis.sentiment || 'Neutral',
    confidence: analysis.sentiment_confidence || 0,
  };

  return (
    <div className="analysis-result-wrapper">
      {/* Saved badge */}
      <div className="analysis-saved-banner" role="status" aria-live="polite">
        <span aria-hidden="true">✅</span>
        Article and analysis saved to database &mdash; ID #{analysis.id}
      </div>

      {/* Article Summary */}
      <ArticleSummary article={article} />

      {/* AI Analysis section heading */}
      <div className="analysis-section-heading">
        <span aria-hidden="true">🤖</span> AI Analysis Results
      </div>

      {/* 2-column top row: Language + Category */}
      <div className="analysis-cards-grid analysis-cards-grid--2">
        <LanguageCard language={language} />
        <CategoryCard category={category} />
      </div>

      {/* Sentiment full-width */}
      <SentimentCard sentiment={sentiment} />

      {/* Keywords full-width */}
      <KeywordList keywords={analysis.keywords || []} />

      {/* Entities full-width */}
      <EntityList entities={analysis.entities || []} />
    </div>
  );
}
