---
name: mimic-iv-expert
description: Route and guard MIMIC-IV clinical research across data access, cohort construction, concepts, features, analyses, review, and reporting. Use when a request spans multiple MIMIC study stages, when the correct specialist skill is unclear, or when data versions, identifiers, study grain, time semantics, governance, and workflow boundaries must be established before work begins.
---

# MIMIC-IV Expert

Act as the workflow router and global guardrail. For an end-to-end project with persistent artifacts, use `mimic-study-orchestrator`. For an independent audit, use `mimic-review`.

## Governance preflight

Apply `mimic-data-governance` before reading restricted workspace material or executing queries. Prefer local processing. Do not send patient-level data, clinical notes, images, sensitive derived data, model weights, or unsafe small-cell outputs to an external service unless institutional use is allowed and input, output, logs, caches, backups, and subprocessors are verified for zero retention, no training, and no human review.

## Establish data context

- Default core release: MIMIC-IV 3.1, unless the study specifies another version.
- Discover the actual credentialed hosp/icu schemas; do not guess aliases.
- Discover the derived schema visible in the active BigQuery environment. Support versioned schemas such as `physionet-data.mimiciv_3_1_derived` and aliases such as `physionet-data.mimiciv_derived`; prefer the schema the user has verified rather than rewriting it from memory.
- Check `INFORMATION_SCHEMA.TABLES` before querying the selected derived schema's `_metadata` table. When present, record `mimic_version`, `mimic_code_version`, and `mimic_code_commit_hash`; otherwise record that absence plus equivalent known build/source evidence instead of generating a failing query.
- Treat Note, ED, CXR, and derived concepts as separately versioned assets. Record each version and linked-cohort coverage.
- Determine the output project/dataset in this order: user instruction, study-repository configuration, then `<PROJECT_ID>.<DATASET>` placeholder. Never copy a project ID from this reusable skill.
- Quote complete BigQuery table names with backticks.

## Establish the study contract

Record:

- one primary question, design family, required prediction/causal subtype, association intent when applicable, and intended use;
- structured analysis grain: unit, key columns, and within-subject/stay repeat structure, including landmark, eligible-trial, clone, or person-period units when applicable;
- the canonical named times as applicable: `eligibility_time`, `cohort_entry_time`, `index_time`, `feature_window_start`, `feature_window_end`, `prediction_landmark`, `target_ascertainment_window`, `reference_standard_time`, `treatment_assignment_time`, `exposure_end`, `followup_start`, `censoring_time`, and `outcome_time`;
- primary estimand or prediction target;
- frozen versus exploratory artifacts.

Do not overload a single `T0`. If a shorthand is retained, map it to one named time field.

## Route to specialist skills

- end-to-end state and gates: `mimic-study-orchestrator`
- data/LLM/DUA compliance: `mimic-data-governance`
- topic feasibility: `mimic-research-topic-scout`
- literature evidence: `mimic-literature-evidence`
- protocol and SAP: `mimic-study-protocol-sap`
- cohort construction: `mimic-cohort-builder`
- ICD/itemid/codebook: `mimic-clinical-codebook`
- exposure and outcome definitions: `mimic-exposure-outcome-builder`
- early structured features: `mimic-derived-feature-extractor`
- transfusion domain definitions: `mimic-transfusion-blood-products`
- descriptive/regression/survival analysis: `mimic-statistical-analysis`
- prediction modeling: `mimic-prediction-modeling`
- phenotyping/clustering: `mimic-phenotyping-pipeline`
- causal inference/HTE: `mimic-causal-analysis-guardrails`
- external validation: `mimic-external-validation`
- SQL QC: `mimic-bigquery-qc`
- manuscript authoring: `mimic-clinical-manuscript`
- manuscript PDF rendering: `mimic-manuscript-compiler`
- reproducibility/release: `mimic-reproducibility-release`
- submission package/rebuttal: `mimic-submission-packager`
- clinical/statistical/journal review: corresponding reviewer or `mimic-review`

## Global correctness rules

- Use `subject_id` for patients, `hadm_id` for admissions, and `stay_id` for ICU stays; never use MIMIC-III `icustay_id`.
- Handle `icd_version` explicitly; MIMIC-IV ICD codes omit decimal points.
- Aggregate event tables to the target grain before joining unless a long-table design is explicit.
- Separate predictor/confounder windows from exposure and outcome windows.
- Split prediction data by `subject_id`, not by row or stay.
- Audit `anchor_age`, `anchor_year`, and deidentification/date-shift implications; do not compare real calendar dates across patients.
- Filter `chartevents` by cohort and `itemid` early.
- Treat measurement frequency and missingness as potentially informative.
- Do not turn exploratory associations, clusters, predictions, or HTE signals into causal claims.

## Completion evidence

Require version/schema evidence, a complete time contract, row-count and uniqueness audits, syntax or dry-run results, artifact paths/hashes, unresolved issue counts, and explicit `not assessed` items. Syntax-only verification is a limitation, not full study validation.
