import re

app_path = 'e:/AI NEWS ANALYZER/ai-news-analyzer/frontend/src/App.jsx'
with open(app_path, 'r', encoding='utf-8') as f:
    app_code = f.read()

# Replace navbar with Masthead
masthead_html = """
      {/* 📰 Masthead 📰 */}
      <header className="masthead" role="banner">
        <div className="masthead-top">
          <span className="masthead-date">{new Date().toLocaleDateString('id-ID', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</span>
          <span className="masthead-edition">EDISI DIGITAL</span>
        </div>
        <a href="/" className="masthead-brand" onClick={(e) => { e.preventDefault(); setActiveTab('home'); }}>
          <h1 className="masthead-title">AI News Analyzer</h1>
        </a>
        <nav className="masthead-nav" role="navigation" aria-label="Main navigation">
          {NAV_TABS.map((tab) => (
            <button
              key={tab.id}
              role="tab"
              aria-selected={activeTab === tab.id}
              className={`masthead-tab ${activeTab === tab.id ? 'masthead-tab--active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
              id={`tab-${tab.id}`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </header>
"""
app_code = re.sub(
    r'\{\/\*\s*✨\s*Navbar\s*✨\s*\*\/\}[\s\S]*?<\/nav>',
    masthead_html.strip(),
    app_code
)

# Replace Hero banner text layout
hero_html = """
                <div className="hero-banner-left newspaper-column">
                  <div className="hero-eyebrow newspaper-kicker">
                    <span>ANALISIS BERITA UTAMA</span>
                  </div>
                  <h2 className="hero-title newspaper-headline">
                    Analisis Isi Berita<br />Secara Otomatis
                  </h2>
                  <p className="hero-subtitle newspaper-lead">
                    <strong>JAKARTA, HARI INI &mdash;</strong> Masukkan URL artikel berita dan sistem akan menganalisis bahasa, kategori, sentimen, kata kunci, serta entitas yang terdapat di dalamnya.
                  </p>
                  <div className="hero-cta-row">
                    <button
                      className="newspaper-btn-primary"
                      onClick={() => setActiveTab('analyze')}
                      id="hero-analyze-cta"
                    >
                      Analisis Artikel
                    </button>
                    <button
                      className="newspaper-btn-secondary"
                      onClick={() => setActiveTab('dashboard')}
                      id="hero-dashboard-cta"
                    >
                      Lihat Dashboard
                    </button>
                  </div>
                </div>
"""
app_code = re.sub(
    r'<div className="hero-banner-left">[\s\S]*?<\/div>\s*<div className="hero-banner-right">',
    hero_html.strip() + '\n                <div className="hero-banner-right">',
    app_code
)

with open(app_path, 'w', encoding='utf-8') as f:
    f.write(app_code)

print("App.jsx updated with Masthead")
