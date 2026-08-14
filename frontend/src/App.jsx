/**
 * App.jsx — Root application component.
 * Phase 3: Added Article Extraction page.
 */

import { useState } from 'react';
import ArticleExtractor from './components/ArticleExtractor';
import StatusBadge from './components/StatusBadge';

const NAV_TABS = [
  { id: 'home', label: '🏠 Home' },
  { id: 'extract', label: '⚡ Extract Article' },
];

const FEATURES = [
  { icon: '📰', label: 'Article Extraction', phase: '3', done: true },
  { icon: '🧠', label: 'AI / NLP Analysis', phase: '4' },
  { icon: '😊', label: 'Sentiment Analysis', phase: '4' },
  { icon: '🏷️', label: 'News Classification', phase: '4' },
  { icon: '🔑', label: 'Keyword Extraction', phase: '4' },
  { icon: '👤', label: 'Named Entity Recognition', phase: '4' },
  { icon: '📝', label: 'News Summary', phase: '5' },
  { icon: '🐘', label: 'PostgreSQL Database', phase: '2', done: true },
  { icon: '📡', label: 'News API', phase: '5' },
  { icon: '📊', label: 'Analytics Dashboard', phase: '6' },
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

          {/* Tab Navigation */}
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

          <span className="navbar-phase-tag">Phase 3 — Extraction</span>
        </nav>

        {/* ── Main Content ── */}
        <main id="main-content">

          {/* ── HOME TAB ── */}
          {activeTab === 'home' && (
            <div className="hero" role="tabpanel" aria-labelledby="tab-home">
              <div className="hero-eyebrow" role="text">
                <span className="hero-eyebrow-dot" aria-hidden="true" />
                Intelligent News Intelligence Platform
              </div>

              <h1 className="hero-title">
                <span className="hero-title-gradient">AI News</span>
                <br />
                Analyzer
              </h1>

              <p className="hero-subtitle">
                Analyze news articles using AI & NLP — sentiment analysis, named
                entity recognition, keyword extraction, and automated summarization,
                all in one platform.
              </p>

              <StatusBadge />

              {/* Quick start CTA */}
              <div className="hero-cta-row">
                <button
                  className="hero-cta-btn"
                  onClick={() => setActiveTab('extract')}
                  aria-label="Go to article extraction"
                  id="hero-extract-cta"
                >
                  ⚡ Extract Your First Article
                </button>
              </div>

              {/* Feature Pills */}
              <section aria-label="Features" className="feature-grid">
                {FEATURES.map(({ icon, label, phase, done }) => (
                  <div
                    key={label}
                    className={`feature-pill ${done ? 'feature-pill--done' : ''}`}
                    title={done ? `Available in Phase ${phase}` : `Coming in Phase ${phase}`}
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
            AI News Analyzer — Phase 3 &middot; Built with{' '}
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
