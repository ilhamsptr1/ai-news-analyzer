import React, { useState, useEffect } from 'react';
import api from '../services/api';
import AnalysisResult from './AnalysisResult';

export default function History() {
  const [view, setView] = useState('list'); // 'list' | 'detail'
  const [analyses, setAnalyses] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Pagination
  const [page, setPage] = useState(1);
  const limit = 20;

  // Filters
  const [language, setLanguage] = useState('');
  const [category, setCategory] = useState('');
  const [sentiment, setSentiment] = useState('');

  // Detail
  const [selectedAnalysis, setSelectedAnalysis] = useState(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  useEffect(() => {
    if (view === 'list') {
      fetchHistory();
    }
  }, [page, language, category, sentiment, view]);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      setError(null);
      const offset = (page - 1) * limit;
      const res = await api.getAnalysisHistory({
        limit,
        offset,
        language,
        category,
        sentiment
      });
      setAnalyses(res.items || []);
      setTotal(res.total || 0);
    } catch (err) {
      setError('Unable to load analysis history.');
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
    } catch (err) {
      setError('Unable to load analysis detail.');
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
    setPage(1); // Reset to page 1 on filter change
  };

  const totalPages = Math.ceil(total / limit);

  // If viewing detail, reuse AnalysisResult
  if (view === 'detail' && selectedAnalysis) {
    return (
      <div className="history-detail-wrapper">
        <button className="btn-secondary" onClick={handleResetDetail} style={{ marginBottom: '1.5rem' }}>
          ← Back to History
        </button>
        <AnalysisResult 
          result={selectedAnalysis} 
          onReset={handleResetDetail} 
        />
      </div>
    );
  }

  return (
    <div className="analyzer-container">
      <div className="analyzer-header">
        <h2>Analysis History</h2>
        <p>View past articles analyzed by the AI.</p>
      </div>

      <div className="history-filters" style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
        <select value={language} onChange={handleFilterChange(setLanguage)} className="form-input" style={{ flex: '1', minWidth: '150px' }}>
          <option value="">All Languages</option>
          <option value="id">Indonesian</option>
          <option value="en">English</option>
        </select>

        <select value={category} onChange={handleFilterChange(setCategory)} className="form-input" style={{ flex: '1', minWidth: '150px' }}>
          <option value="">All Categories</option>
          <option value="POLITIK">Politik (Politics)</option>
          <option value="EKONOMI_BISNIS">Ekonomi (Business)</option>
          <option value="TEKNOLOGI">Teknologi (Technology)</option>
          <option value="OLAHRAGA">Olahraga (Sports)</option>
          <option value="HIBURAN">Hiburan (Entertainment)</option>
        </select>

        <select value={sentiment} onChange={handleFilterChange(setSentiment)} className="form-input" style={{ flex: '1', minWidth: '150px' }}>
          <option value="">All Sentiments</option>
          <option value="Positive">Positive</option>
          <option value="Negative">Negative</option>
          <option value="Neutral">Neutral</option>
        </select>
      </div>

      {error && (
        <div className="error-card">
          <div className="error-icon">❌</div>
          <div className="error-content">
            <h4 className="error-title">Error</h4>
            <p className="error-desc">{error}</p>
          </div>
          <button className="btn-primary" onClick={fetchHistory} style={{ marginLeft: 'auto' }}>Retry</button>
        </div>
      )}

      {loading ? (
        <div className="loading-state" style={{ padding: '3rem 0', textAlign: 'center' }}>
          <div className="spinner"></div>
          <p>Loading history...</p>
        </div>
      ) : analyses.length === 0 && !error ? (
        <div className="empty-state" style={{ padding: '3rem 1rem', textAlign: 'center', backgroundColor: 'var(--surface-color)', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📭</div>
          <h3 style={{ marginBottom: '0.5rem', color: 'var(--text-color)' }}>No analyses yet</h3>
          <p style={{ color: 'var(--text-secondary)' }}>Analyze a news article to see it appear here.</p>
        </div>
      ) : (
        <>
          <div className="history-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1.5rem' }}>
            {analyses.map(item => (
              <div key={item.id} className="history-card" style={{ backgroundColor: 'var(--surface-color)', borderRadius: '12px', border: '1px solid var(--border-color)', padding: '1.5rem', display: 'flex', flexDirection: 'column' }}>
                <div style={{ flex: '1' }}>
                  <h3 style={{ fontSize: '1.1rem', margin: '0 0 0.5rem 0', color: 'var(--text-color)', lineHeight: '1.4', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                    {item.article_title || 'Untitled Article'}
                  </h3>
                  <p style={{ margin: '0 0 1rem 0', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                    {item.article_source || 'Unknown Source'}
                  </p>
                  
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '1.5rem' }}>
                    <span className="badge" style={{ backgroundColor: 'rgba(59, 130, 246, 0.1)', color: '#3b82f6', padding: '0.25rem 0.5rem', borderRadius: '4px', fontSize: '0.75rem', fontWeight: '500' }}>
                      {item.language_code === 'id' ? '🇮🇩 ID' : item.language_code === 'en' ? '🇬🇧 EN' : '🌐 ' + item.language_code}
                    </span>
                    <span className="badge" style={{ backgroundColor: 'rgba(168, 85, 247, 0.1)', color: '#a855f7', padding: '0.25rem 0.5rem', borderRadius: '4px', fontSize: '0.75rem', fontWeight: '500' }}>
                      {item.category || 'Uncategorized'}
                    </span>
                    <span className="badge" style={{ backgroundColor: item.sentiment === 'Positive' ? 'rgba(34, 197, 94, 0.1)' : item.sentiment === 'Negative' ? 'rgba(239, 68, 68, 0.1)' : 'rgba(156, 163, 175, 0.1)', color: item.sentiment === 'Positive' ? '#22c55e' : item.sentiment === 'Negative' ? '#ef4444' : '#9ca3af', padding: '0.25rem 0.5rem', borderRadius: '4px', fontSize: '0.75rem', fontWeight: '500' }}>
                      {item.sentiment === 'Positive' ? '😊 Positive' : item.sentiment === 'Negative' ? '😠 Negative' : '😐 Neutral'}
                    </span>
                  </div>
                </div>
                
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'auto', paddingTop: '1rem', borderTop: '1px solid var(--border-color)' }}>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    Analyzed {new Date(item.created_at).toLocaleDateString()}
                  </span>
                  <button 
                    className="btn-primary" 
                    style={{ padding: '0.4rem 1rem', fontSize: '0.85rem' }}
                    onClick={() => handleViewDetail(item.id)}
                    disabled={loadingDetail}
                  >
                    View
                  </button>
                </div>
              </div>
            ))}
          </div>
          
          {totalPages > 1 && (
            <div className="pagination" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '1rem', marginTop: '2rem' }}>
              <button 
                className="btn-secondary" 
                disabled={page === 1}
                onClick={() => setPage(p => Math.max(1, p - 1))}
              >
                Previous
              </button>
              <span style={{ color: 'var(--text-color)', fontSize: '0.9rem' }}>
                Page {page} of {totalPages}
              </span>
              <button 
                className="btn-secondary" 
                disabled={page >= totalPages}
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
