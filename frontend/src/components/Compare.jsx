import React, { useState } from 'react';
import AnalysisResult from './AnalysisResult';
import { analyzeArticle } from '../services/api';

export default function Compare() {
  const [urlA, setUrlA] = useState('');
  const [urlB, setUrlB] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const [resultA, setResultA] = useState(null);
  const [resultB, setResultB] = useState(null);

  const handleCompare = async (e) => {
    e.preventDefault();
    if (!urlA || !urlB) {
      setError("Silakan masukkan kedua URL untuk dibandingkan.");
      return;
    }

    setLoading(true);
    setError(null);
    setResultA(null);
    setResultB(null);

    try {
      // Run both API requests concurrently
      const [resA, resB] = await Promise.allSettled([
        analyzeArticle(urlA, 10),
        analyzeArticle(urlB, 10)
      ]);

      if (resA.status === 'fulfilled') {
        setResultA(resA.value);
      } else {
        throw new Error(`Gagal menganalisis URL A: ${resA.reason.message}`);
      }

      if (resB.status === 'fulfilled') {
        setResultB(resB.value);
      } else {
        throw new Error(`Gagal menganalisis URL B: ${resB.reason.message}`);
      }
      
    } catch (err) {
      setError(err.message || "Analisis gagal. Pastikan kedua URL valid.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="content-container">
      <div className="section-header">
        <h2 className="section-title">Bandingkan Dua Media</h2>
        <p className="section-subtitle">Masukkan dua tautan berita yang membahas topik yang sama untuk melihat perbandingan objektivitas, sentimen, dan bias secara berdampingan.</p>
      </div>

      <form onSubmit={handleCompare} className="extractor-form" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap' }}>
          <div style={{ flex: '1 1 300px' }}>
            <label htmlFor="url-a" style={{ display: 'block', marginBottom: '8px', fontWeight: 600 }}>Tautan Berita A (Media 1)</label>
            <input
              id="url-a"
              type="url"
              className="extractor-input"
              placeholder="https://www.cnnindonesia.com/..."
              value={urlA}
              onChange={(e) => setUrlA(e.target.value)}
              required
            />
          </div>
          <div style={{ flex: '1 1 300px' }}>
            <label htmlFor="url-b" style={{ display: 'block', marginBottom: '8px', fontWeight: 600 }}>Tautan Berita B (Media 2)</label>
            <input
              id="url-b"
              type="url"
              className="extractor-input"
              placeholder="https://www.cnbcindonesia.com/..."
              value={urlB}
              onChange={(e) => setUrlB(e.target.value)}
              required
            />
          </div>
        </div>

        {error && (
          <div className="error-message" role="alert">
            <span aria-hidden="true">⚠️</span> {error}
          </div>
        )}

        <button 
          type="submit" 
          className="btn-primary extractor-btn" 
          disabled={loading}
          style={{ alignSelf: 'center', minWidth: '250px' }}
        >
          {loading ? 'Membandingkan...' : 'Mulai Pembandingan'}
        </button>
      </form>

      {/* Results Side by Side */}
      {(resultA || resultB) && (
        <div style={{ display: 'flex', gap: '40px', marginTop: '60px', flexWrap: 'wrap' }}>
          {/* Column A */}
          <div style={{ flex: '1 1 45%', minWidth: '300px' }}>
            <h3 style={{ borderBottom: '2px solid var(--ink)', paddingBottom: '12px', marginBottom: '24px', fontFamily: '"Playfair Display", serif', fontSize: '1.5rem' }}>
              Media 1
            </h3>
            {resultA ? (
              <AnalysisResult data={resultA} />
            ) : (
              <div style={{ padding: '24px', background: 'var(--surface)', border: '1px dashed var(--border-color)', textAlign: 'center' }}>Gagal memuat atau sedang memproses...</div>
            )}
          </div>
          
          {/* Column B */}
          <div style={{ flex: '1 1 45%', minWidth: '300px' }}>
            <h3 style={{ borderBottom: '2px solid var(--ink)', paddingBottom: '12px', marginBottom: '24px', fontFamily: '"Playfair Display", serif', fontSize: '1.5rem' }}>
              Media 2
            </h3>
            {resultB ? (
              <AnalysisResult data={resultB} />
            ) : (
              <div style={{ padding: '24px', background: 'var(--surface)', border: '1px dashed var(--border-color)', textAlign: 'center' }}>Gagal memuat atau sedang memproses...</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
