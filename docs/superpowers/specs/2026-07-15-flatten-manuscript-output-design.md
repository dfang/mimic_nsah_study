# Flatten Manuscript Output Paths

## Goal

Make `dist/` the stable canonical location for manuscript deliverables. Manuscript generation must no longer create or require a `YYYYMMDD` directory.

## Scope

- Move the latest English and Chinese manuscripts, electronic supplementary material, STROBE checklist, generation metadata, and their PDFs from `dist/20260711/` to `dist/` and `dist/pdf/`.
- Change `scripts/convert_manuscript_to_pdf.py` to read manuscript Markdown from `dist/` and write PDFs to `dist/pdf/` without a date argument.
- Update the active manuscript-generation instructions and repository conventions to use the stable paths.
- Keep dated analysis results and figures unchanged. `scripts/run_non_traumatic_sah_bigquery_pipeline.sh` and `scripts/generate_manuscript_figures.py` retain their `YYYYMMDD` behavior.
- Preserve older dated manuscript directories as historical snapshots. After migration, remove only the migrated manuscript deliverables from `dist/20260711/`; keep its dated analysis outputs and figures.

## Canonical Paths

Inputs:

- `dist/manuscript_non_traumatic_sah_phenotypes.md`
- `dist/manuscript_non_traumatic_sah_phenotypes_cn.md`
- `dist/electronic_supplementary_material.md`
- `dist/strobe_checklist.md`
- `dist/readme.txt`

Outputs:

- `dist/pdf/manuscript_non_traumatic_sah_phenotypes_en.pdf`
- `dist/pdf/manuscript_non_traumatic_sah_phenotypes_cn.pdf`
- `dist/pdf/electronic_supplementary_material.pdf`
- `dist/pdf/strobe_checklist.pdf`

## Interface and Data Flow

Run PDF generation as:

```bash
python3 scripts/convert_manuscript_to_pdf.py
```

The script uses `dist/` as its fixed base directory. The English and Chinese manuscripts remain required inputs. ESM and STROBE remain optional and are generated when their Markdown sources exist. Existing macOS WeasyPrint library-path setup remains unchanged.

The manuscript may continue to cite dated analysis and figure sources because those are reproducibility inputs, not canonical manuscript output paths.

## Error Handling

Retain the current fail-fast behavior for missing required manuscript files. Continue skipping optional ESM and STROBE inputs when absent. Do not add compatibility handling for the old positional date argument; callers must use the new unambiguous command.

## Documentation Changes

- Replace the blanket `dist/YYYYMMDD` requirement in `AGENTS.md` with separate rules: manuscript deliverables use stable `dist/` paths, while analysis snapshots may remain dated.
- Update `scripts/prompt_for_regenerating_manuscript.md` so manuscript, ESM, STROBE, metadata, and PDF references point to `dist/`; retain dated references for `analysis_result.md` and figures.
- Update the migrated `dist/readme.txt` artifact list to reflect canonical paths while retaining the dated analysis-source references.
- Leave the historical 2026-07-07 implementation plan unchanged because it records a completed historical workflow.

## Verification

- Compile the converter with `python3 -m py_compile`.
- Run `python3 scripts/convert_manuscript_to_pdf.py` without arguments.
- Parse all four PDFs and verify they contain pages.
- Confirm canonical manuscript deliverables exist directly under `dist/` and `dist/pdf/`.
- Confirm migrated manuscript deliverables no longer remain under `dist/20260711/`.
- Confirm dated analysis results and figures remain in place.
- Search active instructions and scripts for stale manuscript-specific `dist/YYYYMMDD` paths.
- Run `git diff --check`.

## Risks

- External callers that still pass a date argument will need to remove it.
- Moving tracked generated PDFs can produce a large rename diff, but content should remain functionally unchanged after regeneration.
- Dated references inside manuscript scientific content must not be replaced when they identify the provenance of analysis inputs.
