Generation and Review Metadata
==============================

- Original analysis/manuscript source: Gemini (Gemini 3.5 Flash) / Antigravity outputs from 2026-07-11
- Citation audit, scientific-language revision, humanization, and submission-readiness review: Codex, 2026-07-16
- Purpose/Methods/Results/Conclusion reconciliation and reproducibility metadata update: Codex, 2026-07-22
- Chinese cited-manuscript alignment with the reviewed English source: Codex, 2026-07-23
- Target journal: Intensive Care Medicine, Original Paper
- Current verdict: analysis content frozen and cited English/Chinese manuscripts reconciled; submission package remains REVISE/not ready
- Governance scope of this revision: public manuscript text, aggregate results/figures, code, protocol, and SAP only; no patient-level data or restricted query was accessed

Canonical artifacts
-------------------

- manuscript_non_traumatic_sah_phenotypes_cited.md: reviewed English submission manuscript
- manuscript_non_traumatic_sah_phenotypes_cn_cited.md: Chinese reference manuscript aligned to the reviewed English source on 2026-07-23
- electronic_supplementary_material.md: ESM source
- references.bib and journal.csl: verified citation inputs
- strobe_checklist.md and record_checklist.md: reporting-guideline mappings
- manuscript_review_report.md: multidisciplinary review verdict and issue register
- submission_manifest.md: live ICM requirement and file manifest
- author_completion_checklist.md: the single list of author-only, authorized-reanalysis, and technical-production tasks
- citation_update_report.md and related CSV/log files: citation provenance and verification evidence

Important production warning
----------------------------

Files currently under dist/pdf/ were generated before the 2026-07-23 bilingual manuscript revisions and must not be submitted. Pandoc 3.10 citeproc preflight passed on the reviewed English and aligned Chinese sources with no unresolved citation keys, but final reference typography/DOI links, editable DOCX, updated manuscript/ESM PDFs, and visual inspection remain outstanding. Referenced figures were regenerated on 2026-07-16 as 600 dpi PNG plus vector PDF; use vector files where the submission system permits them.

Current manuscript preparation status
-------------------------------------

- The citation-aware English `_cited.md` file is the reviewed submission source; the Chinese cited manuscript mirrors its structure, quantitative results, citations, figure references, interpretation boundaries, declarations, and ESM description.
- Eighteen cited keys in eighteen citation clusters resolve to verified bibliography entries; no unresolved cited identity, duplicate DOI/PMID, or known retraction was found.
- The English structured abstract is 242 words, the take-home message is 53 words, and the complete Markdown source is under the 3,000-word Original Paper limit by a conservative whitespace count.
- The main manuscript contains two figures; cohort flow is ESM Fig. 6. A previously referenced severity-score figure was removed because it displayed MIMIC SOFA/SAPS II/OASIS/LODS rather than the eICU APACHE variables described in the Results.
- All referenced figures have 600 dpi PNG and vector PDF versions, and embedded figure numbers were removed to avoid conflicts with manuscript numbering.
- Non-central prediction-model results were removed from the submission manuscript because the current cross-validation has unresolved leakage and patient-grouping risk.
- Mortality findings are framed as descriptive same-hospital associations because the 0-48 h feature window may overlap the outcome; admission-origin Cox/Kaplan-Meier results are excluded from the submission manuscript.
- The MIMIC analysis unit is 1,186 ICU stays from 1,173 patients; subject-grouped bootstrap mean ARI is 0.8554.
- eICU is reported as an exploratory fixed-transport assessment (540/221/82 patients; mortality 5.4%/25.8%/42.7%), not confirmatory external validation or cluster-boundary replication.

Next authoritative action
-------------------------

Work through author_completion_checklist.md, then rerun the manuscript and reproducibility reviews. submission_manifest.md must show both upstream gates passed before the package is called submission-ready.
