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
  if (!err) return 'Terjadi kesalahan tidak terduga.';
  return err.detail || 'Analisis gagal. Silakan coba lagi.';
}

// ─── Loading skeleton ─────────────────────────────────────────────────────────

function LoadingState() {
  return (
    <div className="analyzer-loading" role="status" aria-live="polite">
      <div className="analyzer-loading-ring" aria-hidden="true">
        <div /><div /><div /><div />
      </div>
      <div className="analyzer-loading-text">
        <span className="analyzer-loading-title">Menganalisis artikel…</span>
        <span className="analyzer-loading-sub">
          Mengekstrak konten · Mendeteksi bahasa · Menjalankan model AI
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
      <h3 className="analyzer-unsupported-title">Bahasa Tidak Didukung</h3>
      <p className="analyzer-unsupported-message">
        {data.message || 'Bahasa artikel ini belum didukung.'}
      </p>
      <p className="analyzer-unsupported-hint">
        AI News Analyzer saat ini mendukung <strong>Bahasa Indonesia</strong> dan <strong>Bahasa Inggris</strong>.
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
        aria-label="Coba URL lain"
      >
        ← Coba URL Lain
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
        <h3 className="extractor-error-title">Analisis Gagal</h3>
        <p className="extractor-error-message">{getErrorMessage(error)}</p>
      </div>
      <button className="extractor-retry-btn" onClick={onReset}>
        Coba Lagi
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
    <section className="extractor-container" aria-labelledby="analyzer-heading">
      <div className="extractor-card">
      {/* Header */}
      <div className="extractor-header">
        <h2 id="analyzer-heading" className="extractor-title">
          Analisis Artikel
        </h2>
        <p className="extractor-subtitle">
          Masukkan URL artikel berita publik. Sistem akan mengekstrak konten artikel
          dan menjalankan deteksi bahasa, klasifikasi kategori, analisis sentimen,
          ekstraksi kata kunci, dan pengenalan entitas bernama secara otomatis.
        </p>
      </div>

      {/* URL input form */}
      <form
        className="extractor-form"
        onSubmit={handleAnalyze}
        aria-label="Form analisis artikel"
        noValidate
      >
        <div className="extractor-input-group">
          <label htmlFor="analyzer-url-input" className="extractor-label">
            URL Artikel
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
                  Menganalisis…
                </>
              ) : (
                'Analisis Artikel'
              )}
            </button>
          </div>
          <p id="analyzer-hint" className="extractor-hint">
            Hanya URL publik yang didukung. Artikel berbahasa Indonesia dan Inggris didukung sepenuhnya.
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
            aria-label="Analisis artikel lain"
          >
            ← Analisis Artikel Lain
          </button>
        </>
      )}
      </div>
    </section>
  );
}
