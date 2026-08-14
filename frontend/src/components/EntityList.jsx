/**
 * EntityList.jsx — Displays named entities grouped by label.
 */

const LABEL_CONFIG = {
  PERSON:       { icon: '👤', label: 'Person',        color: 'blue'   },
  ORGANIZATION: { icon: '🏢', label: 'Organization',  color: 'purple' },
  LOCATION:     { icon: '📍', label: 'Location',      color: 'green'  },
  DATE:         { icon: '📅', label: 'Date',          color: 'orange' },
  NUMBER:       { icon: '🔢', label: 'Number',        color: 'gray'   },
  OTHER:        { icon: '🏷️', label: 'Other',         color: 'gray'   },
};

// Map raw backend labels to frontend categories
function normalizeLabel(label) {
  const upper = label ? label.toUpperCase() : '';
  if (['PER', 'PERSON'].includes(upper)) return 'PERSON';
  if (['ORG', 'ORGANIZATION'].includes(upper)) return 'ORGANIZATION';
  if (['LOC', 'GPE', 'LOCATION'].includes(upper)) return 'LOCATION';
  if (['DATE', 'TIME'].includes(upper)) return 'DATE';
  if (['NUM', 'QUANTITY', 'CARDINAL', 'MONEY', 'PERCENT', 'NUMBER'].includes(upper)) return 'NUMBER';
  return 'OTHER';
}

function getConfig(label) {
  return LABEL_CONFIG[label] || LABEL_CONFIG.OTHER;
}

export default function EntityList({ entities }) {
  if (!entities || entities.length === 0) {
    return (
      <div className="analysis-card" aria-label="Named entities">
        <div className="analysis-card-header">
          <span className="analysis-card-icon" aria-hidden="true">👁️</span>
          <h3 className="analysis-card-title">Named Entities</h3>
        </div>
        <p className="analysis-empty">No entities detected.</p>
      </div>
    );
  }

  // Group by normalized label
  const grouped = entities.reduce((acc, ent) => {
    const key = normalizeLabel(ent.label);
    if (!acc[key]) acc[key] = [];
    acc[key].push(ent);
    return acc;
  }, {});

  // Sort groups by priority
  const PRIORITY = ['PERSON', 'ORGANIZATION', 'LOCATION', 'DATE', 'NUMBER', 'OTHER'];
  const sortedKeys = Object.keys(grouped).sort((a, b) => {
    const ai = PRIORITY.indexOf(a);
    const bi = PRIORITY.indexOf(b);
    if (ai === -1 && bi === -1) return a.localeCompare(b);
    if (ai === -1) return 1;
    if (bi === -1) return -1;
    return ai - bi;
  });

  return (
    <div className="analysis-card" aria-label="Named entities">
      <div className="analysis-card-header">
        <span className="analysis-card-icon" aria-hidden="true">👁️</span>
        <h3 className="analysis-card-title">Named Entities</h3>
        <span className="analysis-card-badge analysis-card-badge--green">
          {entities.length} found
        </span>
      </div>

      <div className="entity-groups">
        {sortedKeys.map((key) => {
          const cfg = getConfig(key);
          const items = grouped[key];
          return (
            <div key={key} className="entity-group">
              <div className={`entity-group-label entity-group-label--${cfg.color}`}>
                <span aria-hidden="true">{cfg.icon}</span>
                {cfg.label}
              </div>
              <div className="entity-tags" role="list">
                {items.map((ent, i) => (
                  <span
                    key={i}
                    className={`entity-tag entity-tag--${cfg.color}`}
                    role="listitem"
                  >
                    {ent.text}
                  </span>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
