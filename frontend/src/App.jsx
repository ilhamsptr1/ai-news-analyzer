/**
 * App.jsx — Root application component.
 * Phase 1: Foundation landing page with backend status indicator.
 */

import StatusBadge from './components/StatusBadge';

// Future feature pills to show planned roadmap
const FEATURES = [
  { icon: '📰', label: 'Article Extraction', phase: '2' },
  { icon: '🧠', label: 'AI / NLP Analysis', phase: '3' },
  { icon: '😊', label: 'Sentiment Analysis', phase: '3' },
  { icon: '🏷️', label: 'News Classification', phase: '4' },
  { icon: '🔑', label: 'Keyword Extraction', phase: '4' },
  { icon: '👤', label: 'Named Entity Recognition', phase: '4' },
  { icon: '📝', label: 'News Summary', phase: '5' },
  { icon: '🐘', label: 'PostgreSQL Database', phase: '2' },
  { icon: '📡', label: 'News API', phase: '5' },
  { icon: '📊', label: 'Analytics Dashboard', phase: '6' },
];

export default function App() {
  return (
    <>
      {/* Animated background */}
      <div className="bg-grid" aria-hidden="true" />
      <div className="blob blob-blue" aria-hidden="true" />
      <div className="blob blob-purple" aria-hidden="true" />

      <div className="app-layout">
        {/* ── Navbar ── */}
        <nav className="navbar" role="navigation" aria-label="Main navigation">
          <a href="/" className="navbar-brand" aria-label="AI News Analyzer Home">
            <div className="navbar-logo-icon" aria-hidden="true">⚡</div>
            <span className="navbar-title">AI News Analyzer</span>
            <span className="navbar-badge">AI</span>
          </a>
          <span className="navbar-phase-tag">Phase 1 — Foundation</span>
        </nav>

        {/* ── Hero ── */}
        <main className="hero" id="main-content">
          {/* Eyebrow */}
          <div className="hero-eyebrow" role="text">
            <span className="hero-eyebrow-dot" aria-hidden="true" />
            Intelligent News Intelligence Platform
          </div>

          {/* Heading */}
          <h1 className="hero-title">
            <span className="hero-title-gradient">AI News</span>
            <br />
            Analyzer
          </h1>

          {/* Subtitle */}
          <p className="hero-subtitle">
            Analyze news articles using AI &amp; NLP — sentiment analysis, named
            entity recognition, keyword extraction, and automated summarization,
            all in one platform.
          </p>

          {/* Backend Status Card */}
          <StatusBadge />

          {/* Planned Feature Pills */}
          <section aria-label="Planned features" className="feature-grid">
            {FEATURES.map(({ icon, label, phase }) => (
              <div key={label} className="feature-pill" title={`Coming in Phase ${phase}`}>
                <span aria-hidden="true">{icon}</span>
                {label}
                <span className="feature-pill-label">Ph.{phase}</span>
              </div>
            ))}
          </section>
        </main>

        {/* ── Footer ── */}
        <footer className="footer" role="contentinfo">
          <p>
            AI News Analyzer — Phase 1 &middot; Built with{' '}
            <a
              href="https://fastapi.tiangolo.com/"
              target="_blank"
              rel="noopener noreferrer"
            >
              FastAPI
            </a>{' '}
            &amp;{' '}
            <a
              href="https://react.dev/"
              target="_blank"
              rel="noopener noreferrer"
            >
              React
            </a>
          </p>
        </footer>
      </div>
    </>
  );
}
