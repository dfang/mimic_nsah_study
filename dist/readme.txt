Generation Metadata
===================

- Current manuscript preparation model: Gemini (Gemini 3.5 Flash)
- Original analysis/manuscript source: Gemini (Gemini 3.5 Flash) / Antigravity outputs from 2026-07-11
- Current preparation date: 2026-07-11
- Target journal style: Intensive Care Medicine Original Paper
- Input files used:
  - dist/analysis_result.md
  - dist/figures/*
  - dist/figures/fig1_cohort_flowchart_data.json
  - dist/manuscript_non_traumatic_sah_phenotypes.md
  - BigQuery validation tables under mimic-study-498508.non_traumatic_sah_study

This directory contains the generated analysis results, figures, ICM-style main manuscripts, and electronic supplementary material for the non-traumatic subarachnoid hemorrhage study.

Generated artifacts:
- dist/manuscript_non_traumatic_sah_phenotypes.md (ICM-style English main manuscript)
- dist/manuscript_non_traumatic_sah_phenotypes_cn.md (Chinese reference version)
- dist/electronic_supplementary_material.md (Electronic Supplementary Material)
- dist/strobe_checklist.md (STROBE checklist)
- dist/pdf/manuscript_non_traumatic_sah_phenotypes_en.pdf (English main manuscript PDF)
- dist/pdf/manuscript_non_traumatic_sah_phenotypes_cn.pdf (Chinese reference PDF)
- dist/pdf/electronic_supplementary_material.pdf (ESM PDF)
- dist/pdf/strobe_checklist.pdf (STROBE checklist PDF)

Remaining author-completion items before journal submission:
- Confirm local ethics/IRB wording.
- Complete funding, conflicts of interest, author contributions, and acknowledgements.
- Verify final reference metadata using a reference manager.
- Confirm code repository or supplementary-code release plan.

Codex citation-update provenance (2026-07-16)
================================================

- Update model: Codex
- Scope: targeted citation update and final static audit; not a systematic review
- Target journal: Intensive Care Medicine Original Paper
- Source manuscripts (preserved, not overwritten):
  - dist/manuscript_non_traumatic_sah_phenotypes.md
  - dist/manuscript_non_traumatic_sah_phenotypes_cn.md
- Citation-update artifacts:
  - dist/manuscript_non_traumatic_sah_phenotypes_cited.md
  - dist/manuscript_non_traumatic_sah_phenotypes_cn_cited.md
  - dist/references.bib
  - dist/journal.csl
  - dist/citation_key_map.csv
  - dist/citation_claim_audit.csv
  - dist/literature_search_log.md
  - dist/literature_evidence_table.csv
  - dist/citation_verification.csv
  - dist/citation_update_report.md
- Verification limitation: static citation, bibliography, CSL, bilingual, YAML, hash, and research-number checks passed; Pandoc/citeproc and BibTeX parser executables/modules were unavailable, so actual rendering was not run.
- Review gate: mimic-review/journal-reviewer has not yet been performed; the package is not frozen or submission-ready.
