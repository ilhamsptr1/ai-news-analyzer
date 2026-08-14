/**
 * LanguageCard.jsx — Displays detected language with flag & confidence.
 */

const LANG_FLAGS = {
  id: '🇮🇩',
  en: '🇬🇧',
  fr: '🇫🇷',
  de: '🇩🇪',
  es: '🇪🇸',
  ja: '🇯🇵',
  zh: '🇨🇳',
  ar: '🇸🇦',
  pt: '🇵🇹',
  ko: '🇰🇷',
};

export default function LanguageCard({ language }) {
  const flag = LANG_FLAGS[language.code] || '🌐';
  const confidencePct =
    language.confidence != null
      ? `${(language.confidence * 100).toFixed(1)}%`
      : null;

  return (
    <div className="analysis-card" aria-label="Language detection result">
      <div className="analysis-card-header">
        <span className="analysis-card-icon" aria-hidden="true">🌐</span>
        <h3 className="analysis-card-title">Language</h3>
        <span className="analysis-card-badge analysis-card-badge--blue">
          {language.source === 'auto' ? 'Auto-detected' : 'Provided'}
        </span>
      </div>

      <div className="lang-display">
        <span className="lang-flag" aria-hidden="true">{flag}</span>
        <div className="lang-info">
          <span className="lang-name">{language.language_name}</span>
          <span className="lang-code">{language.code.toUpperCase()}</span>
        </div>
        {confidencePct && (
          <span className="lang-confidence">{confidencePct}</span>
        )}
      </div>

      {!language.supported && (
        <div className="lang-unsupported-note" role="note">
          ⚠️ Language not supported for AI analysis
        </div>
      )}
    </div>
  );
}
