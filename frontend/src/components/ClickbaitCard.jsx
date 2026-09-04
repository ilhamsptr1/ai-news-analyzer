import React from 'react';

export default function ClickbaitCard({ score, reasons = [] }) {
  const percentage = Math.round((score || 0) * 100);
  
  let label = "Faktual";
  let colorClass = "clickbait-low";
  if (percentage > 70) {
    label = "Sangat Sensasional / Clickbait";
    colorClass = "clickbait-high";
  } else if (percentage > 30) {
    label = "Sedikit Sensasional";
    colorClass = "clickbait-medium";
  }

  return (
    <div className={`analysis-card ${colorClass}`}>
      <h3 className="card-title">Skor Clickbait</h3>
      <div className="card-content">
        <div className="clickbait-score-container">
          <div className="clickbait-value">{percentage}%</div>
          <div className="clickbait-label">{label}</div>
        </div>
        
        <div className="clickbait-progress-bar">
          <div 
            className="clickbait-progress-fill" 
            style={{ width: `${percentage}%` }}
          />
        </div>

        {reasons && reasons.length > 0 && (
          <div className="clickbait-reasons">
            <h4>Alasan Deteksi:</h4>
            <ul>
              {reasons.map((r, i) => <li key={i}>{r}</li>)}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
