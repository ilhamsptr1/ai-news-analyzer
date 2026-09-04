import re

app_path = "e:/AI NEWS ANALYZER/ai-news-analyzer/frontend/src/App.jsx"
css_path = "e:/AI NEWS ANALYZER/ai-news-analyzer/frontend/src/index.css"

# 1. Update App.jsx (Remove dark orbs & adjust navbar wrapper)
with open(app_path, "r", encoding="utf-8") as f:
    app_code = f.read()

# Remove hero-orb and background lines in Hero Banner
app_code = re.sub(
    r'<div className="hero-banner-bg"[^>]*>[\s\S]*?</div>\s*<div className="hero-banner-inner">',
    r'<div className="hero-banner-bg" aria-hidden="true">\n                <div className="newspaper-texture" />\n              </div>\n              <div className="hero-banner-inner">',
    app_code
)

with open(app_path, "w", encoding="utf-8") as f:
    f.write(app_code)

# 2. Update index.css
with open(css_path, "r", encoding="utf-8") as f:
    css_code = f.read()

# Modify Root Variables
new_vars = """  /* Colors - Newspaper Aesthetic */
  --bg: #F4F3ED; /* Newsprint off-white */
  --surface: #FCFBF7;
  --ink: #111111; /* Sharp black */
  --ink-light: #2A2A2A;
  --slate: #333333;
  --muted: #555555;
  --faint: #888888;
  
  --rule: #111111; /* Solid black rules */
  --rule-light: rgba(17, 17, 17, 0.15);
  
  --accent: #B91C1C; /* Editorial Red */
  --accent-light: #EF4444;
  --accent-dim: rgba(185, 28, 28, 0.08);
  --accent-grad: var(--accent); /* Solid red */
  
  /* Status Colors */
  --green: #059669;
  --green-dim: rgba(5, 150, 105, 0.1);
  --red: #DC2626;
  --red-dim: rgba(220, 38, 38, 0.1);
  --amber: #D97706;
  --amber-dim: rgba(217, 119, 6, 0.1);
  --blue: #2563EB;
  --blue-dim: rgba(37, 99, 235, 0.1);

  /* Sharp Edges */
  --r-sm: 0px;
  --r-md: 0px;
  --r-lg: 0px;
  --r-xl: 0px;
  --r-full: 0px; /* Keep pill shape for buttons if needed, but let's go sharp */
"""
css_code = re.sub(r'  /\* Colors[\s\S]*?--r-full:\s*9999px;\n', new_vars, css_code)

# Ensure buttons don't stay round if we want sharp
css_code = re.sub(r'border-radius:\s*var\(--r-full\);', r'border-radius: 0;', css_code)

# Modify Navbar to Masthead
css_code = re.sub(
    r'\.navbar \{\s*display:\s*flex;[\s\S]*?z-index:\s*40;\s*\}',
    r'.navbar {\n  display: flex; align-items: center; justify-content: space-between;\n  padding: 0 var(--s8);\n  height: 80px;\n  background: var(--bg);\n  border-bottom: 4px double var(--rule);\n  position: sticky; top: 0; z-index: 40;\n}',
    css_code
)
css_code = re.sub(
    r'\.navbar-brand \{\s*display:\s*flex;[\s\S]*?\}',
    r'.navbar-brand {\n  display: flex; align-items: center; gap: var(--s3);\n  text-decoration: none;\n  padding-right: var(--s5);\n  border-right: 1px solid var(--rule);\n}',
    css_code
)
css_code = re.sub(
    r'\.navbar-title \{\n  font-family: var\(--font\);\n  font-size: 14px; font-weight: 600;\n  color: var\(--ink\); letter-spacing: -0\.01em;\n\}',
    r'.navbar-title {\n  font-family: var(--font-heading);\n  font-size: 22px; font-weight: 800;\n  color: var(--ink); text-transform: uppercase;\n  letter-spacing: 0.05em;\n}',
    css_code
)

# Modify Hero Section to Light Mode Newspaper
css_code = re.sub(
    r'\.hero-banner \{\n  position:\s*relative;\n  background:\s*#0F172A;[\s\S]*?overflow:\s*hidden;\n\}',
    r'.hero-banner {\n  position: relative;\n  background: var(--surface);\n  border-bottom: 2px solid var(--rule);\n  overflow: hidden;\n}',
    css_code
)

# Remove glowing orbs and grids, replace with newspaper texture logic
css_code = re.sub(
    r'\.hero-banner-bg \{\s*position:\s*absolute;[\s\S]*?\}',
    r'.hero-banner-bg {\n  position: absolute; inset: 0; pointer-events: none;\n}\n.newspaper-texture {\n  position: absolute; inset: 0;\n  background-image: radial-gradient(var(--rule-light) 1px, transparent 0);\n  background-size: 24px 24px;\n  opacity: 0.5;\n}',
    css_code
)

# Clean up hero orbs CSS (remove them)
css_code = re.sub(r'\.hero-orb \{\s*position:\s*absolute;[\s\S]*?@keyframes float[\s\S]*?\}', '', css_code)
css_code = re.sub(r'\.hero-grid-lines \{\s*position:\s*absolute;[\s\S]*?\}', '', css_code)

# Fix Hero Title Color
css_code = re.sub(r'color:\s*var\(--white\);', r'color: var(--ink);', css_code)
# Fix Subtitle Color
css_code = re.sub(r'color:\s*rgba\(255, 255, 255, 0\.6\);', r'color: var(--muted);', css_code)
# Fix hero buttons
css_code = re.sub(r'color:\s*rgba\(255,255,255,0\.85\);', r'color: var(--ink);', css_code)
css_code = re.sub(r'background:\s*rgba\(255,255,255,0\.08\);', r'background: transparent;', css_code)
css_code = re.sub(r'border:\s*1px\s*solid\s*rgba\(255,255,255,0\.15\);', r'border: 1px solid var(--rule);', css_code)

# Modify Cards to use thick borders instead of shadow
css_code = re.sub(
    r'box-shadow:\s*0\s*1px\s*4px\s*rgba\(15, 23, 42, 0\.04\);',
    r'box-shadow: none; border: 1px solid var(--rule);',
    css_code
)
css_code = re.sub(
    r'box-shadow:\s*0\s*1px\s*3px\s*rgba\(15,23,42,0\.04\);',
    r'box-shadow: none; border: 1px solid var(--rule);',
    css_code
)
css_code = re.sub(
    r'\.cap-card:hover \{\s*border-color:\s*var\(--accent-light\);\s*box-shadow:\s*0\s*4px\s*20px\s*var\(--accent-dim\),\s*0\s*0\s*0\s*1px\s*var\(--accent-light\);\s*transform:\s*translateY\(-2px\);\s*\}',
    r'.cap-card:hover {\n  border-color: var(--accent);\n  box-shadow: 4px 4px 0px var(--rule);\n  transform: translate(-2px, -2px);\n}',
    css_code
)

# Add Drop Cap to Article Content
drop_cap_css = """
/* Drop Cap */
.article-content-text::first-letter {
  font-family: var(--font-heading);
  font-size: 3.8em;
  font-weight: 800;
  float: left;
  line-height: 0.8;
  margin-right: 8px;
  margin-top: 4px;
  color: var(--ink);
}
"""
css_code = re.sub(r'(\.article-content-text \{\s*[\s\S]*?\})', r'\1' + drop_cap_css, css_code)

# Fix Status Toggle on Hero (was white, now needs to be black)
css_code = re.sub(
    r'\.status-toggle-btn \{\s*display:\s*inline-flex;[\s\S]*?white-space:\s*nowrap;\s*\}',
    r'.status-toggle-btn {\n  display: inline-flex; align-items: center; gap: 10px;\n  background: var(--surface);\n  border: 1px solid var(--rule);\n  color: var(--ink);\n  padding: 10px 18px;\n  border-radius: 0;\n  font-family: var(--font);\n  font-size: 14px; font-weight: 600;\n  transition: var(--t);\n  cursor: pointer;\n  white-space: nowrap;\n  box-shadow: 2px 2px 0 var(--rule);\n}',
    css_code
)
css_code = re.sub(
    r'\.status-toggle-btn:hover \{\s*background:\s*rgba\(255, 255, 255, 0\.14\);\s*border-color:\s*rgba\(255, 255, 255, 0\.25\);\s*color:\s*white;\s*\}',
    r'.status-toggle-btn:hover {\n  background: var(--bg);\n  transform: translate(1px, 1px);\n  box-shadow: 1px 1px 0 var(--rule);\n}',
    css_code
)
css_code = re.sub(r'color:\s*rgba\(255,255,255,0\.4\);', r'color: var(--muted);', css_code) # Chevron

with open(css_path, "w", encoding="utf-8") as f:
    f.write(css_code)

print("Newspaper style applied.")
