# eICU External Validation Plan and Results

> **Execution status, 2026-07-24:** An authorized analyst exported a versioned,
> access-controlled `DERIVED_SENSITIVE` MIMIC transform bundle and executed the
> fail-closed eICU path without fitting, tuning, or recalibration on eICU. The current
> 539/222/82 results supersede the historical 540/221/82 aggregate. The private bundle
> is not published, but its SHA-256 hash, source commit/run ID, and BigQuery job
> provenance are recorded in `reproducibility/eicu-validation-results.yaml`.

## Purpose

This document records the eICU external validation for the MIMIC-IV non-traumatic SAH physiological phenotype study:

- what was validated;
- why the validation was designed this way;
- how the eICU cohort and variables were built;
- what was improved after the initial validation pass;
- what the current external validation results show;
- which parts succeeded, which did not, and what still needs improvement.

The reproducible code is:

- `14_create_eicu_external_validation_cohort.sql`
- `scripts/15_run_eicu_external_validation.py`

The BigQuery target dataset is:

- `mimic-study-498508.eicu_sah_validation`

## Why This Validation Strategy

The primary evaluation uses **frozen assignment transport**, not eICU de novo clustering. The 2026-07-24 execution loaded a privately hashed immutable transform artifact and satisfies that computational contract.

In a transport validation, the MIMIC-IV phenotype model is treated as the development model. The preprocessing rules, imputation medians, transformations, scaling, PCA projection, and phenotype centroids are fixed from MIMIC-IV and then applied directly to eICU. This tests whether a new patient or a new external cohort can be assigned to the MIMIC-derived phenotypes without refitting the model on the validation data.

This is the clinically relevant validation target. If the model were used prospectively, a clinician would not recluster the entire local database each time a new patient arrived. The patient would be projected into a fixed classifier.

De novo clustering in eICU is still useful, but only as a **structural sensitivity analysis**. It asks whether similar physiological groupings emerge when eICU is allowed to define its own cluster boundaries. It does not replace transport validation, because it uses the validation distribution to refit the phenotype geometry.

## Validation Design

### Intended Primary Analysis: Frozen Transport Contract

The transform was exported from the authorized MIMIC derivation run into an access-controlled artifact conforming to `reproducibility/frozen-transform-bundle.schema.json`.

Frozen components:

- MIMIC median imputation;
- `log1p` transformation for creatinine and INR;
- MIMIC StandardScaler mean and SD;
- MIMIC PCA eigenvectors;
- MIMIC phenotype centroids in 3-PC space;
- ordered phenotype labels P1, P2, and P3.

The current evaluation entry point loads those prebuilt parameters and assigns eICU patients to the nearest MIMIC phenotype centroid; it no longer reads MIMIC rows or fits preprocessing during evaluation.

### Sensitivity Robustness

The improved validation adds prespecified sensitivity analyses that address the main reviewer-facing weaknesses:

- ICU LOS >=48h sensitivity, to reduce concern that a 48-hour feature window is partly unavailable in shorter stays;
- no recorded RBC sensitivity, because eICU transfusion units are heterogeneous and should not be used as a hard primary exclusion;
- strict SAH sensitivity, requiring SAH evidence from diagnosis ICD/text rather than admissionDx-only evidence;
- low-missing and complete-case sensitivity, to test dependence on imputation;
- INR-free transport sensitivity, because INR is the most missing eICU core feature;
- Hb-free anemia sensitivity, because Hb is part of the primary phenotype and anemia adjustment would otherwise be partly circular.
- a 2,000-replicate hospital-cluster bootstrap and leave-one-hospital-out analysis, to assess multicenter dependence and single-hospital influence.

### External Criterion Validation With APACHE

The improved validation also tests whether transported phenotype order aligns with independent eICU severity measures:

- acute physiology score;
- APACHE score;
- predicted ICU mortality;
- predicted hospital mortality.

This is not part of the phenotype classifier. It is an external severity anchor.

### De Novo eICU K=3

The eICU cohort is independently imputed, scaled, projected with PCA, and clustered with K-means K=3. These eICU-native labels are compared with frozen transport labels using adjusted Rand index, normalized mutual information, same ordered label rate, silhouette score, and mortality gradient.

This analysis assesses structural reproducibility, not primary external validity.

## eICU Cohort Definition

The eICU validation cohort is built from `physionet-data.eicu_crd`.

Inclusion:

- adult patients;
- SAH evidence from eICU `diagnosis` text, ICD-9 code 430, or `apacheadmissiondx`;
- first ICU stay per `uniquepid`;
- ICU length of stay at least 24 hours;
- non-traumatic SAH after excluding trauma/head injury/traumatic diagnosis text;
- no requirement for aneurysm procedure evidence.

Primary feature eligibility:

- eight core features;
- no more than two missing core features.

Massive transfusion is not a hard eICU exclusion because eICU transfusion units are heterogeneous across `infusiondrug` and `intakeoutput`. Recorded RBC exposure is retained for description and sensitivity analysis.

## eICU Feature Mapping

The current eICU extraction uses the same eight core domains as the MIMIC primary model:

| Domain | eICU variable | Source |
| --- | --- | --- |
| Anemia | `hb_min_48h_all` | `lab`, Hgb/hemoglobin |
| Neurologic | `gcs_motor_min_48h` | `nursecharting`, fallback `apacheapsvar.motor` |
| Circulation | `map_min_48h` | `vitalperiodic` and `vitalaperiodic` |
| Circulation | `shock_index_max_48h` | HR matched to nearest periodic/aperiodic SBP within 15 minutes |
| Oxygenation | `spo2_min_48h` | `vitalperiodic.sao2` |
| Renal | `creatinine_max_48h` | `lab.creatinine` |
| Coagulation | `inr_max_48h` | `lab`, `pt - inr` |
| Platelet | `platelet_min_48h` | `lab`, `platelets x 1000` |

All variables use the ICU admission to 48-hour window and clinical range filters.

## Current External Validation Results

These results were regenerated on July 24, 2026 by running the cohort SQL and then supplying the private transform bundle to the fail-closed evaluator:

```bash
bq query --use_legacy_sql=false --project_id=mimic-study-498508 --location=US < 14_create_eicu_external_validation_cohort.sql
python scripts/15_run_eicu_external_validation.py --frozen-transform-bundle <authorized-private-bundle>
```

### Cohort Flow

| Step | Unit stays | Patients | Definition |
| --- | ---: | ---: | --- |
| 01 | 2,880 | 2,571 | SAH evidence from diagnosis/admissionDx |
| 02 | 2,863 | 2,554 | age >=18 |
| 03 | 1,314 | 1,158 | exclude traumatic SAH flags |
| 04 | 1,153 | 1,153 | first ICU stay per uniquepid |
| 05 | 903 | 903 | ICU LOS >=24h |
| 06 | 843 | 843 | eight core features with <=2 missing |
| 07 | 626 | 626 | validation + ICU LOS >=48h sensitivity |
| 08 | 819 | 819 | validation + no recorded RBC 0-48h sensitivity |
| 09 | 605 | 605 | strict SAH sensitivity |
| 10 | 819 | 819 | <=1 missing core feature sensitivity |
| 11 | 428 | 428 | complete-case sensitivity |

### Feature Missingness

The improved shock index extraction reduced shock index missingness from 44.3% in the initial implementation to 1.1%.

| Feature | Total N | Missing N | Missing Rate |
| --- | ---: | ---: | ---: |
| `inr_max_48h` | 903 | 446 | 49.4% |
| `platelet_min_48h` | 903 | 75 | 8.3% |
| `hb_min_48h_all` | 903 | 64 | 7.1% |
| `creatinine_max_48h` | 903 | 31 | 3.4% |
| `shock_index_max_48h` | 903 | 10 | 1.1% |
| `map_min_48h` | 903 | 10 | 1.1% |
| `spo2_min_48h` | 903 | 10 | 1.1% |
| `gcs_motor_min_48h` | 903 | 5 | 0.6% |

Shock index pairing audit:

- 893 patients had at least one matched HR/SBP pair;
- median number of matched pairs was 440;
- mean median pairing gap was 2.83 minutes.

Interpretation: GCS motor and shock index are no longer limiting eICU features. INR remains the dominant measurement limitation.

### Frozen-Transport Outcome Gradient

Pure frozen evaluation assigned all 843 eICU patients from 66 hospitals to one of the three phenotypes.

| Transported phenotype | N | Hospital mortality | ICU mortality | Early anemia | RBC 0-48h |
| --- | ---: | ---: | ---: | ---: | ---: |
| P1 | 539 | 5.4% | 2.8% | 11.4% | 0.4% |
| P2 | 222 | 25.7% | 16.2% | 34.5% | 5.9% |
| P3 | 82 | 42.7% | 29.3% | 58.0% | 11.0% |

The mortality gradient is strong and monotonic:

- P1 hospital mortality: 5.4%;
- P2 hospital mortality: 25.7%;
- P3 hospital mortality: 42.7%.

### Transported Phenotype Physiology

| Phenotype | Hb median | GCS motor median | MAP median | Shock index median | SpO2 median | Creatinine median | INR median | Platelet median |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| P1 | 11.9 | 6 | 62.0 | 0.88 | 90.0 | 0.75 | 1.1 | 207.0 |
| P2 | 10.7 | 4 | 51.0 | 1.14 | 92.0 | 0.81 | 1.1 | 202.5 |
| P3 | 9.5 | 4 | 51.5 | 1.26 | 74.5 | 1.54 | 1.5 | 146.0 |

Interpretation: P3 remains a high-risk multisystem phenotype with anemia, hypoxemia, renal dysfunction, higher INR, thrombocytopenia, and high mortality.

### Assignment Quality

| Metric | Value |
| --- | ---: |
| N | 843 |
| Phenotype count | 3 |
| Median nearest-centroid distance | 1.3369 |
| Median assignment margin | 1.0516 |
| Low margin <0.10 | 4.51% |
| Low margin <0.25 | 12.10% |

Interpretation: most eICU assignments are not borderline, although P3 remains the most shifted group.

### Sensitivity Robustness Results

All major transport sensitivities preserved a monotonic hospital mortality gradient.

| Analysis | N | P1 mortality | P2 mortality | P3 mortality | Minimum phenotype N |
| --- | ---: | ---: | ---: | ---: | ---: |
| Primary frozen transport | 843 | 5.4% | 25.7% | 42.7% | 82 |
| ICU LOS >=48h | 626 | 6.9% | 24.2% | 33.9% | 62 |
| No recorded RBC 0-48h | 819 | 5.4% | 25.8% | 39.7% | 73 |
| Strict SAH evidence | 605 | 6.6% | 30.5% | 45.6% | 68 |
| <=1 missing feature | 819 | 5.4% | 25.9% | 40.5% | 79 |
| Complete case | 428 | 7.2% | 33.6% | 43.1% | 58 |
| INR-free transport | 868 | 4.6% | 24.4% | 38.7% | 124 |

Interpretation: the external validation signal does not depend on one fragile cohort definition, RBC recording, INR availability, or heavy imputation.

### Hospital-Level Robustness

Hospital-clustered percentile intervals used 2,000 replicates in which the 66 hospitals were sampled with replacement and all stays within sampled hospitals were retained.

| Metric | Estimate | Hospital-clustered 95% interval |
| --- | ---: | ---: |
| P1 hospital mortality | 5.38% | 3.68%-7.39% |
| P2 hospital mortality | 25.68% | 20.75%-31.43% |
| P3 hospital mortality | 42.68% | 32.84%-52.44% |
| P2-P1 risk difference | 20.30 percentage points | 15.06-25.83 |
| P3-P1 risk difference | 37.30 percentage points | 26.99-47.37 |

The P1<P2<P3 mortality order was retained in all 66 leave-one-hospital-out analyses. The P2-P1 risk difference ranged from 19.15 to 21.53 percentage points and the P3-P1 difference from 35.13 to 39.42. These analyses address hospital dependence and single-hospital influence without claiming within-hospital replication of phenotype boundaries. Only aggregate robustness outputs were persisted.

### APACHE External Criterion Validation

Transported phenotype order aligned strongly with independent eICU severity metrics:

| Metric | P1 median | P2 median | P3 median | Spearman rho | P value |
| --- | ---: | ---: | ---: | ---: | ---: |
| Acute physiology score | 27 | 49 | 67 | 0.508 | 2.29e-51 |
| APACHE score | 36 | 57 | 79 | 0.480 | 3.58e-45 |
| Predicted hospital mortality | 0.069 | 0.243 | 0.426 | 0.445 | 2.00e-38 |
| Predicted ICU mortality | 0.039 | 0.175 | 0.299 | 0.453 | 6.15e-40 |

Interpretation: the transported phenotypes are externally anchored to established eICU severity scoring.

### INR Missingness Audit

| INR missing | N | Primary eligible N | Hospital mortality | Early anemia | APS mean | APACHE mean | Predicted hospital mortality |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| No | 457 | 453 | 19.0% | 26.6% | 43.4 | 52.7 | 21.7% |
| Yes | 446 | 390 | 9.0% | 16.5% | 34.7 | 43.1 | 13.1% |

Interpretation: INR is not missing completely at random. INR-measured patients are sicker. This is why the INR-free transport sensitivity should remain in the manuscript.

### De Novo eICU Structural Sensitivity

The eICU de novo K=3 model also forms a mortality gradient:

| De novo phenotype | N | Hospital mortality | Early anemia |
| --- | ---: | ---: | ---: |
| 1 | 447 | 5.8% | 9.9% |
| 2 | 296 | 17.9% | 29.6% |
| 3 | 100 | 42.0% | 53.5% |

However, concordance with frozen transport labels is low:

| Metric | Value |
| --- | ---: |
| Adjusted Rand Index | -0.0017 |
| Normalized mutual information | 0.0016 |
| Same ordered label rate | 45.7% |
| Silhouette | 0.269 |
| Minimum de novo cluster size | 100 |

Interpretation: eICU independently recovers a risk gradient, but its patient-level partition boundaries differ from the MIMIC-frozen classifier. This supports using de novo clustering only as a structural sensitivity analysis. It should not be presented as external validation of the exact cluster membership.

### Hb-Free Anemia Sensitivity

In the eICU Hb-free transport model, phenotype remains strongly associated with mortality, while early anemia is not statistically significant after adjustment:

| Term | OR | 95% CI | P value |
| --- | ---: | ---: | ---: |
| P2 vs P1 | 6.02 | 3.66-9.91 | 1.52e-12 |
| P3 vs P1 | 10.24 | 5.67-18.52 | 1.33e-14 |
| Early anemia | 1.46 | 0.92-2.34 | 0.111 |
| Age, per year | 1.02 | 1.01-1.04 | 0.001 |

Interpretation: the eICU validation supports the MIMIC conclusion that anemia is enriched in high-risk physiology but is not a stable independent mortality factor after accounting for an Hb-free phenotype structure.

## What Succeeded

The authorized frozen-transport rerun showed:

- MIMIC-anchored assignment produced a clinically large crude mortality gradient;
- APACHE severity and predicted mortality increased monotonically across transported phenotypes;
- shock index extraction was substantially improved by nearest HR/SBP pairing;
- all prespecified sensitivity analyses preserved the P1-to-P3 mortality ordering;
- hospital-clustered intervals excluded zero for both P2-P1 and P3-P1 differences, and all 66 leave-one-hospital-out analyses retained the mortality order;
- Hb-free anemia sensitivity reproduced the non-independent anemia signal;
- de novo eICU clustering recovered a risk gradient, supporting the presence of risk-stratifying physiological structure.

## What Did Not Succeed

The main unsuccessful parts are:

- de novo eICU labels did not agree with frozen MIMIC labels at the patient level; ARI was approximately zero;
- INR remained highly missing and showed informative missingness;
- complete-case analysis reduced sample size to 428 patients, so complete-case estimates are supportive but less efficient;
- P3 remains a smaller group, so its estimates are directionally strong but less precise.

## What Still Needs Improvement

Required reporting and future-analysis steps:

- retain the private bundle under access control and preserve its public hash and execution provenance;
- prespecify hospital-level robustness analyses in a future confirmatory protocol rather than treating the current post-outcome analysis as confirmatory;
- keep INR-free transport as a required sensitivity analysis, not an optional appendix;
- describe de novo clustering as structural sensitivity only, not as successful exact subtype replication;
- report shock index pairing logic explicitly, including the 15-minute HR/SBP window;
- consider a stricter 0-24h version if reviewers focus on post-baseline treatment contamination;
- avoid causal wording for RBC and other process-of-care variables unless time-varying methods are implemented.

## Manuscript Interpretation

Permitted current wording:

> In an authorized pure frozen-transport execution, eICU data were assigned using a privately hashed MIMIC-derived transform bundle without eICU fitting, tuning, or recalibration. Assigned groups showed monotonic hospital mortality and APACHE severity ordering; this exploratory result does not establish replication of cluster boundaries.

Recommended sensitivity wording:

> The mortality gradient was preserved across LOS >=48h, no-recorded-RBC, strict-SAH, low-missing, complete-case, and INR-free transport analyses. De novo eICU clustering also produced a mortality gradient, but patient-level agreement with frozen transport labels was low; therefore, de novo clustering was retained as a structural sensitivity analysis rather than used to redefine the phenotypes.

Recommended hospital-robustness wording:

> Hospital-clustered intervals preserved separation between P1 and the higher-risk groups, and the mortality order remained in all 66 leave-one-hospital-out analyses. These analyses address hospital dependence and influence, not within-hospital replication of cluster boundaries.

Recommended limitation:

> INR had substantial and informative eICU missingness, and eICU diagnosis definitions relied partly on diagnosis text and admission diagnosis fields rather than fully harmonized ICD coding. These limitations were addressed using INR-free and strict-SAH sensitivity analyses but should be reported transparently.

## Bottom Line

The eICU results provide a **reproducible exploratory frozen-transport signal, not confirmatory external validation**:

- the frozen MIMIC assignment rule assigned eICU patients into all three phenotypes;
- hospital and ICU mortality increase strongly across transported phenotypes;
- APACHE severity externally validates the phenotype ordering;
- early anemia and RBC exposure increase across phenotype severity;
- Hb-free sensitivity preserves strong phenotype mortality associations while early anemia remains non-significant;
- multiple robustness analyses preserve the mortality gradient;
- hospital-clustered and leave-one-hospital-out analyses preserve the mortality gradient;
- de novo clustering recovers a risk gradient but does not reproduce exact frozen classifier boundaries.

This is best described as a hypothesis-generating cross-database ordering signal. It is not proof of transportable cluster boundaries, a validated classifier, or discrete biological subtype entities.
