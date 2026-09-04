/**
 * ArticleExtractor.jsx — Article extraction UI component.
 * Phase 3: URL input → extract → display article content.
 * No AI analysis UI — that's Phase 4+.
 */

import { useState } from 'react';
import { extractArticle } from '../services/api';

// ─── Helpers ────────────────────────────────────────────────────────────────

function formatDate(dateStr) {
  if (!dateStr) return null;
  try {
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    }).format(new Date(dateStr));
  } catch {
    return null;
  }
}

function getErrorMessage(err) {
  if (!err) return 'An unexpected error occurred.';
  const status = err.status;
  const detail = err.detail;

  if (status === 400) return `Invalid URL: ${detail}`;
  if (status === 422) return 'Article content could not be extracted. The page may require JavaScript or be behind a paywall.';
  if (status === 502) return 'Could not reach the article website. Please check the URL and try again.';
  if (status === 504) return 'Request timed out. The website took too long to respond.';
  return detail || 'Failed to extract article. Please try again.';
}

// ─── Sub-components ──────────────────────────────────────────────────────────

function MetaChip({ icon, label, value }) {
  if (!value && value !== 0) return null;
  return (
    <div className="meta-chip">
      <span className="meta-chip-icon" aria-hidden="true">{icon}</span>
      <div>
        <div className="meta-chip-label">{label}</div>
        <div className="meta-chip-value">{value}</div>
      </div>
    </div>
  );
}

function ArticleResult({ article }) {
  const [expanded, setExpanded] = useState(false);
  const previewLength = 600;
  const isLong = article.content.length > previewLength;
  const displayContent = expanded || !isLong
    ? article.content
    : article.content.slice(0, previewLength) + '…';

  return (
    <div className="article-result" role="article" aria-label="Extracted article">
      {/* Header */}
      <div className="article-result-header">
        <div className="article-result-source-row">
          <span className="article-source-badge">
            🌐 {article.source || 'Unknown Source'}
          </span>
          {article.author && (
            <span className="article-author-badge">
              ✍️ {article.author}
            </span>
          )}
        </div>
        <h2 className="article-result-title">{article.title}</h2>

        {/* Meta chips */}
        <div className="article-meta-grid" role="list" aria-label="Article metadata">
          <MetaChip
            icon="📅"
            label="Published"
            value={formatDate(article.published_at) || 'Date unknown'}
          />
          <MetaChip icon="📝" label="Words" value={article.word_count?.toLocaleString()} />
          <MetaChip
            icon="⏱️"
            label="Read time"
            value={article.reading_time ? `${article.reading_time} min` : null}
          />
          <MetaChip icon="🗃️" label="Article ID" value={`#${article.id}`} />
        </div>

        {/* Source URL link */}
        <a
          href={article.url}
          target="_blank"
          rel="noopener noreferrer"
          className="article-source-link"
          aria-label="Open original article in new tab"
        >
          View original article ↗
        </a>
      </div>

      {/* Divider */}
      <div className="article-result-divider" role="separator" />

      {/* Content */}
      <div className="article-content-area">
        <h3 className="article-content-label">Konten Mentah</h3>
        <div className="article-content-text" aria-live="polite">
          {displayContent.split('\n').map((para, i) =>
            para.trim() ? <p key={i}>{para.trim()}</p> : null
          )}
        </div>
        {isLong && (
          <button
            className="article-expand-btn"
            onClick={() => setExpanded((v) => !v)}
            aria-expanded={expanded}
          >
            {expanded ? '▲ Show less' : '▼ Read full article'}
          </button>
        )}
      </div>

      {/* Save indicator */}
      <div className="article-saved-badge" role="status">
        ✅ Saved to database
      </div>
    </div>
  );
}

// ─── Main Component ──────────────────────────────────────────────────────────

export default function ArticleExtractor() {
  const [url, setUrl] = useState('');
  const [status, setStatus] = useState('idle'); // idle | loading | success | error
  const [article, setArticle] = useState(null);
  const [error, setError] = useState(null);
  const [isDuplicate, setIsDuplicate] = useState(false);

  async function handleExtract(e) {
    e.preventDefault();
    if (!url.trim()) return;

    setStatus('loading');
    setArticle(null);
    setError(null);
    setIsDuplicate(false);

    try {
      // We need to detect the 200 (duplicate) vs 201 (new) case
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/articles/extract`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url: url.trim() }),
        }
      );

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw { status: response.status, detail: data.detail };
      }

      setArticle(data);
      setIsDuplicate(response.status === 200);
      setStatus('success');
    } catch (err) {
      setError(err);
      setStatus('error');
    }
  }

  function handleReset() {
    setUrl('');
    setStatus('idle');
    setArticle(null);
    setError(null);
    setIsDuplicate(false);
  }

  return (
    <section className="extractor-container" aria-labelledby="extractor-heading">
      <div className="extractor-card">
      {/* Section heading */}
      <div className="extractor-header">
        <div className="extractor-eyebrow">
          <span className="extractor-eyebrow-dot" aria-hidden="true" />
          Phase 3 — Article Extraction
        </div>
        <h2 id="extractor-heading" className="extractor-title">
          Ekstrak Artikel
        </h2>
        <p className="extractor-subtitle">
          Hanya ekstrak konten dari sebuah artikel berita. Analisis AI tidak akan dijalankan.
        </p>
      </div>

      {/* URL Input Form */}
      <form
        className="extractor-form"
        onSubmit={handleExtract}
        aria-label="Article extraction form"
        noValidate
      >
        <div className="extractor-input-group">
          <label htmlFor="article-url-input" className="extractor-label">
            Article URL
          </label>
          <div className="extractor-input-row">
            <input
              id="article-url-input"
              type="url"
              className={`extractor-input ${status === 'error' ? 'extractor-input--error' : ''}`}
              placeholder="https://example.com/news/article-title"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              disabled={status === 'loading'}
              required
              aria-required="true"
              aria-describedby="extractor-hint"
              autoComplete="url"
            />
            <button
              id="extract-button"
              type="submit"
              className="extractor-btn"
              disabled={status === 'loading' || !url.trim()}
              aria-busy={status === 'loading'}
            >
              {status === 'loading' ? (
                <>
                  <span className="extractor-spinner" aria-hidden="true" />
                  Mengekstrak…
                </>
              ) : (
                'Ekstrak Konten'
              )}
            </button>
          </div>
          <p id="extractor-hint" className="extractor-hint">
            Only public URLs are supported. Paywalled or JavaScript-only pages may not extract correctly.
          </p>
        </div>
      </form>

      {/* Loading State */}
      {status === 'loading' && (
        <div className="extractor-loading" role="status" aria-live="polite">
          <div className="extractor-loading-ring" aria-hidden="true">
            <div /><div /><div /><div />
          </div>
          <div className="extractor-loading-text">
            <span className="extractor-loading-title">Extracting article…</span>
            <span className="extractor-loading-sub">Fetching content, cleaning HTML, and extracting metadata</span>
          </div>
        </div>
      )}

      {/* Error State */}
      {status === 'error' && error && (
        <div className="extractor-error" role="alert" aria-live="assertive">
          <div className="extractor-error-icon" aria-hidden="true">⚠️</div>
          <div className="extractor-error-body">
            <h3 className="extractor-error-title">Extraction Failed</h3>
            <p className="extractor-error-message">{getErrorMessage(error)}</p>
          </div>
          <button
            className="extractor-retry-btn"
            onClick={handleReset}
            aria-label="Try again with a different URL"
          >
            Try Again
          </button>
        </div>
      )}

      {/* Duplicate notice */}
      {status === 'success' && isDuplicate && (
        <div className="extractor-duplicate-notice" role="status" aria-live="polite">
          <span aria-hidden="true">ℹ️</span>
          This article was already in the database. Showing existing record.
        </div>
      )}

      {/* Success State */}
      {status === 'success' && article && (
        <>
          <ArticleResult article={article} />
          <button
            className="extractor-new-btn"
            onClick={handleReset}
            aria-label="Extract another article"
          >
            ← Ekstrak Artikel Lain
          </button>
        </>
      )}
      </div>
    </section>
  );
}
