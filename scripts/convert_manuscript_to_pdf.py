#!/usr/bin/env python3
"""
Convert markdown manuscripts to publication-quality PDF.
Professional typography with journal-style formatting.
"""
import os
import sys

# On macOS, WeasyPrint needs Homebrew libraries (glib, pango, cairo) which are located in /opt/homebrew/lib.
# Setting DYLD_FALLBACK_LIBRARY_PATH in os.environ before importing weasyprint allows cffi to find them.
if sys.platform == "darwin":
    homebrew_lib = "/opt/homebrew/lib"
    if os.path.exists(homebrew_lib):
        if "DYLD_FALLBACK_LIBRARY_PATH" not in os.environ:
            os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = homebrew_lib
        else:
            os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = f"{homebrew_lib}:{os.environ['DYLD_FALLBACK_LIBRARY_PATH']}"

import markdown
from weasyprint import HTML
import re

# PDF output directory will be created dynamically inside the convert function.

# ═══════════════════════════════════════════════════════════════
# Professional CSS — journal manuscript style
# ═══════════════════════════════════════════════════════════════

CSS_EN = r"""
/* ── Page setup ─────────────────────────────────────────── */
@page {
    size: A4;
    margin: 2.5cm 2.5cm 2.8cm 2.5cm;
    background: #fff;
    @bottom-center {
        content: counter(page);
        font-family: "Times New Roman", serif;
        font-size: 9pt;
        color: #666;
    }
}
@page :first {
    @bottom-center { content: none; }
    margin-top: 3cm;
}

/* ── Body & Typography ──────────────────────────────────── */
body {
    font-family: "Times New Roman", "Georgia", serif;
    font-size: 11.5pt;
    line-height: 1.7;
    color: #1a1a1a;
    background: #fff;
    text-align: justify;
    hyphens: auto;
    widows: 3;
    orphans: 3;
}

/* ── Title page ─────────────────────────────────────────── */
h1 {
    font-family: "Times New Roman", "Georgia", serif;
    font-size: 16pt;
    font-weight: 700;
    text-align: center;
    line-height: 1.35;
    color: #111;
    margin-top: 0;
    margin-bottom: 18pt;
    letter-spacing: -0.2pt;
}
h1 + p {
    text-align: center;
    font-size: 10pt;
    color: #555;
    margin-bottom: 6pt;
}
h1 + p strong {
    font-weight: 600;
}

/* ── Section headings ───────────────────────────────────── */
h2 {
    font-family: "Times New Roman", "Georgia", serif;
    font-size: 13pt;
    font-weight: 700;
    margin-top: 28pt;
    margin-bottom: 10pt;
    padding-bottom: 4pt;
    border-bottom: 1.2pt solid #222;
    color: #111;
    page-break-after: avoid;
}
h3 {
    font-family: "Times New Roman", "Georgia", serif;
    font-size: 12pt;
    font-weight: 700;
    margin-top: 20pt;
    margin-bottom: 8pt;
    color: #222;
    page-break-after: avoid;
}
h4 {
    font-family: "Times New Roman", "Georgia", serif;
    font-size: 11.5pt;
    font-weight: 700;
    font-style: italic;
    margin-top: 14pt;
    margin-bottom: 6pt;
    color: #333;
    page-break-after: avoid;
}

/* ── Paragraphs ─────────────────────────────────────────── */
p {
    margin-top: 0;
    margin-bottom: 8pt;
}

/* ── Abstract labels ────────────────────────────────────── */
strong {
    color: #1a1a1a;
}

/* ── Horizontal rules ───────────────────────────────────── */
hr {
    border: none;
    border-top: 0.8pt solid #999;
    margin: 22pt 0;
}

/* ── Figures ────────────────────────────────────────────── */
figure {
    text-align: center;
    margin: 14pt 0 14pt 0;
    page-break-inside: avoid;
}
img {
    max-width: 100%;
    max-height: 17cm;
    width: auto;
    height: auto;
}
figure img {
    max-width: 100%;
    max-height: 16.5cm;
    height: auto;
    width: auto;
    display: block;
    margin: 0 auto;
    border: 0.3pt solid #ddd;
}
figure figcaption {
    font-size: 9pt;
    color: #444;
    font-style: italic;
    margin-top: 6pt;
    padding: 0 8pt;
    text-align: left;
}
figure figcaption strong {
    font-style: normal;
    font-weight: 700;
    color: #222;
}

/* ── Tables (academic three-line style) ─────────────────── */
table {
    width: 100%;
    table-layout: fixed;
    border-collapse: collapse;
    margin: 16pt 0 18pt 0;
    font-size: 8.6pt;
    line-height: 1.25;
    page-break-inside: auto;
}
thead { display: table-header-group; }
thead th {
    font-weight: 700;
    padding: 6pt 7pt 5pt 7pt;
    text-align: left;
    border-top: 1.5pt solid #222;
    border-bottom: 0.8pt solid #222;
    background: none;
    color: #111;
    font-size: 9.5pt;
}
tbody td {
    padding: 4pt 7pt;
    text-align: left;
    border: none;
    background: none;
    overflow-wrap: anywhere;
}
tbody tr:last-child td {
    border-bottom: 1.2pt solid #222;
}
tbody tr:nth-child(even) td {
    background-color: #fafafa;
}

/* ── Lists ──────────────────────────────────────────────── */
ol {
    margin: 6pt 0 10pt 0;
    padding-left: 22pt;
    list-style-type: decimal;
}
ol li {
    margin-bottom: 3pt;
}
ol li p {
    margin-bottom: 2pt;
}

/* ── Code ───────────────────────────────────────────────── */
code {
    font-family: "Consolas", "Monaco", "Courier New", monospace;
    font-size: 9pt;
    background: #f4f4f4;
    padding: 1pt 4pt;
    border-radius: 2pt;
    border: 0.3pt solid #e0e0e0;
}

/* ── Blockquote ─────────────────────────────────────────── */
blockquote {
    border-left: 3pt solid #555;
    padding: 6pt 14pt;
    margin: 12pt 0;
    color: #444;
    background: #f9f9f9;
}

/* ── Running title area ─────────────────────────────────── */
h1 + p + p + p + hr {
    margin-top: 28pt;
}
"""

CSS_CN = r"""
/* ── Chinese-specific typography ────────────────────────── */
body {
    font-family: "Songti SC", "SimSun", "Noto Serif CJK SC", "Times New Roman", serif;
    font-size: 11.5pt;
    line-height: 1.85;
    text-align: left;
    text-justify: none;
}
p, li { text-align: left; }
h1 {
    font-family: "PingFang SC", "Heiti SC", "Noto Sans CJK SC", "Microsoft YaHei", sans-serif;
    font-size: 17pt;
    font-weight: 700;
    text-align: center;
    line-height: 1.45;
}
h2 {
    font-family: "PingFang SC", "Heiti SC", "Noto Sans CJK SC", "Microsoft YaHei", sans-serif;
    font-size: 14pt;
    font-weight: 700;
    margin-top: 28pt;
    margin-bottom: 10pt;
    padding-bottom: 4pt;
    border-bottom: 1.5pt solid #222;
}
h3 {
    font-family: "PingFang SC", "Heiti SC", "Noto Sans CJK SC", "Microsoft YaHei", sans-serif;
    font-size: 12.5pt;
    font-weight: 700;
    margin-top: 20pt;
    margin-bottom: 8pt;
}
h4 {
    font-family: "PingFang SC", "Heiti SC", "Noto Sans CJK SC", "Microsoft YaHei", sans-serif;
    font-size: 11.5pt;
    font-weight: 700;
    margin-top: 14pt;
    margin-bottom: 6pt;
}
table { font-size: 9pt; }
thead th { font-size: 9pt; }
figure figcaption { font-size: 9pt; }
"""


def preprocess_markdown(md_path):
    """Read markdown and fix image paths to absolute."""
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    replacements = {
        r"$\ge$": "≥",
        r"$\le$": "≤",
        r"$p < 0.001$": "p < 0.001",
        r"$\times 10^3$/µL": "×10³/µL",
        r"$\times 10^3$/μL": "×10³/µL",
    }
    for source, target in replacements.items():
        content = content.replace(source, target)
    content = re.sub(r"\$K\s*=\s*([0-9]+)\$", r"K=\1", content)
    content = re.sub(r"\$\s*([^$]{1,24})\s*\$", r"\1", content)

    base_dir = os.path.dirname(os.path.abspath(md_path))
    relative_image = r"(!\[[^\]]*\]\()(?!(?:[a-z][a-z0-9+.-]*:|/|#))([^)]+)\)"
    content = re.sub(
        relative_image,
        lambda match: f"{match.group(1)}file://{base_dir}/{match.group(2)})",
        content,
        flags=re.IGNORECASE,
    )
    return content


def md_to_html(md_content):
    """Convert markdown to clean HTML."""
    html = markdown.markdown(
        md_content,
        extensions=["tables", "fenced_code", "nl2br"]
    )
    # Remove stray empty <p> tags
    html = re.sub(r'<p>\s*</p>\n?', '', html)
    return html


def wrap_figures(html):
    """Wrap <img> + caption into <figure> containers for proper layout."""
    pattern = (
        r'<p><img (.*?)/?></p>\s*\n?\s*'
        r'<p>(<(?:strong|b)>((?:Supplementary\s+Figure|Figure|附图|图)\s*[^<]+)</(?:strong|b)>.*?)</p>'
    )
    replacement = (
        r'<figure>\n'
        r'  <img \1 />\n'
        r'  <figcaption>\2</figcaption>\n'
        r'</figure>'
    )
    return re.sub(pattern, replacement, html)


def build_html(body_html, css, lang="en"):
    """Assemble full HTML document."""
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<style>{css}</style>
</head>
<body>
{body_html}
</body>
</html>"""


def convert(md_path, pdf_path, css, lang="en"):
    """Full conversion pipeline: MD → HTML → PDF."""
    pdf_dir = os.path.dirname(pdf_path)
    if pdf_dir:
        os.makedirs(pdf_dir, exist_ok=True)
    md_content = preprocess_markdown(md_path)
    body_html = md_to_html(md_content)
    body_html = wrap_figures(body_html)
    full_html = build_html(body_html, css, lang)

    HTML(string=full_html).write_pdf(pdf_path)
    size_kb = os.path.getsize(pdf_path) / 1024
    print(f"  ✓ {os.path.basename(pdf_path)}  ({size_kb:.0f} KB)")


# ═══════════════════════════════════════════════════════════════
def main() -> None:
    """Generate canonical manuscript PDFs under dist/pdf/."""
    base = "dist"

    print(f"Converting manuscripts to PDF in {base}...\n")

    convert(
        f"{base}/manuscript_non_traumatic_sah_phenotypes.md",
        f"{base}/pdf/manuscript_non_traumatic_sah_phenotypes_en.pdf",
        CSS_EN,
        lang="en",
    )

    convert(
        f"{base}/manuscript_non_traumatic_sah_phenotypes_cn.md",
        f"{base}/pdf/manuscript_non_traumatic_sah_phenotypes_cn.pdf",
        CSS_EN + CSS_CN,
        lang="zh",
    )

    optional_outputs = [
        (
            f"{base}/electronic_supplementary_material.md",
            f"{base}/pdf/electronic_supplementary_material.pdf",
            CSS_EN,
            "en",
        ),
        (
            f"{base}/strobe_checklist.md",
            f"{base}/pdf/strobe_checklist.pdf",
            CSS_EN,
            "en",
        ),
    ]
    for md_path, pdf_path, css, lang in optional_outputs:
        if os.path.exists(md_path):
            convert(md_path, pdf_path, css, lang=lang)

    print(f"\nDone → {base}/pdf/")


if __name__ == "__main__":
    main()
