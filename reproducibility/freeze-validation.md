# Analysis Freeze Validation

**Study:** MIMIC-NSAH-PHENO-01

**Freeze date:** 2026-07-16

**Status:** `FROZEN_EXPLORATORY`
**Run ID:** `MIMIC-NSAH-PHENO-01-freeze-20260716`

## Authorized execution

- The authorized user confirmed MIMIC-IV/eICU access on 2026-07-16.
- Restricted processing ran locally through the user's BigQuery credentials.
- Only aggregate QC/results and non-sensitive job provenance were persisted in the repository.
- MIMIC-IV source release: 3.1; eICU-CRD source release: 2.0.
- Main cohort job: `d7eab218-46dd-48c2-9388-df9a7a993a1c`.
- Freeze QC job: `79176287-6e85-4b9c-a54c-8b6da3309d81`.
- Final MIMIC result-read job: `9446e34c-7986-4dc4-8346-7a0aa7e1e36d`.
- Authorized eICU frozen-transport rerun cohort job: `ae05186f-1c43-4598-8e05-c2ce5ad852f0`.
- Frozen transform bundle SHA-256: `63042d68a74643da9c902e4d1f6cd9d774e77d55b5f6e1269851bceb3371dd41` (private `DERIVED_SENSITIVE` artifact; parameters not committed).
- eICU feature-read job: `57f3f6f0-fe67-403c-bbfd-9571b0d031b1`; detailed write-job provenance is in `reproducibility/eicu-validation-results.yaml`.

## Cohort and grain QC

| Check | Aggregate result |
| :--- | ---: |
| Eligible ICU stays before primary exclusions | 1,212 |
| Distinct admissions/stays | 1,212 / 1,212 |
| Duplicate stay rows | 0 |
| Invalid feature-window rows | 0 |
| Primary analysis stays | 1,186 |
| Primary unique subjects | 1,173 |
| Repeated-subject admission rows | 13 |
| ICU LOS >=48 h sensitivity | 1,005 |
| No recorded RBC 0-48 h sensitivity | 1,162 |
| Death before nominal 48 h window end | 66 |
| Discharge before nominal 48 h window end | 91 |

The retained repeat structure is intentional. Bootstrap and cross-validation use `subject_id` groups.

## Frozen analytical results

- Primary phenotype sizes: P1 694, P2 384, P3 108.
- Hospital mortality: 6.34%, 32.55%, and 61.11%, respectively.
- Adjusted mortality ORs: P2 vs P1 7.59 (95% CI 5.07-11.36); P3 vs P1 21.21 (12.08-37.26).
- Early anemia adjusted OR: 0.99 (0.68-1.44).
- Subject-grouped, full-pipeline bootstrap: 200 iterations; mean ARI 0.8554; median ARI 0.8656; mean OOB ARI 0.8578; minimum cluster size across iterations 51.
- LOS >=48 h sensitivity: sizes 587/325/93; subset ARI 0.8604.
- No-RBC sensitivity: sizes 675/374/113; subset ARI 0.9268.
- Include-massive-transfusion sensitivity: no additionally eligible cases; assignments identical (ARI 1.0000).
- Authorized eICU frozen-transport rerun on 2026-07-24: sizes 539/222/82; hospital mortality 5.38%/25.68%/42.68%.
- eICU hospital-level robustness: 2,000 hospital-cluster bootstrap replicates; P2-P1 risk difference 20.30 percentage points (95% percentile interval 15.06-25.83), P3-P1 37.30 (26.99-47.37); mortality ordering retained in 66/66 leave-one-hospital-out analyses.
- eICU de novo K=3 showed negligible assignment concordance with transport (ARI -0.0017), retained as a limitation rather than evidence of replication.

## Disclosure review

- No patient-level rows, identifiers, timestamps, model assignments, or restricted query caches are committed.
- Primary and sensitivity phenotype cells reviewed: 36 cells, none below 10; minimum reviewed phenotype cell was 58.
- Non-zero public table/figure cells below 10 are rendered as `<10`; adjacent cohort-flow transitions below 10 are suppressed in the public JSON/ESM.
- Patient-level assignments and exact transform parameters remain only in the authorized environment; approved aggregate results and hashes are recorded in the public reproducibility contract.
- This local conservative review supports analysis freezing. Author/institutional disclosure approval remains required before public journal submission.

## Interpretation boundary

This is a retrospective, post-outcome-access exploratory freeze. It is not prospective preregistration, not a 48-hour landmark prediction study, and not a causal analysis. Submission readiness remains separately blocked by author, ethics, declaration, editable-source, and final-render requirements.
