/**
 * KeywordList.jsx — Displays extracted keywords as badges.
 * Note: YAKE score — lower is MORE relevant. Display rank, not score as %.
 */

export default function KeywordList({ keywords }) {
  if (!keywords || keywords.length === 0) {
    return (
      <div className="analysis-card" aria-label="Keywords">
        <div className="analysis-card-header">
          <span className="analysis-card-icon" aria-hidden="true">🔑</span>
          <h3 className="analysis-card-title">Keywords</h3>
        </div>
        <p className="analysis-empty">No keywords extracted.</p>
      </div>
    );
  }

  return (
    <div className="analysis-card" aria-label="Extracted keywords">
      <div className="analysis-card-header">
        <span className="analysis-card-icon" aria-hidden="true">🔑</span>
        <h3 className="analysis-card-title">Keywords</h3>
        <span className="analysis-card-badge analysis-card-badge--purple">
          {keywords.length} found
        </span>
      </div>

      <div className="keyword-grid" role="list" aria-label="Keyword list">
        {keywords.map((kw, idx) => (
          <div
            key={kw.id ?? idx}
            className="keyword-badge"
            role="listitem"
            title={`Rank #${kw.rank ?? idx + 1}`}
          >
            <span className="keyword-rank">#{kw.rank ?? idx + 1}</span>
            <span className="keyword-text">{kw.keyword}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
