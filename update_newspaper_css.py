import re

css_path = 'e:/AI NEWS ANALYZER/ai-news-analyzer/frontend/src/index.css'
with open(css_path, 'r', encoding='utf-8') as f:
    css = f.read()

# Add new newspaper styles
newspaper_styles = """
/* ══════════════════════════════════════════════════════════════
   NEWSPAPER AESTHETIC OVERRIDES
══════════════════════════════════════════════════════════════ */
.masthead {
  display: flex; flex-direction: column; align-items: center;
  border-bottom: 4px double var(--rule);
  padding: var(--s5) var(--s8) 0 var(--s8);
  margin-bottom: var(--s8);
  background: var(--bg);
}
.masthead-top {
  display: flex; justify-content: space-between; width: 100%;
  font-family: var(--font); font-size: 12px; font-weight: 600;
  text-transform: uppercase; color: var(--muted);
  border-bottom: 1px solid var(--rule); padding-bottom: 4px;
  margin-bottom: var(--s4);
}
.masthead-brand { text-decoration: none; color: var(--ink); margin-bottom: var(--s4); }
.masthead-title {
  font-family: var(--font-serif);
  font-size: 56px; font-weight: 900;
  letter-spacing: -0.02em; text-align: center;
}
.masthead-nav {
  display: flex; gap: var(--s6); width: 100%; justify-content: center;
  border-top: 1px solid var(--rule); padding: var(--s3) 0;
}
.masthead-tab {
  background: transparent; border: none; font-family: var(--font-heading);
  font-size: 15px; font-weight: 700; color: var(--ink); text-transform: uppercase;
  cursor: pointer; position: relative;
}
.masthead-tab:hover { color: var(--accent); }
.masthead-tab--active::after {
  content: ""; position: absolute; bottom: -8px; left: 0; right: 0;
  height: 3px; background: var(--rule);
}
.newspaper-column {
  border-right: 1px solid var(--rule); padding-right: var(--s8);
}
.newspaper-kicker {
  font-family: var(--font); font-size: 13px; font-weight: 700;
  text-transform: uppercase; color: var(--accent); margin-bottom: var(--s3);
  border-bottom: 2px solid var(--rule); display: inline-block; padding-bottom: 2px;
}
.newspaper-headline {
  font-family: var(--font-serif); font-size: 56px; font-weight: 700;
  line-height: 1.05; letter-spacing: -0.02em; margin-bottom: var(--s4);
  color: var(--ink);
}
.newspaper-lead {
  font-family: var(--font-serif); font-size: 19px; line-height: 1.6;
  color: var(--ink); margin-bottom: var(--s6);
}
.newspaper-btn-primary {
  background: var(--ink); color: var(--white);
  border: 1px solid var(--ink); padding: 12px 24px;
  font-family: var(--font); font-size: 14px; font-weight: 700;
  text-transform: uppercase; cursor: pointer; transition: background 0.2s;
}
.newspaper-btn-primary:hover { background: var(--slate); }
.newspaper-btn-secondary {
  background: transparent; color: var(--ink);
  border: 1px solid var(--ink); padding: 12px 24px;
  font-family: var(--font); font-size: 14px; font-weight: 700;
  text-transform: uppercase; cursor: pointer; transition: background 0.2s;
}
.newspaper-btn-secondary:hover { background: var(--rule-light); }

/* Make sure the hero banner itself fits */
.hero-banner {
  background: var(--bg); border: none; border-top: 1px solid var(--rule);
  border-bottom: 4px double var(--rule); margin: 0 var(--s8) var(--s8) var(--s8);
}
.app-layout { background: var(--bg); }
"""

# Append to end of file to override previous things
with open(css_path, 'a', encoding='utf-8') as f:
    f.write("\n" + newspaper_styles)

print("index.css updated with Newspaper overrides")
