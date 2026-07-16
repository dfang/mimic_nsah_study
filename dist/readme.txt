Generation and Review Metadata
==============================

- Original analysis/manuscript source: Gemini (Gemini 3.5 Flash) / Antigravity outputs from 2026-07-11
- Citation audit, scientific-language revision, humanization, and submission-readiness review: Codex, 2026-07-16
- Target journal: Intensive Care Medicine, Original Paper
- Current verdict: REVISE; not frozen and not submission-ready
- Governance scope of this revision: public manuscript text, aggregate results/figures, code, protocol, and SAP only; no patient-level data or restricted query was accessed

Canonical artifacts
-------------------

- manuscript_non_traumatic_sah_phenotypes.md: canonical English manuscript
- manuscript_non_traumatic_sah_phenotypes_cn.md: synchronized Chinese reference manuscript
- electronic_supplementary_material.md: ESM source
- references.bib and journal.csl: verified citation inputs
- strobe_checklist.md and record_checklist.md: reporting-guideline mappings
- manuscript_review_report.md: multidisciplinary review verdict and issue register
- submission_manifest.md: live ICM requirement and file manifest
- author_completion_checklist.md: the single list of author-only, authorized-reanalysis, and technical-production tasks
- citation_update_report.md and related CSV/log files: citation provenance and verification evidence

Important production warning
----------------------------

Files currently under dist/pdf/ were generated before the 2026-07-16 manuscript revisions and must not be submitted. Pandoc/citeproc was unavailable in this environment, so numeric citation rendering, reference typography, DOI links, editable DOCX, and updated manuscript/ESM PDFs remain unverified. Referenced figures were regenerated on 2026-07-16 as 600 dpi PNG plus vector PDF; use vector files where the submission system permits them.

Current manuscript preparation status
-------------------------------------

- Citation-aware text has been promoted to the canonical English and Chinese filenames; _cited.md files are synchronized traceability copies.
- Eighteen cited keys in eighteen citation clusters resolve to verified bibliography entries; no unresolved cited identity, duplicate DOI/PMID, or known retraction was found.
- The English structured abstract is 242 words, the take-home message is 63 words, and the main file is approximately 2,060 words including declarations and captions.
- The main manuscript contains three figures; cohort flow is ESM Fig. 8.
- All referenced figures have 600 dpi PNG and vector PDF versions, and embedded figure numbers were removed to avoid conflicts with manuscript numbering.
- Non-central prediction-model results were removed from the submission manuscript because the current cross-validation has unresolved leakage and patient-grouping risk.
- Mortality findings are framed as descriptive same-hospital associations because the 0-48 h feature window may overlap the outcome.

Next authoritative action
-------------------------

Work through author_completion_checklist.md, then rerun the manuscript and reproducibility reviews. submission_manifest.md must show both upstream gates passed before the package is called submission-ready.
