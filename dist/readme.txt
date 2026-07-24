Generation and Review Metadata
==============================

- Original analysis/manuscript source: Gemini (Gemini 3.5 Flash) / Antigravity outputs from 2026-07-11
- Citation audit, scientific-language revision, humanization, and submission-readiness review: Codex, 2026-07-16
- Purpose/Methods/Results/Conclusion reconciliation and reproducibility metadata update: Codex, 2026-07-22
- Chinese cited-manuscript alignment with the reviewed English source: Codex, 2026-07-23
- Target journal: Intensive Care Medicine, Original Paper
- Current verdict: remediation completed for repository-local blocking/major defects; manuscript review is pending independent rereview and submission remains not ready
- Governance scope of this revision: authorized local eICU processing plus public code/documentation and aggregate-reviewed outputs; no patient-level or hospital-identified result was printed, exported, or committed

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

Files under dist/pdf/ were built on 2026-07-24 using Pandoc 3.10 citeproc and WeasyPrint 69.0, but the Markdown sources changed after the authorized eICU rerun and the PDFs must be regenerated before use. They remain non-submission artifacts while author metadata, declarations, institutional aggregate-disclosure approval, editable DOCX, and independent post-rerun review are open. See pdf/generation-manifest.yaml.

Current manuscript preparation status
-------------------------------------

- The citation-aware English `_cited.md` file is the reviewed submission source; the Chinese cited manuscript mirrors its structure, quantitative results, citations, figure references, interpretation boundaries, declarations, and ESM description.
- Eighteen cited keys in eighteen citation clusters resolve to verified bibliography entries; no unresolved cited identity, duplicate DOI/PMID, or known retraction was found.
- The English structured abstract is 250 words, the take-home message is 60 words, and the main text remains under the 3,000-word Original Paper limit.
- The main manuscript contains two figures; cohort flow is ESM Fig. 6. A previously referenced severity-score figure was removed because it displayed MIMIC SOFA/SAPS II/OASIS/LODS rather than the eICU APACHE variables described in the Results.
- All referenced figures have 600 dpi PNG and vector PDF versions, and embedded figure numbers were removed to avoid conflicts with manuscript numbering.
- Non-central prediction-model results were removed from the submission manuscript because the current cross-validation has unresolved leakage and patient-grouping risk.
- Mortality findings are framed as descriptive same-hospital associations because the 0-48 h feature window may overlap the outcome; admission-origin Cox/Kaplan-Meier results are excluded from the submission manuscript.
- The MIMIC analysis unit is 1,186 ICU stays from 1,173 patients; subject-grouped bootstrap mean ARI is 0.8554.
- The authorized 2026-07-24 eICU pure frozen evaluation assigned 539/222/82 patients, with mortality 5.4%/25.7%/42.7%. The derived-sensitive transform bundle remains private; its SHA-256 hash, source identifiers, and BigQuery job provenance are recorded.
- Hospital-level robustness used 2,000 hospital-cluster bootstrap replicates and 66 leave-one-hospital-out analyses; both higher-risk-group contrasts remained separated and the mortality order was retained in 66/66 omissions.

Next authoritative action
-------------------------

Work through author_completion_checklist.md, complete institutional approval and post-rerun rendering, then rerun the independent manuscript and reproducibility reviews. submission_manifest.md must show both upstream gates passed before the package is called submission-ready.
