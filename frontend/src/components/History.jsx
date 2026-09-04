import React, { useState, useEffect } from 'react';
import api from '../services/api';
import AnalysisResult from './AnalysisResult';

const SENTIMENT_BADGE = {
  Positive: 'badge--positive',
  Negative: 'badge--negative',
  Neutral:  'badge--neutral',
};

function formatDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('en-GB', {
    day: '2-digit', month: 'short', year: 'numeric',
  });
}

function shortCategory(cat) {
  if (!cat) return '—';
  return cat.replace(/_/g, ' ');
}

export default function History() {
  const [view, setView]                     = useState('list');
  const [analyses, setAnalyses]             = useState([]);
  const [total, setTotal]                   = useState(0);
  const [loading, setLoading]               = useState(true);
  const [error, setError]                   = useState(null);
  const [page, setPage]                     = useState(1);
  const limit = 20;

  // Filters
  const [language, setLanguage]   = useState('');
  const [category, setCategory]   = useState('');
  const [sentiment, setSentiment] = useState('');

  // Detail
  const [selectedAnalysis, setSelectedAnalysis] = useState(null);
  const [loadingDetail, setLoadingDetail]       = useState(false);

  useEffect(() => {
    if (view === 'list') fetchHistory();
  }, [page, language, category, sentiment, view]);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      setError(null);
      const offset = (page - 1) * limit;
      const res = await api.getAnalysisHistory({ limit, offset, language, category, sentiment });
      setAnalyses(res.items || []);
      setTotal(res.total || 0);
    } catch {
      setError('Gagal memuat riwayat analisis.');
    } finally {
      setLoading(false);
    }
  };

  const handleViewDetail = async (id) => {
    try {
      setLoadingDetail(true);
      setError(null);
      const data = await api.getAnalysisDetail(id);
      setSelectedAnalysis(data);
      setView('detail');
    } catch {
      setError('Gagal memuat detail analisis.');
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleResetDetail = () => {
    setView('list');
    setSelectedAnalysis(null);
  };

  const handleFilterChange = (setter) => (e) => {
    setter(e.target.value);
    setPage(1);
  };

  const totalPages = Math.ceil(total / limit);

  // Detail view
  if (view === 'detail' && selectedAnalysis) {
    return (
      <div className="history-detail-wrapper">
        <div style={{ marginBottom: '20px', borderBottom: '1px solid var(--border-color)', paddingBottom: '10px' }}>
          <button 
            onClick={handleResetDetail}
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              fontFamily: 'var(--font-serif)',
              fontSize: '1rem',
              fontWeight: 600,
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              padding: '4px 0',
              textTransform: 'uppercase',
              letterSpacing: '0.05em'
            }}
          >
            &#8592; Kembali ke Riwayat
          </button>
        </div>
        <AnalysisResult data={selectedAnalysis} onReset={handleResetDetail} />
      </div>
    );
  }

  return (
    <div className="analyzer-container">
      {/* Page heading */}
      <div className="analyzer-header">
        <h2>Riwayat Analisis</h2>
        <p>Telusuri artikel yang pernah dianalisis oleh sistem. {total > 0 && `Total ${total} data.`}</p>
      </div>

      {/* Filters */}
      <div className="history-filters">
        <span style={{ fontSize: '0.78rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-muted)', marginRight: '4px' }}>
          Filter:
        </span>

        <select
          value={language}
          onChange={handleFilterChange(setLanguage)}
          className="form-input"
          style={{ flex: '0 1 160px', minWidth: '120px' }}
          aria-label="Filter bahasa"
        >
          <option value="">Semua Bahasa</option>
          <option value="id">Bahasa Indonesia</option>
          <option value="en">Bahasa Inggris</option>
        </select>

        <select
          value={category}
          onChange={handleFilterChange(setCategory)}
          className="form-input"
          style={{ flex: '0 1 200px', minWidth: '150px' }}
          aria-label="Filter kategori"
        >
          <option value="">Semua Kategori</option>
          <option value="POLITIK">Politik</option>
          <option value="EKONOMI_BISNIS">Ekonomi &amp; Bisnis</option>
          <option value="TEKNOLOGI">Teknologi</option>
          <option value="OLAHRAGA">Olahraga</option>
          <option value="HIBURAN">Hiburan</option>
        </select>

        <select
          value={sentiment}
          onChange={handleFilterChange(setSentiment)}
          className="form-input"
          style={{ flex: '0 1 160px', minWidth: '120px' }}
          aria-label="Filter sentimen"
        >
          <option value="">Semua Sentimen</option>
          <option value="Positive">Positif</option>
          <option value="Negative">Negatif</option>
          <option value="Neutral">Netral</option>
        </select>

        {(language || category || sentiment) && (
          <button
            className="btn-secondary"
            onClick={() => { setLanguage(''); setCategory(''); setSentiment(''); setPage(1); }}
          >
            Hapus Filter
          </button>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="error-card">
          <div className="error-icon">⚠</div>
          <div className="error-content">
            <h4 className="error-title">Kesalahan</h4>
            <p className="error-desc">{error}</p>
          </div>
          <button className="btn-primary" onClick={fetchHistory} style={{ marginLeft: 'auto' }}>
            Coba Lagi
          </button>
        </div>
      )}

      {/* Loading */}
      {loading ? (
        <div className="loading-state">
          <div className="spinner" />
          <p>Memuat riwayat…</p>
        </div>

      ) : analyses.length === 0 && !error ? (
        <div className="empty-state">
          <p style={{ fontSize: '2rem', marginBottom: '12px' }}>📭</p>
          <h3 style={{ marginBottom: '6px', color: 'var(--text-primary)', fontWeight: 700 }}>Belum ada analisis</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            Analisis artikel berita untuk melihatnya di sini.
          </p>
        </div>

      ) : (
        <>
          {/* Desktop table */}
          <div className="history-table-wrap" role="region" aria-label="Tabel riwayat analisis">
            <table className="history-table">
              <thead>
                <tr>
                  <th style={{ width: '100px' }}>Tanggal</th>
                  <th>Artikel</th>
                  <th style={{ width: '130px' }}>Sumber</th>
                  <th style={{ width: '70px' }}>Bhs</th>
                  <th style={{ width: '140px' }}>Kategori</th>
                  <th style={{ width: '90px' }}>Sentimen</th>
                  <th style={{ width: '60px' }}>Aksi</th>
                </tr>
              </thead>
              <tbody>
                {analyses.map((item) => (
                  <tr key={item.id}>
                    <td style={{ color: 'var(--text-muted)', fontSize: '0.82rem', whiteSpace: 'nowrap' }}>
                      {formatDate(item.created_at)}
                    </td>
                    <td>
                      <span className="history-table-title">
                        {item.article_title || 'Artikel Tanpa Judul'}
                      </span>
                    </td>
                    <td style={{ fontSize: '0.82rem' }}>
                      {item.article_source || '—'}
                    </td>
                    <td>
                      <span className="badge badge--lang">
                        {item.language_code === 'id' ? 'ID' : item.language_code === 'en' ? 'EN' : (item.language_code || '—').toUpperCase()}
                      </span>
                    </td>
                    <td>
                      <span className="badge badge--cat">
                        {shortCategory(item.category)}
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${SENTIMENT_BADGE[item.sentiment] || 'badge--neutral'}`}>
                        {item.sentiment || 'Neutral'}
                      </span>
                    </td>
                    <td>
                      <button
                        className="dash-view-btn"
                        onClick={() => handleViewDetail(item.id)}
                        disabled={loadingDetail}
                        aria-label={`Lihat analisis untuk ${item.article_title}`}
                      >
                        Lihat
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="pagination">
              <button
                className="btn-secondary"
                disabled={page === 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                ← Sebelumnya
              </button>
              <span style={{ fontSize: '0.875rem' }}>
                Halaman {page} dari {totalPages}
              </span>
              <button
                className="btn-secondary"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              >
                Selanjutnya →
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
