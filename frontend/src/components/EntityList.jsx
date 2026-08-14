/**
 * EntityList.jsx — Displays named entities grouped by label.
 */

const LABEL_CONFIG = {
  PER:    { icon: '👤', label: 'Person',        color: 'blue'   },
  PERSON: { icon: '👤', label: 'Person',        color: 'blue'   },
  ORG:    { icon: '🏢', label: 'Organization',  color: 'purple' },
  LOC:    { icon: '📍', label: 'Location',      color: 'green'  },
  GPE:    { icon: '🌏', label: 'Place / Region',color: 'green'  },
  DATE:   { icon: '📅', label: 'Date',          color: 'orange' },
  TIME:   { icon: '⏰', label: 'Time',          color: 'orange' },
  CARDINAL: { icon: '🔢', label: 'Number',      color: 'gray'   },
  MONEY:  { icon: '💰', label: 'Money',         color: 'yellow' },
  PRODUCT:{ icon: '📦', label: 'Product',       color: 'teal'   },
  EVENT:  { icon: '📣', label: 'Event',         color: 'red'    },
};

function getConfig(label) {
  return (
    LABEL_CONFIG[label?.toUpperCase()] ||
    LABEL_CONFIG[label] ||
    { icon: '🏷️', label: label || 'Other', color: 'gray' }
  );
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

  // Group by label
  const grouped = entities.reduce((acc, ent) => {
    const key = ent.label || 'Other';
    if (!acc[key]) acc[key] = [];
    acc[key].push(ent);
    return acc;
  }, {});

  // Sort groups by priority
  const PRIORITY = ['PER', 'PERSON', 'ORG', 'LOC', 'GPE', 'DATE', 'TIME'];
  const sortedKeys = Object.keys(grouped).sort((a, b) => {
    const ai = PRIORITY.indexOf(a.toUpperCase());
    const bi = PRIORITY.indexOf(b.toUpperCase());
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
