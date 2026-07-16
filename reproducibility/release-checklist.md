# Reproducibility Release Audit

**Release ID:** MIMIC-NSAH-PHENO-01-freeze-20260716

**Status:** `FROZEN_EXPLORATORY`
**Reproducibility level achieved:** Computational/statistical analysis freeze in an authorized environment; restricted source access is required to rerun.

## Source and environment

- [x] MIMIC-IV 3.1 and eICU-CRD 2.0 are explicit.
- [x] Source access date and key BigQuery job provenance are recorded.
- [x] Derived concepts are tied to the PhysioNet MIMIC-IV 3.1 release; no separate local MIMIC-Code checkout was used.
- [x] The annotated freeze tag is the immutable repository entry point.
- [x] Python dependencies are exactly locked with distribution hashes.
- [x] GoogleSQL and local tool versions are recorded.
- [x] Credentials and environment-variable values are excluded.

## Determinism and execution

- [x] Random seeds and subject-grouping rules are registered.
- [x] Pipeline stages map the reported result path.
- [x] Repository tests, syntax checks and freeze guardrails pass in the locked Python 3.12 environment.
- [x] Authorized MIMIC and eICU end-to-end reruns completed.
- [x] SQL dry-run, row-grain, duplicate-key and time-window QC passed.
- [x] Regenerated aggregate results were reconciled with manuscripts, ESM and figures.

## Provenance

- [x] Principal SQL, Python, manuscript and reference files have final hashes.
- [x] Manuscript components map to DAG stages.
- [x] Twelve figure pairs were regenerated from frozen aggregate tables as 600 dpi PNG/vector PDF and visually reviewed.
- [x] Artifact provenance records generating run IDs and hashes.
- [x] Freeze commit/tag and clean-worktree assertion are recorded.

## Data governance

- [x] Public code and restricted data boundaries are documented.
- [x] No patient-level rows, credentials, timestamps, assignments or restricted caches are included.
- [x] Secret/path scan is required in final verification.
- [x] Local aggregate disclosure review is recorded.
- [x] Non-zero public cells below 10 and adjacent small cohort transitions are suppressed.
- [x] Derived patient-level/model artifacts remain restricted.
- [x] Users must obtain their own authorized data access.

## Freeze verdict

The analysis is frozen as retrospective and exploratory. Changes to cohort logic, preprocessing, outcomes, models, reported values, or interpretation require a new version and deviation entry. This verdict does not mean submission-ready: author/ethics/declaration metadata, final institutional disclosure approval, editable source and final rendered documents remain open under REV-007.
