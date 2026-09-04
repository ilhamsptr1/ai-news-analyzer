import React from 'react';

export default function ObjectivityCard({ score, details }) {
  const percentage = Math.round((score || 0) * 100);
  
  let label = "Netral";
  let colorClass = "objectivity-medium"; // Neutral/Mixed
  let barColor = "var(--highlight-brand)";
  
  if (percentage >= 70) {
    label = "Sangat Faktual";
    colorClass = "objectivity-high";
    barColor = "var(--success)"; // Green/Blue for facts
  } else if (percentage <= 40) {
    label = "Opini / Subjektif";
    colorClass = "objectivity-low";
    barColor = "var(--danger)"; // Orange/Red for opinion
  } else {
    label = "Campuran Fakta & Opini";
  }

  const reasons = details?.reasons || [];
  const factCount = details?.factual_count || 0;
  const opCount = details?.opinion_count || 0;

  return (
    <div className={`analysis-card ${colorClass}`}>
      <h3 className="card-title">Tingkat Objektivitas</h3>
      <div className="card-content" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        
        {/* Main Score Area */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--ink)' }}>{percentage}%</span>
            <span style={{ fontSize: '0.875rem', fontWeight: 600, color: barColor, textTransform: 'uppercase', letterSpacing: '0.05em' }}>{label}</span>
          </div>
          
          <div style={{ display: 'flex', gap: '12px', textAlign: 'right' }}>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
              <span style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--slate)' }}>{factCount}</span>
              <span style={{ fontSize: '0.75rem', color: 'var(--faint)' }}>Fakta</span>
            </div>
            <div style={{ width: '1px', background: 'var(--rule)', height: '100%' }}></div>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
              <span style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--slate)' }}>{opCount}</span>
              <span style={{ fontSize: '0.75rem', color: 'var(--faint)' }}>Opini</span>
            </div>
          </div>
        </div>
        
        {/* Progress Bar */}
        <div style={{ height: '8px', background: 'var(--rule)', borderRadius: '4px', overflow: 'hidden' }}>
          <div 
            style={{ 
              width: `${percentage}%`, 
              height: '100%', 
              background: barColor,
              transition: 'width 1s ease-in-out'
            }}
          />
        </div>

        {/* Reasons List */}
        {reasons.length > 0 && (
          <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '0.875rem', color: 'var(--slate)' }}>
            {reasons.map((r, i) => (
              <li key={i} style={{ marginBottom: '4px' }}>{r}</li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
