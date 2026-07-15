# Canonicalize All Dist Artifacts

## Goal

Make `dist/` a fully Git-managed, date-independent artifact tree. Analysis results, figures, manuscripts, supplementary materials, metadata, and PDFs must all use stable canonical paths.

## Scope

- Remove the tracked `dist/20260707/` and `dist/20260708/` historical snapshots, matching the user-authorized working-tree deletions.
- Migrate the latest tracked `dist/20260711/analysis_result.md` and `dist/20260711/figures/` content to `dist/analysis_result.md` and `dist/figures/`.
- Keep the already canonical manuscript, ESM, STROBE, metadata, and PDF files directly under `dist/` and `dist/pdf/`.
- Remove active `dist/YYYYMMDD` behavior and documentation from the BigQuery report pipeline, figure generator, manuscript prompt, repository guidance, metadata, and scientific provenance text.
- Keep historical design and implementation-plan documents unchanged because they record previously completed workflows.

## Canonical Artifact Tree

```text
dist/
├── analysis_result.md
├── figures/
│   ├── fig1_cohort_flowchart.png
│   ├── fig1_cohort_flowchart_data.json
│   ├── fig2_primary_log_pca_heatmap.png
│   └── ...
├── manuscript_non_traumatic_sah_phenotypes.md
├── manuscript_non_traumatic_sah_phenotypes_cn.md
├── electronic_supplementary_material.md
├── strobe_checklist.md
├── readme.txt
└── pdf/
    ├── manuscript_non_traumatic_sah_phenotypes_en.pdf
    ├── manuscript_non_traumatic_sah_phenotypes_cn.pdf
    ├── electronic_supplementary_material.pdf
    └── strobe_checklist.pdf
```

No eight-digit date directory remains below `dist/`.

## Command Interfaces

Analysis report generation:

```bash
scripts/run_non_traumatic_sah_bigquery_pipeline.sh
```

The script writes `dist/analysis_result.md`. For transition safety, the legacy `--date YYYYMMDD` option is accepted, ignored, and accompanied by a deprecation warning on stderr. Repository-owned callers omit it.

Figure generation:

```bash
python3 scripts/generate_manuscript_figures.py
```

The script writes `dist/figures/`. For transition safety, exactly one legacy positional `YYYYMMDD` argument is accepted, ignored, and accompanied by a deprecation warning on stderr. Repository-owned callers omit it.

PDF generation:

```bash
python3 scripts/convert_manuscript_to_pdf.py
```

The script writes `dist/pdf/`. For transition safety, exactly one legacy positional `YYYYMMDD` argument is accepted, ignored, and accompanied by a deprecation warning on stderr. Any other positional value or more than one positional argument fails with a concise usage error. Repository-owned callers and documentation use the no-argument command.

## Figure and Provenance Paths

- Canonical Markdown image links use `figures/...` relative to `dist/`.
- `preprocess_markdown()` continues resolving local relative images to absolute `file://` URLs for WeasyPrint.
- ESM provenance references use `dist/figures/fig1_cohort_flowchart_data.json` rather than a dated snapshot.
- `dist/readme.txt` lists only canonical artifact and input paths. It may retain the preparation date as metadata, but the date is not part of a path.

## Git Management

`dist/` is already tracked and is not ignored. The implementation makes this contract explicit through regression tests rather than adding redundant negation patterns to `.gitignore`.

Completion requires:

- every existing non-ignored file under `dist/` to be tracked;
- no untracked files under `dist/`;
- no tracked paths matching `dist/[0-9]{8}/...`;
- no ignored canonical `dist` path;
- intentional deletion of obsolete historical snapshots to be included in the implementation commit.

Generated PDFs and PNG figures remain committed because the user explicitly requested Git management of `dist/`. Patient-level exports, credentials, and PHI remain prohibited.

## Error Handling

- The BigQuery pipeline continues failing on query or report-generation errors; only its output path changes.
- The figure generator continues creating its output directory when missing.
- Required English and Chinese manuscript inputs remain fail-fast in the PDF converter.
- Optional ESM and STROBE inputs remain conditional.
- The one-argument PDF compatibility path only accepts an eight-digit date, preventing arbitrary stale arguments from being silently ignored.

## Testing and Verification

- Add regression tests for canonical analysis, figure, manuscript, supplementary, and PDF paths.
- Verify date-directory variables are absent and legacy date arguments cannot change output paths.
- Verify figure and PDF commands work with no date argument.
- Verify legacy analysis, figure, and PDF date arguments warn and still target canonical paths; invalid arguments fail.
- Verify manuscript and ESM image links contain no eight-digit directory and generated PDFs contain embedded figures.
- Run the complete pytest suite and Python syntax checks.
- Run the BigQuery pipeline shell syntax check without accessing BigQuery.
- Confirm `git ls-files dist` covers every non-ignored `dist` file and contains no dated directory.
- Confirm `git status` is clean after commits.

## Risks and Mitigations

- External callers may still pass dates: compatibility shims keep all three generation commands working while clearly deprecating date arguments.
- Removing historical snapshots loses duplicate artifact copies from Git history but not from repository history; prior commits remain available.
- New generated artifacts could be forgotten: the Git-management regression test and final tracked-versus-existing audit detect that condition.
