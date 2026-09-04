/**
 * AnalysisResult.jsx — Combines all AI analysis cards for supported languages.
 */

import { useState } from 'react';
import LanguageCard from './LanguageCard';
import CategoryCard from './CategoryCard';
import SentimentCard from './SentimentCard';
import KeywordList from './KeywordList';
import EntityList from './EntityList';
import ClickbaitCard from './ClickbaitCard';
import ObjectivityCard from './ObjectivityCard';
import PodcastPlayer from './PodcastPlayer';

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
        <span className="article-source-badge">{article.source || 'Unknown source'}</span>
        {article.author && (
          <span className="article-author-badge">{article.author}</span>
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
            <div className="meta-chip-label">Diterbitkan</div>
            <div className="meta-chip-value">{formatDate(article.published_at)}</div>
          </div>
        )}
        {article.word_count != null && (
          <div className="meta-chip">
            <div className="meta-chip-label">Kata</div>
            <div className="meta-chip-value">{article.word_count.toLocaleString()}</div>
          </div>
        )}
        {article.reading_time != null && (
          <div className="meta-chip">
            <div className="meta-chip-label">Waktu baca</div>
            <div className="meta-chip-value">{article.reading_time} mnt</div>
          </div>
        )}
      </div>

      <a
        href={article.url}
        target="_blank"
        rel="noopener noreferrer"
        className="article-source-link"
        aria-label="Buka artikel asli di tab baru"
      >
        Lihat artikel asli ↗
      </a>

      <div className="article-result-divider" />

      {/* Article content preview */}
      <h3 className="article-content-label">Konten Artikel</h3>
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
          {expanded ? '▲ Tampilkan lebih sedikit' : '▼ Baca artikel lengkap'}
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
      {/* Header controls: Saved badge + Print button */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div className="analysis-saved-banner" style={{ margin: 0 }} role="status" aria-live="polite">
          <span aria-hidden="true">✅</span>
          Artikel dan analisis disimpan ke database &mdash; ID #{analysis.id}
        </div>
        
        <button 
          onClick={() => window.print()} 
          className="btn-secondary hide-on-print" 
          style={{ display: 'inline-flex', gap: '8px', alignItems: 'center', padding: '8px 16px', background: '#fff', border: '1px solid var(--border-color)', color: 'var(--ink)' }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="7 10 12 15 17 10"></polyline>
            <line x1="12" y1="15" x2="12" y2="3"></line>
          </svg>
          Unduh Laporan (PDF)
        </button>
      </div>

      {/* Article Summary */}
      <ArticleSummary article={article} />

      <PodcastPlayer article={article} analysis={analysis} />

      {/* AI Analysis section heading */}
      <div className="analysis-section-heading">
        Hasil Analisis AI
      </div>

      {/* 2-column top row: Language + Category */}
      <div className="analysis-cards-grid analysis-cards-grid--2">
        <LanguageCard language={language} />
        <CategoryCard category={category} />
      </div>

      {/* 2-column middle row: Clickbait + Objectivity */}
      <div className="analysis-cards-grid analysis-cards-grid--2">
        <ClickbaitCard score={analysis.clickbait_score || analysis?.clickbait?.score || 0} reasons={analysis?.clickbait?.reasons || []} />
        <ObjectivityCard score={analysis.objectivity_score ?? analysis?.objectivity?.score ?? 0.5} details={analysis.objectivity_details || analysis?.objectivity?.details || {}} />
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
