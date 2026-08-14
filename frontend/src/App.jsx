/**
 * App.jsx — Root application component.
 * Phase 5C-1: Added AI Analysis page.
 */

import { useState } from 'react';
import ArticleExtractor from './components/ArticleExtractor';
import NewsAnalyzer from './components/NewsAnalyzer';
import StatusBadge from './components/StatusBadge';

const NAV_TABS = [
  { id: 'home',    label: '🏠 Home' },
  { id: 'analyze', label: '🤖 Analyze' },
  { id: 'extract', label: '⚡ Extract' },
];

const FEATURES = [
  { icon: '📰', label: 'Article Extraction',       phase: '3', done: true  },
  { icon: '🧠', label: 'AI / NLP Analysis',        phase: '5', done: true  },
  { icon: '😊', label: 'Sentiment Analysis',        phase: '4', done: true  },
  { icon: '🏷️', label: 'News Classification',      phase: '4', done: true  },
  { icon: '🔑', label: 'Keyword Extraction',        phase: '4', done: true  },
  { icon: '👤', label: 'Named Entity Recognition',  phase: '4', done: true  },
  { icon: '🌐', label: 'Language Detection',        phase: '4', done: true  },
  { icon: '🐘', label: 'PostgreSQL Database',       phase: '2', done: true  },
  { icon: '📊', label: 'Analytics Dashboard',       phase: '6'              },
  { icon: '📡', label: 'News Feed API',             phase: '6'              },
];

export default function App() {
  const [activeTab, setActiveTab] = useState('home');

  return (
    <>
      {/* Animated background */}
      <div className="bg-grid" aria-hidden="true" />
      <div className="blob blob-blue" aria-hidden="true" />
      <div className="blob blob-purple" aria-hidden="true" />

      <div className="app-layout">
        {/* ── Navbar ── */}
        <nav className="navbar" role="navigation" aria-label="Main navigation">
          <a href="/" className="navbar-brand" aria-label="AI News Analyzer Home"
            onClick={(e) => { e.preventDefault(); setActiveTab('home'); }}>
            <div className="navbar-logo-icon" aria-hidden="true">⚡</div>
            <span className="navbar-title">AI News Analyzer</span>
            <span className="navbar-badge">AI</span>
          </a>

          <div className="navbar-tabs" role="tablist" aria-label="Page tabs">
            {NAV_TABS.map((tab) => (
              <button
                key={tab.id}
                role="tab"
                aria-selected={activeTab === tab.id}
                className={`navbar-tab ${activeTab === tab.id ? 'navbar-tab--active' : ''}`}
                onClick={() => setActiveTab(tab.id)}
                id={`tab-${tab.id}`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <span className="navbar-phase-tag">Phase 5C — Full Pipeline</span>
        </nav>

        {/* ── Main Content ── */}
        <main id="main-content">

          {/* ── HOME TAB ── */}
          {activeTab === 'home' && (
            <div className="hero" role="tabpanel" aria-labelledby="tab-home">
              <div className="hero-eyebrow" role="text">
                <span className="hero-eyebrow-dot" aria-hidden="true" />
                Multilingual News Intelligence Platform
              </div>

              <h1 className="hero-title">
                <span className="hero-title-gradient">Understand</span>
                <br />
                Every Story.
              </h1>

              <p className="hero-subtitle">
                Analyze news articles using AI &amp; NLP — automatic language detection,
                sentiment analysis, named entity recognition, keyword extraction,
                and category classification, all in one pipeline.
              </p>

              <StatusBadge />

              {/* CTA */}
              <div className="hero-cta-row">
                <button
                  className="hero-cta-btn"
                  onClick={() => setActiveTab('analyze')}
                  aria-label="Go to article analysis"
                  id="hero-analyze-cta"
                >
                  🤖 Analyze an Article
                </button>
                <button
                  className="hero-cta-btn hero-cta-btn--secondary"
                  onClick={() => setActiveTab('extract')}
                  aria-label="Extract only"
                  id="hero-extract-cta"
                >
                  ⚡ Extract Only
                </button>
              </div>

              {/* Feature Pills */}
              <section aria-label="Features" className="feature-grid">
                {FEATURES.map(({ icon, label, phase, done }) => (
                  <div
                    key={label}
                    className={`feature-pill ${done ? 'feature-pill--done' : ''}`}
                    title={done ? `Available — Phase ${phase}` : `Coming in Phase ${phase}`}
                  >
                    <span aria-hidden="true">{icon}</span>
                    {label}
                    <span className={`feature-pill-label ${done ? 'feature-pill-label--done' : ''}`}>
                      {done ? '✓' : `Ph.${phase}`}
                    </span>
                  </div>
                ))}
              </section>
            </div>
          )}

          {/* ── ANALYZE TAB ── */}
          {activeTab === 'analyze' && (
            <div
              className="extract-tab-content"
              role="tabpanel"
              aria-labelledby="tab-analyze"
            >
              <NewsAnalyzer />
            </div>
          )}

          {/* ── EXTRACT TAB ── */}
          {activeTab === 'extract' && (
            <div
              className="extract-tab-content"
              role="tabpanel"
              aria-labelledby="tab-extract"
            >
              <ArticleExtractor />
            </div>
          )}
        </main>

        {/* ── Footer ── */}
        <footer className="footer" role="contentinfo">
          <p>
            AI News Analyzer — Phase 5C &middot; Built with{' '}
            <a href="https://fastapi.tiangolo.com/" target="_blank" rel="noopener noreferrer">
              FastAPI
            </a>{' '}
            &amp;{' '}
            <a href="https://react.dev/" target="_blank" rel="noopener noreferrer">
              React
            </a>
          </p>
        </footer>
      </div>
    </>
  );
}
