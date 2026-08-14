/**
 * NewsAnalyzer.jsx — Main orchestrating component for Phase 5C-1.
 * URL input → analyzeArticle → show result / unsupported / error.
 */

import { useState } from 'react';
import { analyzeArticle } from '../services/api';
import AnalysisResult from './AnalysisResult';
import LanguageCard from './LanguageCard';

// ─── Error message helper ────────────────────────────────────────────────────

function getErrorMessage(err) {
  if (!err) return 'An unexpected error occurred.';
  const { status, detail } = err;
  if (status === 400) return `Invalid or blocked URL: ${detail}`;
  if (status === 422) return 'Article content could not be extracted. The page may require JavaScript or be behind a paywall.';
  if (status === 502) return 'Could not reach the article website. The server may be unavailable.';
  if (status === 504) return 'Request timed out. The website took too long to respond.';
  if (status === 500) return 'A server error occurred. Please try again later.';
  return detail || 'Analysis failed. Please try again.';
}

// ─── Loading skeleton ─────────────────────────────────────────────────────────

function LoadingState() {
  return (
    <div className="analyzer-loading" role="status" aria-live="polite">
      <div className="analyzer-loading-ring" aria-hidden="true">
        <div /><div /><div /><div />
      </div>
      <div className="analyzer-loading-text">
        <span className="analyzer-loading-title">Analyzing article…</span>
        <span className="analyzer-loading-sub">
          Extracting content · Detecting language · Running AI models
        </span>
      </div>
      {/* Skeleton cards */}
      <div className="skeleton-grid">
        <div className="skeleton-card" aria-hidden="true">
          <div className="skeleton-line skeleton-line--sm" />
          <div className="skeleton-line" />
          <div className="skeleton-line skeleton-line--md" />
        </div>
        <div className="skeleton-card" aria-hidden="true">
          <div className="skeleton-line skeleton-line--sm" />
          <div className="skeleton-line" />
          <div className="skeleton-line skeleton-line--md" />
        </div>
      </div>
    </div>
  );
}

// ─── Unsupported language state ───────────────────────────────────────────────

function UnsupportedLanguageState({ data, onReset }) {
  return (
    <div className="analyzer-unsupported" role="alert" aria-live="assertive">
      <div className="analyzer-unsupported-icon" aria-hidden="true">🌐</div>
      <h3 className="analyzer-unsupported-title">Language Not Supported</h3>
      <p className="analyzer-unsupported-message">
        {data.message || 'Bahasa artikel ini belum didukung.'}
      </p>
      <p className="analyzer-unsupported-hint">
        AI News Analyzer currently supports <strong>Bahasa Indonesia</strong> and <strong>English</strong>.
      </p>

      {/* Show detected language */}
      {data.language && (
        <div className="analyzer-unsupported-lang">
          <LanguageCard language={data.language} />
        </div>
      )}

      <button
        className="analyzer-new-btn"
        onClick={onReset}
        aria-label="Try another article"
      >
        ← Try Another URL
      </button>
    </div>
  );
}

// ─── Error state ──────────────────────────────────────────────────────────────

function ErrorState({ error, onReset }) {
  return (
    <div className="extractor-error" role="alert" aria-live="assertive">
      <div className="extractor-error-icon" aria-hidden="true">⚠️</div>
      <div className="extractor-error-body">
        <h3 className="extractor-error-title">Analysis Failed</h3>
        <p className="extractor-error-message">{getErrorMessage(error)}</p>
      </div>
      <button className="extractor-retry-btn" onClick={onReset}>
        Try Again
      </button>
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

export default function NewsAnalyzer() {
  const [url, setUrl] = useState('');
  const [status, setStatus] = useState('idle'); // idle | loading | success | unsupported | error
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  async function handleAnalyze(e) {
    e.preventDefault();
    const trimmed = url.trim();
    if (!trimmed) return;

    setStatus('loading');
    setResult(null);
    setError(null);

    try {
      const data = await analyzeArticle(trimmed);

      if (data.status === 'unsupported_language') {
        setResult(data);
        setStatus('unsupported');
      } else {
        setResult(data);
        setStatus('success');
      }
    } catch (err) {
      setError(err);
      setStatus('error');
    }
  }

  function handleReset() {
    setUrl('');
    setStatus('idle');
    setResult(null);
    setError(null);
  }

  return (
    <section className="extractor-section" aria-labelledby="analyzer-heading">
      {/* Header */}
      <div className="extractor-header">
        <div className="extractor-eyebrow">
          <span className="extractor-eyebrow-dot" aria-hidden="true" />
          Phase 5C — Full AI Analysis Pipeline
        </div>
        <h2 id="analyzer-heading" className="extractor-title">
          Understand Every Story
        </h2>
        <p className="extractor-subtitle">
          Paste a public news article URL. AI News Analyzer will extract the article,
          detect the language, classify its category, analyze sentiment, extract
          keywords, and identify named entities — all automatically.
        </p>
      </div>

      {/* URL input form */}
      <form
        className="extractor-form"
        onSubmit={handleAnalyze}
        aria-label="Article analysis form"
        noValidate
      >
        <div className="extractor-input-group">
          <label htmlFor="analyzer-url-input" className="extractor-label">
            Article URL
          </label>
          <div className="extractor-input-row">
            <input
              id="analyzer-url-input"
              type="url"
              className={`extractor-input ${status === 'error' ? 'extractor-input--error' : ''}`}
              placeholder="https://example.com/news/article-title"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              disabled={status === 'loading'}
              required
              aria-required="true"
              aria-describedby="analyzer-hint"
              autoComplete="url"
            />
            <button
              id="analyze-button"
              type="submit"
              className="extractor-btn"
              disabled={status === 'loading' || !url.trim()}
              aria-busy={status === 'loading'}
            >
              {status === 'loading' ? (
                <>
                  <span className="extractor-spinner" aria-hidden="true" />
                  Analyzing…
                </>
              ) : (
                '🤖 Analyze Article'
              )}
            </button>
          </div>
          <p id="analyzer-hint" className="extractor-hint">
            Only public URLs are supported. Indonesian and English articles are fully supported.
          </p>
        </div>
      </form>

      {/* States */}
      {status === 'loading' && <LoadingState />}

      {status === 'error' && (
        <ErrorState error={error} onReset={handleReset} />
      )}

      {status === 'unsupported' && result && (
        <UnsupportedLanguageState data={result} onReset={handleReset} />
      )}

      {status === 'success' && result && (
        <>
          <AnalysisResult data={result} />
          <button
            className="analyzer-new-btn"
            onClick={handleReset}
            aria-label="Analyze another article"
          >
            ＋ Analyze Another Article
          </button>
        </>
      )}
    </section>
  );
}
