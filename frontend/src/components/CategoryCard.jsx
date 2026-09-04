/**
 * CategoryCard.jsx — News category with confidence bar.
 */

import { getConfidenceLabel } from '../utils/formatters';

const CATEGORY_ICONS = {
  Technology: '💻',
  Politics: '🏛️',
  Economy: '📈',
  Sports: '⚽',
  Health: '🏥',
  Science: '🔬',
  Entertainment: '🎬',
  Business: '💼',
  World: '🌍',
  Environment: '🌿',
  Education: '📚',
  Crime: '🚨',
  Unknown: '📰',
};

export default function CategoryCard({ category }) {
  const icon = CATEGORY_ICONS[category.category] || '📰';
  const confidenceScore = category.confidence || 0;
  const confidencePct = Math.round(confidenceScore * 100);
  const confidenceLabel = getConfidenceLabel(confidenceScore);

  return (
    <div className="analysis-card" aria-label="News category">
      <div className="analysis-card-header">
        <span className="analysis-card-icon" aria-hidden="true">🏷️</span>
        <h3 className="analysis-card-title">Category</h3>
      </div>

      <div className="category-display">
        <span className="category-icon" aria-hidden="true">{icon}</span>
        <span className="category-name">{category.category}</span>
      </div>

      <div className="confidence-row">
        <span className="confidence-label">Confidence</span>
        <span className="confidence-value">
          {confidencePct}% <span className="confidence-text-label">({confidenceLabel})</span>
        </span>
      </div>
      <div
        className="confidence-bar"
        role="meter"
        aria-valuenow={confidencePct}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`Confidence: ${confidencePct}%`}
      >
        <div
          className="confidence-bar-fill confidence-bar-fill--blue"
          style={{ width: `${confidencePct}%` }}
        />
      </div>
    </div>
  );
}
