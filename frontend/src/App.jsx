/**
 * App.jsx — Root application component.
 * Premium Editorial Redesign
 */

import { useState } from 'react';
import ArticleExtractor from './components/ArticleExtractor';
import NewsAnalyzer from './components/NewsAnalyzer';
import History from './components/History';
import Dashboard from './components/Dashboard';
import Compare from './components/Compare';
import { StatusBadge } from './components/StatusBadge';

const NAV_TABS = [
  { id: 'home',      label: 'Beranda'   },
  { id: 'dashboard', label: 'Dasbor'    },
  { id: 'analyze',   label: 'Analisis'  },
  { id: 'compare',   label: 'Bandingkan'},
  { id: 'history',   label: 'Riwayat'   },
  { id: 'extract',   label: 'Ekstrak'   },
];

const CAPABILITIES = [
  { id: 'extract',    label: 'Ekstraksi Artikel',           desc: 'Ambil konten penuh dari URL berita publik',          nav: 'extract'   },
  { id: 'language',   label: 'Deteksi Bahasa',              desc: 'Identifikasi bahasa otomatis: Indonesia & Inggris',  nav: 'analyze'   },
  { id: 'category',   label: 'Klasifikasi Kategori',        desc: 'Politik, Ekonomi, Teknologi, Olahraga & lainnya',   nav: 'analyze'   },
  { id: 'sentiment',  label: 'Analisis Sentimen',           desc: 'Positif, Negatif, atau Netral dengan skor kepercayaan', nav: 'analyze' },
  { id: 'keywords',   label: 'Ekstraksi Kata Kunci',        desc: 'Temukan topik utama dalam setiap artikel',          nav: 'analyze'   },
  { id: 'entities',   label: 'Pengenalan Entitas',          desc: 'Orang, organisasi, dan lokasi yang disebutkan',     nav: 'analyze'   },
  { id: 'clickbait',  label: 'Deteksi Clickbait',           desc: 'Mendeteksi tingkat sensasionalisme judul',          nav: 'analyze'   },
  { id: 'objectivity',label: 'Opini vs Fakta',              desc: 'Mengukur objektivitas dan gaya bahasa berita',      nav: 'analyze'   },
];

export default function App() {
  const [activeTab, setActiveTab] = useState('home');
  const [statusOpen, setStatusOpen] = useState(false);
  const handleNavigate = (tab) => setActiveTab(tab);

  return (
    <div className="app-layout">

      {/* 📰 Masthead 📰 */}
      <header className="masthead" role="banner">
        <div className="masthead-top">
          <span className="masthead-date">{new Date().toLocaleDateString('id-ID', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</span>
          <span className="masthead-edition">EDISI DIGITAL</span>
        </div>
        <a href="/" className="masthead-brand" onClick={(e) => { e.preventDefault(); setActiveTab('home'); }}>
          <h1 className="masthead-title">Analisis Berita</h1>
        </a>
        <nav className="masthead-nav" role="navigation" aria-label="Main navigation">
          {NAV_TABS.map((tab) => (
            <button
              key={tab.id}
              role="tab"
              aria-selected={activeTab === tab.id}
              className={`masthead-tab ${activeTab === tab.id ? 'masthead-tab--active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
              id={`tab-${tab.id}`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </header>

      {/* ── Main Content ── */}
      <main id="main-content">

        {/* ── HOME TAB ── */}
        {activeTab === 'home' && (
          <div role="tabpanel" aria-labelledby="tab-home">

            {/* Hero Banner — dark editorial */}
            <section className="hero-banner">
              <div className="hero-banner-bg" aria-hidden="true">
                <div className="newspaper-texture" />
              </div>
              <div className="hero-banner-inner">
                <div className="hero-banner-left newspaper-column">
                  <div className="hero-eyebrow newspaper-kicker">
                    <span>PLATFORM ANALISIS BERITA</span>
                  </div>
                  <h2 className="hero-title newspaper-headline">
                    Analisis Isi Berita<br />Secara Otomatis
                  </h2>
                  <p className="hero-subtitle newspaper-lead">
                    Masukkan URL artikel berita dan sistem akan menganalisis bahasa, kategori, sentimen, kata kunci, serta entitas yang terdapat di dalamnya.
                  </p>
                  <div className="hero-cta-row">
                    <button
                      className="newspaper-btn-primary"
                      onClick={() => setActiveTab('analyze')}
                      id="hero-analyze-cta"
                    >
                      Analisis Artikel
                    </button>
                    <button
                      className="newspaper-btn-secondary"
                      onClick={() => setActiveTab('dashboard')}
                      id="hero-dashboard-cta"
                    >
                      Lihat Dashboard
                    </button>
                  </div>
                </div>
                <div className="hero-banner-right">
                  <div className="status-toggle-wrap">
                    <button
                      className="status-toggle-btn"
                      onClick={() => setStatusOpen(o => !o)}
                      aria-expanded={statusOpen}
                      aria-label="Tampilkan/sembunyikan status sistem"
                    >
                      <span className="status-toggle-dot" />
                      <span>Status Sistem</span>
                      <span className="status-toggle-chevron">{statusOpen ? '▲' : '▼'}</span>
                    </button>
                    {statusOpen && (
                      <div className="status-panel-dropdown">
                        <StatusBadge />
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </section>

            {/* Capability Cards */}
            <section className="capabilities-section" aria-label="Kemampuan sistem">
              <div className="capabilities-header">
                <h2 className="capabilities-title">Kemampuan Sistem</h2>
                <p className="capabilities-subtitle">Enam modul NLP terintegrasi dalam satu platform</p>
              </div>
              <div className="capabilities-grid">
                {CAPABILITIES.map((cap) => (
                  <button
                    key={cap.id}
                    className="cap-card"
                    onClick={() => setActiveTab(cap.nav)}
                    aria-label={`${cap.label} — ${cap.desc}`}
                  >
                    <div className="cap-card-top">
                      <span className="cap-card-label">{cap.label}</span>
                      <span className="cap-card-arrow">→</span>
                    </div>
                    <p className="cap-card-desc">{cap.desc}</p>
                  </button>
                ))}
              </div>
            </section>

          </div>
        )}

        {/* ── DASHBOARD TAB ── */}
        {activeTab === 'dashboard' && (
          <div className="inner-page" role="tabpanel" aria-labelledby="tab-dashboard">
            <Dashboard onNavigate={handleNavigate} />
          </div>
        )}

        {/* ── ANALYZE TAB ── */}
        {activeTab === 'analyze' && (
          <div className="inner-page" role="tabpanel" aria-labelledby="tab-analyze">
            <NewsAnalyzer />
          </div>
        )}

        {/* 📰 HISTORY TAB 📰 */}
        {activeTab === 'history' && (
          <div className="inner-page" role="tabpanel" aria-labelledby="tab-history">
            <History />
          </div>
        )}

        {/* 📰 COMPARE TAB 📰 */}
        {activeTab === 'compare' && (
          <div className="inner-page" role="tabpanel" aria-labelledby="tab-compare">
            <Compare />
          </div>
        )}

        {/* ── EXTRACT TAB ── */}
        {activeTab === 'extract' && (
          <div className="inner-page" role="tabpanel" aria-labelledby="tab-extract">
            <ArticleExtractor />
          </div>
        )}
      </main>

        {/* ── Footer ── */}
        <footer className="footer" role="contentinfo">
          <p>&copy; {new Date().getFullYear()} ilham saputra</p>
        </footer>
    </div>
  );
}
