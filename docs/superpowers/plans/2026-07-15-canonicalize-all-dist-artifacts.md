# Canonicalize All Dist Artifacts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move every generated aggregate artifact to stable Git-managed paths under `dist/` while keeping stale date-bearing command invocations operational through explicit deprecation shims.

**Architecture:** A small dependency-free Python CLI helper validates and warns about legacy `YYYYMMDD` positional arguments for both figure and PDF generators; the BigQuery shell pipeline implements the equivalent `--date` compatibility locally. The latest 20260711 analysis and figures become the canonical `dist/analysis_result.md` and `dist/figures/`, historical snapshots are deleted, and regression tests plus Git audits enforce the tree contract.

**Tech Stack:** Python 3, Bash, pytest, Git, WeasyPrint, pypdf

## Global Constraints

- Do not add dependencies.
- Preserve the user-authorized deletions of `dist/20260707/` and `dist/20260708/`.
- Recover only the latest 20260711 analysis result and figures from HEAD, then move them immediately to canonical paths.
- Keep patient-level exports, credentials, and PHI out of Git.
- Commit generated aggregate Markdown, JSON, PNG, and PDF artifacts under `dist/`.
- Repository-owned commands use no date argument.
- Legacy date arguments may warn and be ignored, but may never alter canonical output paths.

---

### Task 1: Define the canonical path and compatibility contracts

**Files:**
- Create: `tests/test_artifact_cli_compatibility.py`
- Modify: `tests/test_manuscript_output_paths.py`

**Interfaces:**
- Consumes: `accept_legacy_date_arg(args: list[str], program: str) -> None` from the not-yet-created `scripts.artifact_cli` module
- Produces: failing tests for legacy date validation, canonical output paths, and date-free manuscript links

- [ ] **Step 1: Write failing compatibility tests**

Create `tests/test_artifact_cli_compatibility.py`:

```python
from pathlib import Path

import pytest

from scripts.artifact_cli import accept_legacy_date_arg


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_no_legacy_date_argument_is_silent(capsys: pytest.CaptureFixture[str]) -> None:
    accept_legacy_date_arg([], "generator")
    assert capsys.readouterr().err == ""


def test_legacy_date_argument_warns_and_is_ignored(
    capsys: pytest.CaptureFixture[str],
) -> None:
    accept_legacy_date_arg(["20260711"], "generator")
    assert "deprecated" in capsys.readouterr().err.lower()


@pytest.mark.parametrize("args", [["not-a-date"], ["20260711", "extra"]])
def test_invalid_legacy_arguments_fail(args: list[str]) -> None:
    with pytest.raises(SystemExit, match="Usage"):
        accept_legacy_date_arg(args, "generator")


def test_generators_use_canonical_output_paths() -> None:
    pipeline = read_text("scripts/run_non_traumatic_sah_bigquery_pipeline.sh")
    figures = read_text("scripts/generate_manuscript_figures.py")
    converter = read_text("scripts/convert_manuscript_to_pdf.py")

    assert 'output_file="dist/analysis_result.md"' in pipeline
    assert 'figures_dir = "dist/figures"' in figures
    assert 'base = "dist"' in converter
    assert "date_dir" not in pipeline
    assert "date_dir" not in figures
    assert "date_dir" not in converter
```

- [ ] **Step 2: Replace dated-figure expectations in manuscript tests**

In `tests/test_manuscript_output_paths.py`, replace the dated-figure test and preprocessing fixture with:

```python
def test_canonical_manuscripts_reference_canonical_figures() -> None:
    english = read_text("dist/manuscript_non_traumatic_sah_phenotypes.md")
    chinese = read_text("dist/manuscript_non_traumatic_sah_phenotypes_cn.md")
    supplement = read_text("dist/electronic_supplementary_material.md")

    for document in (english, chinese, supplement):
        assert "](figures/" in document
        assert "](20260711/figures/" not in document


def test_preprocess_resolves_canonical_relative_figure_path(tmp_path: Path) -> None:
    manuscript = tmp_path / "manuscript.md"
    manuscript.write_text("![Figure](figures/figure.png)", encoding="utf-8")

    result = preprocess_markdown(manuscript)

    assert f"](file://{tmp_path}/figures/figure.png)" in result
```

Remove the obsolete assertions that `sys.argv` is absent because the PDF compatibility shim intentionally reads arguments.

- [ ] **Step 3: Run tests and verify the red phase**

Run: `python3 -m pytest tests/test_artifact_cli_compatibility.py tests/test_manuscript_output_paths.py -q`

Expected: collection fails because `scripts.artifact_cli` does not exist, proving the compatibility contract is not implemented.

- [ ] **Step 4: Commit the failing contract tests**

```bash
git add tests/test_artifact_cli_compatibility.py tests/test_manuscript_output_paths.py
git commit -m "Guard canonical artifact paths and legacy callers" \
  -m "Confidence: high" \
  -m "Scope-risk: narrow" \
  -m "Tested: Focused tests fail because scripts.artifact_cli is not implemented."
```

---

### Task 2: Canonicalize generator command interfaces

**Files:**
- Create: `scripts/artifact_cli.py`
- Modify: `scripts/convert_manuscript_to_pdf.py:1-20,363-410`
- Modify: `scripts/generate_manuscript_figures.py:1-30`
- Modify: `scripts/run_non_traumatic_sah_bigquery_pipeline.sh:1-80`
- Test: `tests/test_artifact_cli_compatibility.py`

**Interfaces:**
- Produces: `accept_legacy_date_arg(args: list[str], program: str) -> None`
- Consumes: `sys.argv[1:]` in the two Python generators and `--date YYYYMMDD` in the shell pipeline

- [ ] **Step 1: Implement the shared Python compatibility helper**

Create `scripts/artifact_cli.py`:

```python
"""Shared command-line compatibility for canonical artifact generators."""

from __future__ import annotations

import re
import sys


def accept_legacy_date_arg(args: list[str], program: str) -> None:
    """Accept one deprecated YYYYMMDD argument without changing output paths."""
    if not args:
        return
    if len(args) == 1 and re.fullmatch(r"\d{8}", args[0]):
        print(
            f"Warning: {program}: the YYYYMMDD argument is deprecated and ignored; "
            "artifacts are written to canonical dist paths.",
            file=sys.stderr,
        )
        return
    raise SystemExit(f"Usage: {program} [YYYYMMDD]")
```

- [ ] **Step 2: Integrate the helper into PDF generation**

Import the helper in a way that supports both `python3 scripts/...py` and package imports used by pytest:

```python
if __package__:
    from .artifact_cli import accept_legacy_date_arg
else:
    from artifact_cli import accept_legacy_date_arg
```

Begin `main()` with:

```python
accept_legacy_date_arg(sys.argv[1:], "convert_manuscript_to_pdf.py")
base = "dist"
```

Do not change PDF input or output paths.

- [ ] **Step 3: Make figure generation canonical**

Remove `datetime`, use the same package/script import block from Step 2, and set:

```python
from scripts.artifact_cli import accept_legacy_date_arg

accept_legacy_date_arg(sys.argv[1:], "generate_manuscript_figures.py")
figures_dir = "dist/figures"
os.makedirs(figures_dir, exist_ok=True)
```

Update the module docstring to identify `dist/analysis_result.md` and `dist/figures/`.

- [ ] **Step 4: Canonicalize the BigQuery pipeline with deprecated `--date` support**

Change help text to `dist/analysis_result.md`. Remove `date_dir`. Replace the `--date` case with validation and a warning:

```bash
    --date)
      if [[ $# -lt 2 || ! "$2" =~ ^[0-9]{8}$ ]]; then
        echo "Usage: --date requires a legacy YYYYMMDD value." >&2
        exit 2
      fi
      echo "Warning: --date is deprecated and ignored; output is dist/analysis_result.md." >&2
      shift 2
      ;;
```

Set:

```bash
mkdir -p dist
output_file="dist/analysis_result.md"
```

- [ ] **Step 5: Run focused tests and syntax checks**

Run:

```bash
python3 -m pytest tests/test_artifact_cli_compatibility.py -q
python3 -m py_compile scripts/artifact_cli.py scripts/convert_manuscript_to_pdf.py scripts/generate_manuscript_figures.py
bash -n scripts/run_non_traumatic_sah_bigquery_pipeline.sh
```

Expected: compatibility tests pass and syntax checks print no errors.

- [ ] **Step 6: Commit command-interface changes**

```bash
git add scripts/artifact_cli.py scripts/convert_manuscript_to_pdf.py scripts/generate_manuscript_figures.py scripts/run_non_traumatic_sah_bigquery_pipeline.sh
git commit -m "Keep artifact generators canonical and backward compatible" \
  -m "Constraint: Legacy dates may warn but cannot select output directories." \
  -m "Confidence: high" \
  -m "Scope-risk: moderate" \
  -m "Tested: Focused pytest and Python/Bash syntax checks."
```

---

### Task 3: Migrate the latest analysis artifacts and remove snapshots

**Files:**
- Move from HEAD: `dist/20260711/analysis_result.md` → `dist/analysis_result.md`
- Move from HEAD: `dist/20260711/figures/` → `dist/figures/`
- Delete: tracked `dist/20260707/`
- Delete: tracked `dist/20260708/`
- Modify: `dist/manuscript_non_traumatic_sah_phenotypes.md`
- Modify: `dist/manuscript_non_traumatic_sah_phenotypes_cn.md`
- Modify: `dist/electronic_supplementary_material.md`
- Modify: `dist/readme.txt`

**Interfaces:**
- Consumes: latest aggregate artifacts stored in HEAD under `dist/20260711/`
- Produces: canonical tracked analysis, figure, manuscript, metadata, and PDF tree under `dist/`

- [ ] **Step 1: Restore only the latest deleted analysis and figures from HEAD**

```bash
git restore --source=HEAD -- dist/20260711/analysis_result.md dist/20260711/figures
```

Do not restore any 20260707 or 20260708 path.

- [ ] **Step 2: Move restored latest artifacts to canonical paths**

```bash
git mv dist/20260711/analysis_result.md dist/analysis_result.md
git mv dist/20260711/figures dist/figures
```

- [ ] **Step 3: Make Markdown image and provenance paths canonical**

Apply these exact replacements:

```diff
-](20260711/figures/
+](figures/

-dist/20260708/figures/fig1_cohort_flowchart_data.json
+dist/figures/fig1_cohort_flowchart_data.json
```

Apply the image replacement to the English manuscript, Chinese manuscript, and ESM. Apply the provenance replacement throughout ESM.

- [ ] **Step 4: Update `dist/readme.txt` inputs**

Replace dated inputs with:

```text
  - dist/analysis_result.md
  - dist/figures/*
  - dist/figures/fig1_cohort_flowchart_data.json
```

Keep the preparation date as metadata, not as a path.

- [ ] **Step 5: Verify the canonical artifact tree before committing**

Run:

```bash
test -f dist/analysis_result.md
test -d dist/figures
test ! -d dist/20260707
test ! -d dist/20260708
test ! -d dist/20260711
python3 -m pytest tests/test_manuscript_output_paths.py -q
```

Expected: all path assertions succeed and manuscript tests pass.

- [ ] **Step 6: Commit the authorized deletion and migration**

```bash
git add -A dist
git commit -m "Make dist a single canonical artifact tree" \
  -m "Constraint: Historical copies remain recoverable from Git history." \
  -m "Confidence: high" \
  -m "Scope-risk: moderate" \
  -m "Tested: Canonical tree assertions and manuscript path tests."
```

---

### Task 4: Update active guidance and enforce Git coverage

**Files:**
- Modify: `AGENTS.md:35-50`
- Modify: `scripts/prompt_for_regenerating_manuscript.md`
- Modify: `dist/electronic_supplementary_material.md`
- Modify: `tests/test_artifact_cli_compatibility.py`

**Interfaces:**
- Consumes: canonical tree and command interfaces from Tasks 2–3
- Produces: date-free active documentation and automated Git-coverage checks

- [ ] **Step 1: Update active path guidance**

Replace active `dist/YYYYMMDD` references in `AGENTS.md` and `scripts/prompt_for_regenerating_manuscript.md` with:

```text
Analysis: dist/analysis_result.md
Figures: dist/figures/
Manuscripts and metadata: dist/
PDFs: dist/pdf/
```

Update figure command examples to `python3 scripts/generate_manuscript_figures.py`. Preserve historical plan/spec documents unchanged.

- [ ] **Step 2: Add repository-tree contract tests**

Append to `tests/test_artifact_cli_compatibility.py`:

```python
import re
import subprocess


def test_active_files_have_no_dated_dist_paths() -> None:
    active_paths = [
        "AGENTS.md",
        "scripts/prompt_for_regenerating_manuscript.md",
        "scripts/run_non_traumatic_sah_bigquery_pipeline.sh",
        "scripts/generate_manuscript_figures.py",
        "dist/readme.txt",
        "dist/electronic_supplementary_material.md",
    ]
    dated_dist = re.compile(r"dist/[0-9]{8}")
    for path in active_paths:
        assert not dated_dist.search(read_text(path)), path


def test_dist_is_not_ignored_and_has_no_dated_directories() -> None:
    ignored = subprocess.run(
        ["git", "check-ignore", "-q", "dist/analysis_result.md"], cwd=ROOT
    )
    assert ignored.returncode == 1
    assert not any(re.fullmatch(r"[0-9]{8}", path.name) for path in (ROOT / "dist").iterdir())
```

- [ ] **Step 3: Run active-path tests**

Run: `python3 -m pytest tests/test_artifact_cli_compatibility.py tests/test_manuscript_output_paths.py -q`

Expected: all focused tests pass.

- [ ] **Step 4: Commit guidance and contract tests**

```bash
git add AGENTS.md scripts/prompt_for_regenerating_manuscript.md dist/electronic_supplementary_material.md tests/test_artifact_cli_compatibility.py
git commit -m "Enforce Git-managed canonical dist artifacts" \
  -m "Confidence: high" \
  -m "Scope-risk: narrow" \
  -m "Tested: Active path and Git-ignore contract tests."
```

---

### Task 5: Regenerate and audit the complete artifact tree

**Files:**
- Modify: `dist/figures/*` when deterministic regeneration changes content
- Modify: `dist/pdf/*.pdf` when deterministic regeneration changes content

**Interfaces:**
- Consumes: canonical analysis, Markdown, and generation commands
- Produces: verified Git-managed figures and PDFs without dated paths

- [ ] **Step 1: Generate figures and PDFs using no-date commands**

Run:

```bash
python3 scripts/generate_manuscript_figures.py
python3 scripts/convert_manuscript_to_pdf.py
```

Expected: figures are written to `dist/figures/` and four PDFs to `dist/pdf/`.

- [ ] **Step 2: Verify legacy compatibility without changing output paths**

Run:

```bash
python3 scripts/convert_manuscript_to_pdf.py 20260711 2>&1 | tee /tmp/legacy-pdf.log
python3 scripts/generate_manuscript_figures.py 20260711 2>&1 | tee /tmp/legacy-figures.log
rg -i "deprecated" /tmp/legacy-pdf.log /tmp/legacy-figures.log
```

Expected: both commands warn, succeed, and create no dated directory.

- [ ] **Step 3: Parse PDFs and confirm embedded figures**

Run:

```bash
python3 - <<'PY'
from pathlib import Path
from pypdf import PdfReader

pdf_dir = Path("dist/pdf")
expected = {
    "electronic_supplementary_material.pdf",
    "manuscript_non_traumatic_sah_phenotypes_cn.pdf",
    "manuscript_non_traumatic_sah_phenotypes_en.pdf",
    "strobe_checklist.pdf",
}
assert {path.name for path in pdf_dir.glob("*.pdf")} == expected
counts = {}
for path in sorted(pdf_dir.glob("*.pdf")):
    reader = PdfReader(path)
    counts[path.name] = (
        len(reader.pages),
        sum(len(page.images) for page in reader.pages),
    )
    assert counts[path.name][0] > 0
assert counts["manuscript_non_traumatic_sah_phenotypes_en.pdf"][1] >= 5
assert counts["manuscript_non_traumatic_sah_phenotypes_cn.pdf"][1] >= 5
assert counts["electronic_supplementary_material.pdf"][1] >= 7
print(counts)
PY
```

Expected: four PDFs have positive page counts; English and Chinese manuscripts have at least 5 images each; ESM has at least 7.

- [ ] **Step 4: Run full verification and Git coverage audit**

```bash
python3 -m pytest -q
python3 -m py_compile scripts/artifact_cli.py scripts/convert_manuscript_to_pdf.py scripts/generate_manuscript_figures.py
bash -n scripts/run_non_traumatic_sah_bigquery_pipeline.sh
git diff --check
test -z "$(git ls-files --others --exclude-standard dist)"
test -z "$(git ls-files dist | rg '^dist/[0-9]{8}/' || true)"
```

Expected: all tests pass, syntax checks succeed, and both Git coverage assertions are empty.

- [ ] **Step 5: Commit regenerated artifacts if changed**

```bash
git add -A dist
git diff --cached --quiet || git commit -m "Refresh canonical tracked artifacts" \
  -m "Confidence: high" \
  -m "Scope-risk: narrow" \
  -m "Tested: Full pytest, syntax, PDF, and Git coverage audits."
```
