# Flatten Manuscript Output Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `dist/` and `dist/pdf/` the canonical manuscript locations without changing dated analysis-result or figure outputs.

**Architecture:** The PDF converter will expose a small `main()` entry point whose fixed base directory is `dist/`; required manuscript Markdown and optional supplementary Markdown flow through the existing `convert()` function. The latest tracked manuscript artifacts will be moved from `dist/20260711/` to those canonical paths, while active instructions distinguish stable manuscript outputs from dated analysis snapshots.

**Tech Stack:** Python 3, pytest, Markdown, WeasyPrint, pypdf, Git

## Global Constraints

- Do not add dependencies.
- Keep `scripts/run_non_traumatic_sah_bigquery_pipeline.sh` and `scripts/generate_manuscript_figures.py` date-based.
- Preserve `dist/20260711/analysis_result.md` and `dist/20260711/figures/`.
- Preserve older dated manuscript directories as historical snapshots.
- Required English and Chinese manuscript inputs remain fail-fast; ESM and STROBE remain optional.
- Keep the macOS WeasyPrint library-path setup before importing WeasyPrint.

---

### Task 1: Lock the canonical manuscript-path contract

**Files:**
- Create: `tests/test_manuscript_output_paths.py`
- Test: `tests/test_manuscript_output_paths.py`

**Interfaces:**
- Consumes: repository files as UTF-8 text via `ROOT / path`
- Produces: regression tests defining the no-date converter command and stable manuscript paths

- [ ] **Step 1: Write the failing regression tests**

```python
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_pdf_converter_uses_stable_dist_directory() -> None:
    script = read_text("scripts/convert_manuscript_to_pdf.py")

    assert 'base = "dist"' in script
    assert "date_dir" not in script
    assert "datetime" not in script
    assert "sys.argv" not in script


def test_active_instructions_use_canonical_manuscript_paths() -> None:
    agents = read_text("AGENTS.md")
    prompt = read_text("scripts/prompt_for_regenerating_manuscript.md")

    assert "`dist/manuscript_non_traumatic_sah_phenotypes.md`" in agents
    assert "`dist/pdf/`" in agents
    assert "dist/YYYYMMDD/manuscript_non_traumatic_sah_phenotypes" not in prompt
    assert "dist/YYYYMMDD/electronic_supplementary_material" not in prompt
    assert "dist/YYYYMMDD/strobe_checklist" not in prompt
    assert "convert_manuscript_to_pdf.py YYYYMMDD" not in prompt


def test_canonical_manuscripts_reference_dated_figures() -> None:
    english = read_text("dist/manuscript_non_traumatic_sah_phenotypes.md")
    chinese = read_text("dist/manuscript_non_traumatic_sah_phenotypes_cn.md")
    supplement = read_text("dist/electronic_supplementary_material.md")

    for document in (english, chinese, supplement):
        assert "](figures/" not in document
        assert "](20260711/figures/" in document
```

- [ ] **Step 2: Run the focused test and verify it fails**

Run: `python3 -m pytest tests/test_manuscript_output_paths.py -q`

Expected: FAIL because the converter still defines `date_dir`, and active instructions still use dated manuscript paths.

- [ ] **Step 3: Commit the contract test**

```bash
git add tests/test_manuscript_output_paths.py
git commit -m "Guard canonical manuscript output paths" \
  -m "Confidence: high" \
  -m "Scope-risk: narrow" \
  -m "Tested: python3 -m pytest tests/test_manuscript_output_paths.py -q (expected failure before implementation)"
```

---

### Task 2: Flatten converter paths and migrate the latest artifacts

**Files:**
- Modify: `scripts/convert_manuscript_to_pdf.py:363-407`
- Move: `dist/20260711/manuscript_non_traumatic_sah_phenotypes.md` → `dist/manuscript_non_traumatic_sah_phenotypes.md`
- Move: `dist/20260711/manuscript_non_traumatic_sah_phenotypes_cn.md` → `dist/manuscript_non_traumatic_sah_phenotypes_cn.md`
- Move: `dist/20260711/electronic_supplementary_material.md` → `dist/electronic_supplementary_material.md`
- Move: `dist/20260711/strobe_checklist.md` → `dist/strobe_checklist.md`
- Move: `dist/20260711/readme.txt` → `dist/readme.txt`
- Move: `dist/20260711/pdf/manuscript_non_traumatic_sah_phenotypes_en.pdf` → `dist/pdf/manuscript_non_traumatic_sah_phenotypes_en.pdf`
- Move: `dist/20260711/pdf/manuscript_non_traumatic_sah_phenotypes_cn.pdf` → `dist/pdf/manuscript_non_traumatic_sah_phenotypes_cn.pdf`
- Move: `dist/20260711/pdf/electronic_supplementary_material.pdf` → `dist/pdf/electronic_supplementary_material.pdf`
- Move: `dist/20260711/pdf/strobe_checklist.pdf` → `dist/pdf/strobe_checklist.pdf`
- Modify after move: `dist/manuscript_non_traumatic_sah_phenotypes.md`
- Modify after move: `dist/manuscript_non_traumatic_sah_phenotypes_cn.md`
- Modify after move: `dist/electronic_supplementary_material.md`

**Interfaces:**
- Consumes: required Markdown at `dist/manuscript_non_traumatic_sah_phenotypes.md` and `dist/manuscript_non_traumatic_sah_phenotypes_cn.md`; optional ESM and STROBE Markdown at `dist/`
- Produces: four PDFs under `dist/pdf/` when all four Markdown files exist

- [ ] **Step 1: Move the latest tracked manuscript artifacts**

```bash
mkdir -p dist/pdf
git mv dist/20260711/manuscript_non_traumatic_sah_phenotypes.md dist/
git mv dist/20260711/manuscript_non_traumatic_sah_phenotypes_cn.md dist/
git mv dist/20260711/electronic_supplementary_material.md dist/
git mv dist/20260711/strobe_checklist.md dist/
git mv dist/20260711/readme.txt dist/
git mv dist/20260711/pdf/*.pdf dist/pdf/
```

- [ ] **Step 2: Keep manuscript image links pointed at the dated figure snapshot**

In the three moved Markdown files, replace every relative image target prefix exactly as follows:

```diff
-](figures/
+](20260711/figures/
```

This changes 5 English main-manuscript links, 5 Chinese main-manuscript links, and 7 ESM links. It does not move or rename any figure.

- [ ] **Step 3: Replace the dated command entry point with a stable one**

Replace the `if __name__ == "__main__":` block with:

```python
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
```

Remove the now-unused `import datetime` and second `import sys` from the old entry-point block. Keep the top-level `sys` import used by the macOS setup.

- [ ] **Step 4: Run the focused tests and syntax check**

Run: `python3 -m pytest tests/test_manuscript_output_paths.py::test_pdf_converter_uses_stable_dist_directory tests/test_manuscript_output_paths.py::test_canonical_manuscripts_reference_dated_figures -q && python3 -m py_compile scripts/convert_manuscript_to_pdf.py`

Expected: PASS with two pytest tests passed and no `py_compile` output.

- [ ] **Step 5: Commit the converter and artifact migration**

```bash
git add scripts/convert_manuscript_to_pdf.py dist
git commit -m "Make manuscript deliverables date-independent" \
  -m "Constraint: Dated analysis results and figures remain unchanged." \
  -m "Confidence: high" \
  -m "Scope-risk: moderate" \
  -m "Tested: Canonical path and dated figure-reference regression tests." \
  -m "Tested: python3 -m py_compile scripts/convert_manuscript_to_pdf.py"
```

---

### Task 3: Update active instructions and artifact metadata

**Files:**
- Modify: `AGENTS.md:35-46`
- Modify: `scripts/prompt_for_regenerating_manuscript.md:102-120,675-737`
- Modify: `dist/readme.txt:1-25`
- Test: `tests/test_manuscript_output_paths.py`

**Interfaces:**
- Consumes: the canonical paths established in Task 2
- Produces: unambiguous user and agent instructions that retain dated analysis/figure inputs

- [ ] **Step 1: Split repository conventions by artifact type**

Replace the blanket dated-output rule in `AGENTS.md` with:

```markdown
- canonical manuscript 产物直接放在 `dist/`：Markdown、`readme.txt` 和 `pdf/` 不再使用 `YYYYMMDD` 子目录。
- 分析结果和图表快照仍可放入 `dist/YYYYMMDD/`，以保留生成日期和数据版本。
- `dist/readme.txt` 必须明确说明 manuscript Markdown 和 PDF 由哪个模型（如 `codex`、`gemini` 或 `claude`）生成。
```

- [ ] **Step 2: Update active manuscript-generation instructions**

Apply these exact path rules throughout `scripts/prompt_for_regenerating_manuscript.md`:

```text
Canonical manuscript files:
  dist/manuscript_non_traumatic_sah_phenotypes.md
  dist/manuscript_non_traumatic_sah_phenotypes_cn.md
  dist/electronic_supplementary_material.md
  dist/strobe_checklist.md
  dist/readme.txt
  dist/pdf/*.pdf

Dated analysis inputs retained:
  dist/YYYYMMDD/analysis_result.md
  dist/YYYYMMDD/figures/

PDF command:
  python3 scripts/convert_manuscript_to_pdf.py
```

Keep `python3 scripts/generate_manuscript_figures.py YYYYMMDD` unchanged.

- [ ] **Step 3: Update migrated generation metadata paths**

In `dist/readme.txt`, keep the existing model and preparation date, keep dated analysis/figure inputs, change the manuscript input from `dist/20260711/manuscript_non_traumatic_sah_phenotypes.md` to `dist/manuscript_non_traumatic_sah_phenotypes.md`, and change the artifact list to:

```text
Generated artifacts:
- dist/manuscript_non_traumatic_sah_phenotypes.md (ICM-style English main manuscript)
- dist/manuscript_non_traumatic_sah_phenotypes_cn.md (Chinese reference version)
- dist/electronic_supplementary_material.md (Electronic Supplementary Material)
- dist/strobe_checklist.md (STROBE checklist)
- dist/pdf/manuscript_non_traumatic_sah_phenotypes_en.pdf (English main manuscript PDF)
- dist/pdf/manuscript_non_traumatic_sah_phenotypes_cn.pdf (Chinese reference PDF)
- dist/pdf/electronic_supplementary_material.pdf (ESM PDF)
- dist/pdf/strobe_checklist.pdf (STROBE checklist PDF)
```

- [ ] **Step 4: Run the full path-contract test**

Run: `python3 -m pytest tests/test_manuscript_output_paths.py -q`

Expected: PASS with three tests passed.

- [ ] **Step 5: Commit the documentation migration**

```bash
git add AGENTS.md scripts/prompt_for_regenerating_manuscript.md dist/readme.txt tests/test_manuscript_output_paths.py
git commit -m "Document canonical manuscript locations" \
  -m "Constraint: Analysis results and figures continue to use dated snapshots." \
  -m "Confidence: high" \
  -m "Scope-risk: narrow" \
  -m "Tested: python3 -m pytest tests/test_manuscript_output_paths.py -q"
```

---

### Task 4: Regenerate and verify canonical PDFs

**Files:**
- Modify: `dist/pdf/manuscript_non_traumatic_sah_phenotypes_en.pdf`
- Modify: `dist/pdf/manuscript_non_traumatic_sah_phenotypes_cn.pdf`
- Modify: `dist/pdf/electronic_supplementary_material.pdf`
- Modify: `dist/pdf/strobe_checklist.pdf`

**Interfaces:**
- Consumes: canonical Markdown under `dist/` and dated figure references embedded in those files
- Produces: readable canonical PDFs under `dist/pdf/`

- [ ] **Step 1: Generate all PDFs with the no-date command**

Run: `python3 scripts/convert_manuscript_to_pdf.py`

Expected: four success lines followed by `Done → dist/pdf/`.

- [ ] **Step 2: Parse every generated PDF**

Run:

```bash
python3 - <<'PY'
from pathlib import Path
from pypdf import PdfReader

expected = {
    "electronic_supplementary_material.pdf",
    "manuscript_non_traumatic_sah_phenotypes_cn.pdf",
    "manuscript_non_traumatic_sah_phenotypes_en.pdf",
    "strobe_checklist.pdf",
}
pdf_dir = Path("dist/pdf")
assert {path.name for path in pdf_dir.glob("*.pdf")} == expected
for path in sorted(pdf_dir.glob("*.pdf")):
    reader = PdfReader(path)
    pages = len(reader.pages)
    assert pages > 0, path
    print(f"{path}: {pages} pages")

english = PdfReader(pdf_dir / "manuscript_non_traumatic_sah_phenotypes_en.pdf")
supplement = PdfReader(pdf_dir / "electronic_supplementary_material.pdf")
assert sum(len(page.images) for page in english.pages) >= 5
assert sum(len(page.images) for page in supplement.pages) >= 7
print("Embedded manuscript figures verified")
PY
```

Expected: four paths printed with positive page counts, followed by `Embedded manuscript figures verified`.

- [ ] **Step 3: Verify migration boundaries and active references**

Run:

```bash
test -f dist/20260711/analysis_result.md
test -d dist/20260711/figures
test ! -e dist/20260711/manuscript_non_traumatic_sah_phenotypes.md
test ! -e dist/20260711/pdf
rg -n "dist/YYYYMMDD/(manuscript_non_traumatic_sah_phenotypes|electronic_supplementary_material|strobe_checklist)|convert_manuscript_to_pdf.py YYYYMMDD" AGENTS.md scripts --glob '!docs/superpowers/plans/2026-07-07-regenerate-manuscript.md'
```

Expected: all `test` commands succeed and `rg` returns no matches.

- [ ] **Step 4: Run repository verification**

Run: `python3 -m pytest -q && git diff --check && git status --short`

Expected: all tests pass, `git diff --check` prints nothing, and status contains only the four regenerated canonical PDFs if their binary serialization changed.

- [ ] **Step 5: Commit regenerated PDFs if changed**

```bash
git add -f dist/pdf/*.pdf
git diff --cached --quiet || git commit -m "Refresh canonical manuscript PDFs" \
  -m "Confidence: high" \
  -m "Scope-risk: narrow" \
  -m "Tested: Parsed all four PDFs with pypdf." \
  -m "Tested: python3 -m pytest -q" \
  -m "Tested: git diff --check"
```
