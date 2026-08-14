/**
 * StatusBadge.jsx — Displays backend connection status with animated indicator.
 */

import { useHealthCheck } from '../hooks/useHealthCheck';

const STATUS_CONFIG = {
  loading: {
    badge: 'status-badge--loading',
    dot: 'status-dot--loading',
    textClass: 'status-text--loading',
    label: 'Checking backend…',
    dotEl: <span className="spinner" aria-hidden="true" />,
  },
  connected: {
    badge: 'status-badge--connected',
    dot: 'status-dot--connected',
    textClass: 'status-text--connected',
    label: 'Connected',
    dotEl: null,
  },
  error: {
    badge: 'status-badge--error',
    dot: 'status-dot--error',
    textClass: 'status-text--error',
    label: 'Backend unavailable',
    dotEl: null,
  },
};

export function StatusBadge() {
  const { status, service, retry } = useHealthCheck();
  const cfg = STATUS_CONFIG[status] ?? STATUS_CONFIG.loading;

  return (
    <div className="status-card" role="region" aria-label="Backend Status">
      {/* Card Header */}
      <div className="status-card-header">
        <span className="status-card-title">System Status</span>
        <div className="status-card-icon" aria-hidden="true">⚡</div>
      </div>

      {/* Backend Status Row */}
      <div className="status-row">
        <span className="status-label">Backend API</span>
        <span className={`status-value ${cfg.textClass}`}>
          {status === 'loading' ? (
            <span className="spinner" aria-hidden="true" />
          ) : (
            <span className={`status-dot ${cfg.dot}`} aria-hidden="true" />
          )}
          {cfg.label}
        </span>
      </div>

      {/* Service Name Row */}
      <div className="status-row">
        <span className="status-label">Service</span>
        <span className="status-value" style={{ color: 'var(--color-text-secondary)' }}>
          {status === 'connected'
            ? service ?? 'AI News Analyzer API'
            : status === 'loading'
            ? '—'
            : 'Unreachable'}
        </span>
      </div>

      {/* Endpoint Row */}
      <div className="status-row">
        <span className="status-label">Health Endpoint</span>
        <span
          className="status-value"
          style={{
            fontFamily: 'monospace',
            fontSize: '0.8rem',
            color: 'var(--color-primary-light)',
          }}
        >
          GET /api/health
        </span>
      </div>

      {/* Retry Button (only in error state) */}
      {status === 'error' && (
        <button
          className="btn-retry"
          onClick={retry}
          id="btn-retry-health"
          aria-label="Retry backend connection"
        >
          ↺ Retry Connection
        </button>
      )}

      {/* Overall Badge */}
      <div style={{ marginTop: '20px', display: 'flex', justifyContent: 'center' }}>
        <span className={`status-badge ${cfg.badge}`}>
          <span
            className={`status-dot ${cfg.dot}`}
            style={{ width: 7, height: 7 }}
            aria-hidden="true"
          />
          {status === 'loading'
            ? 'Checking…'
            : status === 'connected'
            ? '● Connected'
            : '✕ Offline'}
        </span>
      </div>
    </div>
  );
}

export default StatusBadge;
