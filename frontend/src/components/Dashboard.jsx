/**
 * Dashboard.jsx — Analytics Dashboard (Phase 6)
 * Real-time statistics from PostgreSQL via /api/dashboard/stats
 * No dummy data — all data fetched from backend.
 */

import { useState, useEffect, useCallback } from 'react';
import { getDashboardStats } from '../services/api';

// ── Helpers ──────────────────────────────────────────────────────────────────

const SENTIMENT_META = {
  Positive: { icon: '😊', color: 'var(--color-success)',   bg: 'var(--color-success-dim)' },
  Neutral:  { icon: '😐', color: 'var(--color-warning)',   bg: 'rgba(245,158,11,0.12)'   },
  Negative: { icon: '😞', color: 'var(--color-error)',     bg: 'var(--color-error-dim)'  },
};

const LANG_META = {
  id: { flag: '🇮🇩', name: 'Indonesian' },
  en: { flag: '🇬🇧', name: 'English'    },
};

function fmt(n) {
  return n?.toLocaleString('id-ID') ?? '0';
}

function pct(n) {
  return `${n?.toFixed(1) ?? '0.0'}%`;
}

function shortCategory(cat) {
  if (!cat) return '—';
  return cat.replace(/_/g, ' ');
}

function confidenceBadge(val) {
  if (val == null) return null;
  const p = Math.round(val * 100);
  const color = p >= 80 ? 'var(--color-success)' : p >= 60 ? 'var(--color-warning)' : 'var(--color-error)';
  return <span style={{ color, fontWeight: 600, fontSize: '0.78rem' }}>{p}%</span>;
}

function formatDate(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric' });
}

// ── Skeleton ─────────────────────────────────────────────────────────────────

function Skeleton({ width = '100%', height = '1.2rem', radius = '6px', style = {} }) {
  return (
    <div
      className="dash-skeleton"
      style={{ width, height, borderRadius: radius, ...style }}
      aria-hidden="true"
    />
  );
}

function OverviewSkeleton() {
  return (
    <div className="dash-overview-grid">
      {[...Array(5)].map((_, i) => (
        <div key={i} className="dash-overview-card">
          <Skeleton width="40px" height="40px" radius="10px" style={{ marginBottom: '12px' }} />
          <Skeleton width="60%" height="2rem" style={{ marginBottom: '8px' }} />
          <Skeleton width="80%" height="0.9rem" />
        </div>
      ))}
    </div>
  );
}

function ChartSkeleton() {
  return (
    <div className="dash-card">
      <Skeleton width="50%" height="1.3rem" style={{ marginBottom: '20px' }} />
      {[...Array(5)].map((_, i) => (
        <div key={i} style={{ marginBottom: '12px' }}>
          <Skeleton width={`${80 - i * 12}%`} height="32px" radius="6px" />
        </div>
      ))}
    </div>
  );
}

// ── Empty State ───────────────────────────────────────────────────────────────

function EmptyState({ onAnalyze }) {
  return (
    <div className="dash-empty">
      <div className="dash-empty-icon">📭</div>
      <h3 className="dash-empty-title">Belum ada data</h3>
      <p className="dash-empty-desc">
        Lakukan analisis artikel terlebih dahulu untuk melihat grafik dasbor terisi.
      </p>
      <button className="dash-empty-btn" onClick={onAnalyze}>
        Analisis Artikel
      </button>
    </div>
  );
}

// ── Error State ───────────────────────────────────────────────────────────────

function ErrorState({ message, onRetry }) {
  return (
    <div className="dash-error">
      <div className="dash-error-icon">⚠️</div>
      <h3 className="dash-error-title">Gagal Memuat Dasbor</h3>
      <p className="dash-error-desc">{message}</p>
      <button className="dash-retry-btn" onClick={onRetry}>
        Coba Lagi
      </button>
    </div>
  );
}

// ── Overview Cards ────────────────────────────────────────────────────────────

function OverviewCards({ overview }) {
  const cards = [
    { label: 'Total Artikel',     value: overview.total_articles,     color: '#3b82f6' },
    { label: 'Total Analisis',    value: overview.total_analyses,     color: '#8b5cf6' },
    { label: 'Artikel Indonesia', value: overview.indonesian_articles, color: '#10b981' },
    { label: 'Artikel English',   value: overview.english_articles,   color: '#06b6d4' },
    { label: 'Sumber Berita',     value: overview.total_sources,      color: '#f59e0b' },
  ];
  return (
    <div className="dash-overview-grid">
      {cards.map(({ label, value }) => (
        <div key={label} className="dash-overview-card">
          <div className="dash-overview-value">{fmt(value)}</div>
          <div className="dash-overview-label">{label}</div>
        </div>
      ))}
    </div>
  );
}

// ── Category Bar Chart ────────────────────────────────────────────────────────

function CategoryChart({ data }) {
  if (!data.length) return <p className="dash-no-data">Belum ada data kategori.</p>;
  const max = data[0]?.count || 1;
  return (
    <div className="dash-bar-list">
      {data.map(({ category, count, percentage }) => (
        <div key={category} className="dash-bar-row">
          <div className="dash-bar-label">{shortCategory(category)}</div>
          <div className="dash-bar-track">
            <div
              className="dash-bar-fill"
              style={{ width: `${(count / max) * 100}%` }}
            />
          </div>
          <div className="dash-bar-meta">
            <span className="dash-bar-count">{fmt(count)}</span>
            <span className="dash-bar-pct">{pct(percentage)}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Sentiment Cards ───────────────────────────────────────────────────────────

function SentimentDistribution({ data }) {
  if (!data.length) return <p className="dash-no-data">Belum ada data sentimen.</p>;
  return (
    <div className="dash-sentiment-grid">
      {data.map(({ sentiment, count, percentage }) => {
        const meta = SENTIMENT_META[sentiment] || { icon: '❓', color: '#94a3b8', bg: 'rgba(148,163,184,0.1)' };
        return (
          <div key={sentiment} className="dash-sentiment-card" style={{ borderColor: meta.color, background: meta.bg }}>
            <div className="dash-sentiment-icon">{meta.icon}</div>
            <div className="dash-sentiment-label" style={{ color: meta.color }}>{sentiment}</div>
            <div className="dash-sentiment-count">{fmt(count)}</div>
            <div className="dash-sentiment-pct">{pct(percentage)}</div>
            <div className="dash-sentiment-bar-track">
              <div className="dash-sentiment-bar-fill" style={{ width: pct(percentage), background: meta.color }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ── Language Cards ────────────────────────────────────────────────────────────

function LanguageDistribution({ data }) {
  if (!data.length) return <p className="dash-no-data">Belum ada data bahasa.</p>;
  const total = data.reduce((s, d) => s + d.count, 0) || 1;
  return (
    <div className="dash-lang-grid">
      {data.map(({ language_code, language_name, count }) => {
        const meta = LANG_META[language_code] || { flag: '🌐', name: language_name };
        const p = (count / total) * 100;
        return (
          <div key={language_code} className="dash-lang-card">
            <span className="dash-lang-flag">{meta.flag}</span>
            <div className="dash-lang-name">{meta.name || language_name}</div>
            <div className="dash-lang-count">{fmt(count)}</div>
            <div className="dash-lang-bar-track">
              <div className="dash-lang-bar-fill" style={{ width: `${p}%` }} />
            </div>
            <div className="dash-lang-pct">{pct(p)}</div>
          </div>
        );
      })}
    </div>
  );
}

// ── Top Sources Table ─────────────────────────────────────────────────────────

function TopSources({ data }) {
  if (!data.length) return <p className="dash-no-data">Belum ada data sumber.</p>;
  const max = data[0]?.count || 1;
  return (
    <div className="dash-sources-list">
      {data.map(({ source, count }, i) => (
        <div key={source} className="dash-source-row">
          <span className="dash-source-rank">#{i + 1}</span>
          <span className="dash-source-name">{source}</span>
          <div className="dash-source-bar-track">
            <div className="dash-source-bar-fill" style={{ width: `${(count / max) * 100}%` }} />
          </div>
          <span className="dash-source-count">{fmt(count)}</span>
        </div>
      ))}
    </div>
  );
}

// ── Recent Analyses Table ─────────────────────────────────────────────────────

function RecentAnalyses({ data, onViewAnalysis }) {
  if (!data.length) return <p className="dash-no-data">Belum ada analisis tersimpan.</p>;
  return (
    <div className="dash-recent-table-wrap">
      <table className="dash-recent-table">
        <thead>
          <tr>
            <th>Judul</th>
            <th>Sumber</th>
            <th>Bahasa</th>
            <th>Kategori</th>
            <th>Sentimen</th>
            <th>Conf.</th>
            <th>Tanggal</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {data.map((item) => {
            const sentMeta = SENTIMENT_META[item.sentiment] || { color: '#94a3b8' };
            const langMeta = LANG_META[item.language_code] || { flag: '🌐' };
            return (
              <tr key={item.id}>
                <td className="dash-recent-title" title={item.article_title}>
                  {item.article_title
                    ? item.article_title.length > 50
                      ? item.article_title.slice(0, 50) + '…'
                      : item.article_title
                    : '—'}
                </td>
                <td>{item.article_source || '—'}</td>
                <td>{langMeta.flag} {item.language_code?.toUpperCase()}</td>
                <td>
                  <span className="dash-recent-cat">{shortCategory(item.category) || '—'}</span>
                </td>
                <td>
                  {item.sentiment ? (
                    <span style={{ color: sentMeta.color, fontWeight: 600 }}>
                      {item.sentiment}
                    </span>
                  ) : '—'}
                </td>
                <td>{confidenceBadge(item.sentiment_confidence)}</td>
                <td>{formatDate(item.created_at)}</td>
                <td>
                  <button
                    className="dash-view-btn"
                    onClick={() => onViewAnalysis && onViewAnalysis(item.id)}
                    title="Lihat detail analisis"
                  >
                    View
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// ── Trend Sparkline (SVG) ─────────────────────────────────────────────────────

function TrendChart({ data }) {
  if (!data.length) return <p className="dash-no-data">Belum ada data tren.</p>;

  const W = 700, H = 120, PAD = 16;
  const maxCount = Math.max(...data.map((d) => d.count), 1);
  const n = data.length;

  const points = data.map((d, i) => {
    const x = PAD + (i / Math.max(n - 1, 1)) * (W - 2 * PAD);
    const y = H - PAD - ((d.count / maxCount) * (H - 2 * PAD));
    return [x, y];
  });

  const pathD = points
    .map(([x, y], i) => `${i === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`)
    .join(' ');

  const areaD =
    pathD +
    ` L ${points[points.length - 1][0].toFixed(1)} ${H - PAD}` +
    ` L ${points[0][0].toFixed(1)} ${H - PAD} Z`;

  return (
    <div className="dash-trend-wrap">
      <svg
        viewBox={`0 0 ${W} ${H}`}
        preserveAspectRatio="none"
        className="dash-trend-svg"
        aria-label="Trend chart"
      >
        <defs>
          <linearGradient id="trendGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--color-primary)" stopOpacity="0.35" />
            <stop offset="100%" stopColor="var(--color-primary)" stopOpacity="0.02" />
          </linearGradient>
        </defs>
        <path d={areaD} fill="url(#trendGrad)" />
        <path d={pathD} fill="none" stroke="var(--color-primary)" strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round" />
        {points.map(([x, y], i) => (
          <circle key={i} cx={x} cy={y} r="3.5" fill="var(--color-primary)" stroke="var(--color-bg-card)" strokeWidth="2" />
        ))}
      </svg>
      <div className="dash-trend-labels">
        {data.length > 1 && (
          <>
            <span>{data[0]?.date}</span>
            <span>{data[data.length - 1]?.date}</span>
          </>
        )}
      </div>
    </div>
  );
}

// ── Section Wrapper ───────────────────────────────────────────────────────────

function DashSection({ title, children, wide = false }) {
  return (
    <div className={`dash-card ${wide ? 'dash-card--wide' : ''}`}>
      <h3 className="dash-card-title">{title}</h3>
      {children}
    </div>
  );
}

// ── Main Dashboard Component ──────────────────────────────────────────────────

export default function Dashboard({ onNavigate }) {
  const [stats, setStats]     = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState(null);

  const fetchStats = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getDashboardStats();
      setStats(data);
    } catch (err) {
      setError(err?.detail || 'Gagal menghubungi server. Pastikan backend berjalan.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  const isEmpty =
    stats &&
    stats.overview.total_articles === 0 &&
    stats.overview.total_analyses === 0;

  return (
    <div className="dash-root" role="main" aria-label="Analytics Dashboard">
      {/* ── Header ── */}
      <div className="dash-header">
        <div>
          <h1 className="dash-title">
            <span className="dash-title-gradient">Dasbor</span> Analitik
          </h1>
          <p className="dash-subtitle">Statistik real-time dari database PostgreSQL.</p>
        </div>
        <button
          className="dash-refresh-btn"
          onClick={fetchStats}
          disabled={loading}
          aria-label="Refresh dashboard"
          id="dashboard-refresh-btn"
        >
          {loading ? '⟳' : '🔄'} {loading ? 'Memuat…' : 'Refresh'}
        </button>
      </div>

      {/* ── Loading ── */}
      {loading && (
        <div aria-busy="true" aria-label="Memuat data dashboard">
          <OverviewSkeleton />
          <div className="dash-two-col">
            <ChartSkeleton />
            <ChartSkeleton />
          </div>
          <ChartSkeleton />
        </div>
      )}

      {/* ── Error ── */}
      {!loading && error && (
        <ErrorState message={error} onRetry={fetchStats} />
      )}

      {/* ── Empty ── */}
      {!loading && !error && isEmpty && (
        <EmptyState onAnalyze={() => onNavigate?.('analyze')} />
      )}

      {/* ── Content ── */}
      {!loading && !error && stats && !isEmpty && (
        <>
          {/* 1. Overview */}
          <OverviewCards overview={stats.overview} />

          {/* 2+3: Category + Sentiment */}
          <div className="dash-two-col">
            <DashSection title="Distribusi Kategori">
              <CategoryChart data={stats.category_distribution} />
            </DashSection>
            <DashSection title="Distribusi Sentimen">
              <SentimentDistribution data={stats.sentiment_distribution} />
            </DashSection>
          </div>

          {/* 4+5: Language + Sources */}
          <div className="dash-two-col">
            <DashSection title="Distribusi Bahasa">
              <LanguageDistribution data={stats.language_distribution} />
            </DashSection>
            <DashSection title="Top Sumber Berita">
              <TopSources data={stats.top_sources} />
            </DashSection>
          </div>

          {/* 6. Recent Analyses */}
          <DashSection title="Analisis Terbaru" wide>
            <RecentAnalyses
              data={stats.recent_analyses}
              onViewAnalysis={(id) => onNavigate?.('history', id)}
            />
          </DashSection>

          {/* 7. Trend */}
          <DashSection title="Tren Analisis (30 Hari Terakhir)" wide>
            <TrendChart data={stats.trend} />
          </DashSection>
        </>
      )}
    </div>
  );
}
