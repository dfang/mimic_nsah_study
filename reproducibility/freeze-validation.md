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
- eICU cohort job: `b8ddf1a3-1e1e-49f0-a8ee-6155d536ea82`.
- Final eICU result-read jobs: `eb4587a6-8536-487f-aa5b-4463a93f0aac`, `5d29dcb5-4f4c-46d3-bd38-ad926d94bf94`.

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
- eICU frozen transport: sizes 540/221/82; hospital mortality 5.37%/25.79%/42.68%.
- eICU de novo K=3 showed low assignment concordance with transport (ARI 0.0005), retained as a limitation rather than evidence of replication.

## Disclosure review

- No patient-level rows, identifiers, timestamps, model assignments, or restricted query caches are committed.
- Primary and sensitivity phenotype cells reviewed: 36 cells, none below 10; minimum reviewed phenotype cell was 58.
- Non-zero public table/figure cells below 10 are rendered as `<10`; adjacent cohort-flow transitions below 10 are suppressed in the public JSON/ESM.
- Exact aggregate values remain only in the authorized BigQuery environment.
- This local conservative review supports analysis freezing. Author/institutional disclosure approval remains required before public journal submission.

## Interpretation boundary

This is a retrospective, post-outcome-access exploratory freeze. It is not prospective preregistration, not a 48-hour landmark prediction study, and not a causal analysis. Submission readiness remains separately blocked by author, ethics, declaration, editable-source, and final-render requirements.
