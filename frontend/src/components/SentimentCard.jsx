/**
 * SentimentCard.jsx — Sentiment with visual indicator.
 */

import { getConfidenceLabel } from '../utils/formatters';

const SENTIMENT_CONFIG = {
  Positive: { icon: '😊', color: 'green', label: 'Positive' },
  Neutral:  { icon: '😐', color: 'gray',  label: 'Neutral'  },
  Negative: { icon: '😞', color: 'red',   label: 'Negative' },
  positive: { icon: '😊', color: 'green', label: 'Positive' },
  neutral:  { icon: '😐', color: 'gray',  label: 'Neutral'  },
  negative: { icon: '😞', color: 'red',   label: 'Negative' },
};

export default function SentimentCard({ sentiment }) {
  const raw = sentiment.sentiment || 'Neutral';
  const config = SENTIMENT_CONFIG[raw] || { icon: '😐', color: 'gray', label: raw };
  const confidenceScore = sentiment.confidence || 0;
  const confidencePct = Math.round(confidenceScore * 100);
  const confidenceLabel = getConfidenceLabel(confidenceScore);

  return (
    <div className="analysis-card" aria-label="Sentiment analysis result">
      <div className="analysis-card-header">
        <span className="analysis-card-icon" aria-hidden="true">💬</span>
        <h3 className="analysis-card-title">Sentiment</h3>
      </div>

      <div className={`sentiment-display sentiment-display--${config.color}`}>
        <span className="sentiment-icon" aria-hidden="true">{config.icon}</span>
        <span className="sentiment-label">{config.label}</span>
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
          className={`confidence-bar-fill confidence-bar-fill--${config.color}`}
          style={{ width: `${confidencePct}%` }}
        />
      </div>
    </div>
  );
}
