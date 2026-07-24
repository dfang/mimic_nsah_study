# Pipeline DAG

| Stage ID | Purpose | Depends on | Command or entry point | Inputs | Outputs | Parameters/config | QC evidence |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| GOV | Governance gate | None | Manual review of `DATA_GOVERNANCE.md` | Task scope and artifact classes | Governance decision | Public-only boundary | `DATA_GOVERNANCE.md` |
| COHORT-M | Build MIMIC NSAH cohort and features | GOV | `python scripts/12_run_non_traumatic_sah_cohort_sql.py` | MIMIC-IV 3.1 authorized tables | Restricted BigQuery derived tables | GoogleSQL; 0-48 h feature contract | Not rerun in public-only review |
| ANALYSIS-M | Run MIMIC phenotyping and association analyses | COHORT-M | `python scripts/13_run_non_traumatic_sah_analysis.py` | Restricted MIMIC feature table | Restricted assignments; aggregate analysis outputs | Seed 42; PCA 3; K-means K=3, n_init=100 | Existing aggregate report; clean rerun pending |
| QC-FREEZE | Audit row grain, repeats, time contract, source metadata, and dictionaries | COHORT-M, ANALYSIS-M | `python scripts/12_run_non_traumatic_sah_cohort_sql.py --sql-file 16_freeze_release_qc.sql` | Restricted BigQuery derived tables | Aggregate QC tables and job log | No patient-level preview rows | Passed; job `79176287-6e85-4b9c-a54c-8b6da3309d81` |
| COHORT-E | Build eICU validation cohort | GOV | BigQuery execution of `14_create_eicu_external_validation_cohort.sql` | eICU-CRD 2.0 authorized tables | Restricted eICU derived tables | Frozen variable mapping | Passed 2026-07-24; job `ae05186f-1c43-4598-8e05-c2ce5ad852f0` |
| VALIDATE-E | Apply frozen transport and sensitivity analyses | ANALYSIS-M, COHORT-E | `python scripts/15_run_eicu_external_validation.py` | Private versioned MIMIC transform bundle; restricted eICU features | Restricted labels; aggregate validation outputs | Seed 42; nearest frozen centroid; 2,000 hospital-cluster bootstrap replicates; 66 leave-one-hospital-out analyses; no eICU fitting/tuning/recalibration | Passed 2026-07-24; bundle SHA-256 and job IDs in `reproducibility/eicu-validation-results.yaml` |
| REPORT | Generate aggregate analysis report | ANALYSIS-M, VALIDATE-E | `scripts/run_non_traumatic_sah_bigquery_pipeline.sh` | Authorized query outputs | `dist/analysis_result.md` | Canonical flat `dist/` layout | Output exists; no current clean rerun |
| FIGURES | Generate manuscript figures | REPORT | `python scripts/generate_manuscript_figures.py` | Aggregate frozen values; cohort-flow queries | `dist/figures/` | 600 dpi PNG plus vector PDF after current revision | Unit test and metadata inspection |
| MANUSCRIPT | Maintain manuscripts and ESM | REPORT, FIGURES | Editorial workflow | Aggregate results, citation evidence | Canonical Markdown manuscripts and ESM | ICM Original Paper limits | Citation/static checks and manuscript review |
| CITATIONS | Resolve references | MANUSCRIPT | Pandoc citeproc command in compiler skill | Markdown, BibTeX, CSL | Resolved intermediate | ICM CSL parent | Blocked: Pandoc unavailable |
| PDF | Render submission PDF | CITATIONS | Typst or Chrome path after citeproc | Resolved intermediate | Submission PDF | Journal layout | Blocked by citeproc and author placeholders |
| RELEASE | Audit public reproducibility package | All prior stages | Manual release checklist | Public code/docs and cleared aggregates | Tagged release | Exact Python lock; secret/disclosure/reproducibility checks | In progress |

## Manual stages

| Stage ID | Decision | Reviewer | Inputs | Recorded outcome |
| :--- | :--- | :--- | :--- | :--- |
| GOV | Permit authorized local eICU processing while retaining the public-release block | Codex + prior author authorization | Governance record, private-bundle controls, and aggregate-only output contract | `PROCEED_LOCAL`; public release remains blocked pending author/institution approval |
| ESTIMAND | Descriptive same-hospital association versus 48 h landmark | Authors | Protocol, SAP, review findings | Version 0.2.0 selects descriptive same-hospital association; final author approval pending |
| DISCLOSURE | Clear aggregate outputs for public release | Authors/institution | Tables, figures, manuscripts | Pending |
| MANUSCRIPT-REVIEW | Multidisciplinary submission-readiness review | Codex review passes | Manuscript package | REVISE |

## Execution order

1. GOV
2. COHORT-M and COHORT-E (authorized environment only)
3. ANALYSIS-M
4. QC-FREEZE
5. VALIDATE-E
6. REPORT
7. FIGURES and MANUSCRIPT
8. CITATIONS
9. PDF
10. RELEASE
