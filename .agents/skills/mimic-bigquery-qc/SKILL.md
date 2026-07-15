---
name: mimic-bigquery-qc
description: Quality-control and review BigQuery SQL for MIMIC research. Use for schema/version verification, dry runs, row-count and duplicate-key audits, join cardinality, row-grain review, time-window logic, leakage, timestamp types, costly event queries, provenance, final-table review, or pre-publication SQL validation.
---

# MIMIC BigQuery QC

Review correctness, cost, and reproducibility. Do not treat formatting as validation.

## Governance preflight

Apply `mimic-data-governance` before inspecting restricted query outputs. Keep patient-level results in an approved local or controlled environment; review SQL text and non-sensitive schemas without exporting underlying rows.

## Verify data assets

- Record the core MIMIC-IV version and the exact hosp/icu schemas visible to the user.
- Discover the derived schema visible to the user. Accept verified versioned schemas such as `physionet-data.mimiciv_3_1_derived` and aliases such as `physionet-data.mimiciv_derived`; never rewrite a user-verified schema solely from a remembered convention.
- Check `INFORMATION_SCHEMA.TABLES` for `_metadata` before querying it. When present, record the MIMIC version, mimic-code version, and commit hash; when absent, do not emit a guaranteed-to-fail `_metadata` query—record the table-existence result and equivalent known build/source evidence instead.
- Treat Note, ED, and CXR as separately released modules. Record their versions and linkage coverage rather than calling all modules “3.1.”
- Verify table existence with metadata or a dry run before approving generated SQL.
- Read `../../docs/data-compatibility.md` when working from this source repository. In installed copies, verify the same facts from official sources.
- Quote complete BigQuery table names with backticks.
- Resolve the output project/dataset from the active study configuration; otherwise use `<PROJECT_ID>.<DATASET>`.

## Check row grain and joins

State the intended key before reviewing. After each major join, compare:

- row count;
- distinct `subject_id`, `hadm_id`, and `stay_id` where applicable;
- duplicate count at the target key;
- unmatched rows on each side;
- maximum multiplicity per key.

Aggregate event-level tables before joining to a one-row-per-unit table unless the output is intentionally long. Flag `SELECT DISTINCT` used to hide a faulty join.

## Check the time contract

Map every timestamp filter to the canonical named study times: `eligibility_time`, `cohort_entry_time`, `index_time`, `prediction_landmark`, `treatment_assignment_time`, `exposure_end`, `followup_start`, `censoring_time`, and `outcome_time`. Check half-open boundaries and timezone/type conversions.

Do not approve:

- post-landmark predictors;
- future treatment used as a baseline group;
- outcomes inside feature or exposure windows;
- a `0-24h` feature model with an ICU-entry prediction time;
- real-calendar comparisons across independently date-shifted patients.

## Control cost

- Prefer validated derived concepts when they match the study definition.
- Filter `chartevents` and other event tables by cohort keys, `itemid`, and time as early as possible.
- Select required columns instead of `SELECT *`.
- Use a dry run and report bytes processed for expensive queries.
- Test candidate itemids with small audit queries before full extraction.

## Review the final table

- Require a unique intended key or an explicitly documented repeated-measure structure.
- Preserve concept, source table, unit, summary, and time-window provenance.
- Audit plausible ranges, units, missingness, and measurement counts.
- Keep outcomes and post-treatment variables out of baseline/prediction inputs.
- Check `anchor_age`/`anchor_year` handling and age-top-coding implications.
- Produce a column dictionary; do not approve unnamed or ambiguous features.

## Return evidence

Return an issue register with severity, query location, evidence, impact, correction, and verification query. Include:

- verified schemas and derived `_metadata` or equivalent version evidence;
- dry-run/syntax result;
- row-count and uniqueness checkpoints;
- temporal leakage findings;
- cost findings;
- limitations that remain `not assessed` because execution access is unavailable.
