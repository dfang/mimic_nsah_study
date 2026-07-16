# Submission Render Preflight

**Checked:** 2026-07-16
**Verdict:** BLOCKED before citeproc resolution

## Tool availability

| Tool | Status | Role |
| :--- | :--- | :--- |
| Pandoc | Unavailable | Required citation resolution and bibliography generation |
| Typst | Unavailable | Preferred optional PDF layout engine |
| Google Chrome | Available | Possible PDF renderer after Pandoc creates resolved HTML |
| WeasyPrint | Available (Python package 69.0) | Diagnostic renderer only after citations are resolved |

## Safety behavior verified

`scripts/convert_manuscript_to_pdf.py` now refuses canonical manuscripts containing unresolved `[@citation_key]` syntax. A regression test demonstrates that it exits before creating or overwriting a PDF. The existing English PDF hash remained unchanged during the failed preflight:

`4d700a256e7b246efc4e6df3143b9ca4c00138d2c21d5a92c257517b42a1820c`

This prevents a visually plausible but bibliographically invalid PDF from being mistaken for a submission build.

## Commands to run when Pandoc is available

Run from `dist/` so relative bibliography, CSL, and figure paths resolve consistently:

```bash
pandoc manuscript_non_traumatic_sah_phenotypes.md \
  --citeproc \
  --bibliography=references.bib \
  --csl=journal.csl \
  --fail-if-warnings \
  --standalone \
  --resource-path=. \
  --to=html5 \
  --output=resolved-manuscript.html
```

Repeat for `electronic_supplementary_material.md` if it contains citations. Preserve the resolved intermediate as build evidence; do not edit it as the manuscript source.

After injecting the journal CSS into the resolved HTML, Chrome can render a diagnostic PDF:

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless \
  --disable-gpu \
  --print-to-pdf=pdf/manuscript_non_traumatic_sah_phenotypes_en.pdf \
  resolved-manuscript.html
```

An editable DOCX should be created from the same canonical Markdown and citeproc inputs, not reverse-converted from PDF.

## Required post-render inspection

- Numeric citations appear in order and no `[@key]` syntax remains.
- Reference entries are de-duplicated and DOI links are complete.
- Title page, author metadata, declarations, line spacing, page numbers, and line numbering satisfy the final journal instructions.
- No table, figure, caption, or reference entry is clipped.
- Vector figures are used where supported; raster fallbacks are 600 dpi.
- Title page, representative citations, widest tables, every main figure, the first/middle/final references, and the final page are visually inspected.
