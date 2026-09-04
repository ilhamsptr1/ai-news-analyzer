import re

file_path = "e:/AI NEWS ANALYZER/ai-news-analyzer/frontend/src/index.css"

with open(file_path, "r", encoding="utf-8") as f:
    css = f.read()

# 1. Imports
css = re.sub(
    r"@import url\('https://fonts.googleapis.com/css2\?family=Inter[^\']*'\);",
    r"@import url('https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,400&family=Manrope:wght@400;500;600;700;800&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&display=swap');",
    css
)

# 2. Font variables
css = re.sub(
    r"(--font:\s*'Inter', system-ui, -apple-system, sans-serif;)",
    r"\1\n  --font-heading: 'Manrope', system-ui, -apple-system, sans-serif;\n  --font-serif: 'Source Serif 4', Georgia, serif;",
    css
)

# 3. Navbar (Inter, 14px, 500-600)
css = re.sub(
    r"\.navbar-title \{\s*font-size:\s*0\.95rem;\s*font-weight:\s*700;",
    r".navbar-title {\n  font-family: var(--font);\n  font-size: 14px; font-weight: 600;",
    css
)
css = re.sub(
    r"(\.navbar-tab \{\s*[\s\S]*?border-radius:\s*var\(--r-full\);)\s*font-size:\s*0\.875rem;\s*font-weight:\s*500;",
    r"\1\n  font-family: var(--font);\n  font-size: 14px; font-weight: 500;",
    css
)

# 4. Hero Title (Manrope, 48px, 700) and Subtitle (Inter, 16px)
css = re.sub(
    r"\.hero-title \{\s*font-size:\s*4rem;\s*font-weight:\s*900;\s*line-height:\s*1\.08;\s*letter-spacing:\s*-0\.035em;",
    r".hero-title {\n  font-family: var(--font-heading);\n  font-size: 48px;\n  font-weight: 700;\n  line-height: 1.1;\n  letter-spacing: -0.02em;",
    css
)
css = re.sub(
    r"\.hero-subtitle \{\s*font-size:\s*1\.1rem;",
    r".hero-subtitle {\n  font-family: var(--font);\n  font-size: 16px;",
    css
)

# 5. Buttons (Inter, 14-15px, 600)
css = re.sub(
    r"(\.hero-btn-primary \{\s*[\s\S]*?border-radius:\s*var\(--r-full\);)\s*font-size:\s*0\.95rem;\s*font-weight:\s*600;",
    r"\1\n  font-family: var(--font);\n  font-size: 15px; font-weight: 600;",
    css
)
css = re.sub(
    r"(\.hero-btn-ghost \{\s*[\s\S]*?border-radius:\s*var\(--r-full\);)\s*font-size:\s*0\.95rem;\s*font-weight:\s*500;",
    r"\1\n  font-family: var(--font);\n  font-size: 15px; font-weight: 600;",
    css
)
css = re.sub(
    r"(\.btn-primary \{\s*[\s\S]*?border-radius:\s*var\(--r-full\);)\s*font-weight:\s*600;\s*font-size:\s*0\.875rem;",
    r"\1\n  font-family: var(--font);\n  font-weight: 600; font-size: 14px;",
    css
)
css = re.sub(
    r"(\.btn-secondary \{\s*[\s\S]*?border-radius:\s*var\(--r-full\);)\s*font-weight:\s*500;\s*font-size:\s*0\.875rem;",
    r"\1\n  font-family: var(--font);\n  font-weight: 600; font-size: 14px;",
    css
)

# 6. Page Headings & Section Headings (Manrope, 36-48px and 22-28px, 700)
css = re.sub(
    r"\.capabilities-title \{\s*font-size:\s*1\.75rem;\s*font-weight:\s*800;\s*letter-spacing:\s*-0\.025em;",
    r".capabilities-title {\n  font-family: var(--font-heading);\n  font-size: 28px; font-weight: 700;\n  letter-spacing: -0.01em;",
    css
)
css = re.sub(r"\.capabilities-subtitle \{\s*color:\s*var\(--muted\);\s*font-size:\s*1rem;", r".capabilities-subtitle { font-family: var(--font); color: var(--muted); font-size: 16px;", css)

css = re.sub(
    r"\.analyzer-header h2 \{\s*font-size:\s*1\.75rem;\s*font-weight:\s*800;\s*letter-spacing:\s*-0\.02em;",
    r".analyzer-header h2 {\n  font-family: var(--font-heading);\n  font-size: 36px; font-weight: 700;\n  letter-spacing: -0.02em;",
    css
)
css = re.sub(
    r"\.extractor-title \{\s*font-size:\s*1\.75rem;\s*font-weight:\s*800;\s*letter-spacing:\s*-0\.025em;",
    r".extractor-title {\n  font-family: var(--font-heading);\n  font-size: 36px; font-weight: 700;\n  letter-spacing: -0.025em;",
    css
)
css = re.sub(
    r"\.dash-title \{\s*font-size:\s*1\.85rem;\s*font-weight:\s*800;\s*letter-spacing:\s*-0\.025em;",
    r".dash-title {\n  font-family: var(--font-heading);\n  font-size: 36px; font-weight: 700;\n  letter-spacing: -0.02em;",
    css
)

# 7. Card Titles (Inter, 16-18px, 600)
css = re.sub(
    r"\.cap-card-label \{\s*font-weight:\s*700;\s*font-size:\s*0\.95rem;",
    r".cap-card-label {\n  font-family: var(--font);\n  font-weight: 600; font-size: 18px;",
    css
)
css = re.sub(
    r"\.dash-card-title \{\s*font-size:\s*0\.95rem;\s*font-weight:\s*700;",
    r".dash-card-title {\n  font-family: var(--font);\n  font-size: 18px; font-weight: 600;",
    css
)

# 8. Statistics (Inter, 24-32px, 700)
css = re.sub(
    r"\.dash-overview-value \{\s*font-size:\s*1\.85rem;\s*font-weight:\s*800;\s*letter-spacing:\s*-0\.02em;",
    r".dash-overview-value {\n  font-family: var(--font);\n  font-size: 32px; font-weight: 700;\n  letter-spacing: -0.02em;",
    css
)

# 9. Article Title & Content
css = re.sub(
    r"\.article-result-title \{\s*font-size:\s*1\.65rem;\s*font-weight:\s*800;\s*line-height:\s*1\.25;",
    r".article-result-title {\n  font-family: var(--font-heading);\n  font-size: 36px; font-weight: 700;\n  line-height: 1.25;",
    css
)
css = re.sub(
    r"(\.article-content-text \{\s*[\s\S]*?padding:\s*var\(--s5\)\s*var\(--s6\);)\s*font-size:\s*1rem;\s*line-height:\s*1\.8;\s*color:\s*var\(--slate\);",
    r"\1\n  font-family: var(--font-serif);\n  font-size: 18px; line-height: 1.7; font-weight: 400; color: var(--slate);",
    css
)

# 10. Status/Label (Inter 14-16px)
css = re.sub(r"\.status-card-title \{\s*font-size:\s*0\.72rem;", r".status-card-title { font-family: var(--font); font-size: 12px;", css) # smaller for label
css = re.sub(r"\.article-content-label \{\s*font-size:\s*0\.72rem;", r".article-content-label { font-family: var(--font); font-size: 12px;", css)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(css)

print("Typography updated successfully.")
