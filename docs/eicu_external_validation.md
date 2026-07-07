# eICU External Validation Plan and Results

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

The primary external validation uses **Frozen Transport**, not eICU de novo clustering.

In a transport validation, the MIMIC-IV phenotype model is treated as the development model. The preprocessing rules, imputation medians, transformations, scaling, PCA projection, and phenotype centroids are fixed from MIMIC-IV and then applied directly to eICU. This tests whether a new patient or a new external cohort can be assigned to the MIMIC-derived phenotypes without refitting the model on the validation data.

This is the clinically relevant validation target. If the model were used prospectively, a clinician would not recluster the entire local database each time a new patient arrived. The patient would be projected into a fixed classifier.

De novo clustering in eICU is still useful, but only as a **structural sensitivity analysis**. It asks whether similar physiological groupings emerge when eICU is allowed to define its own cluster boundaries. It does not replace transport validation, because it uses the validation distribution to refit the phenotype geometry.

## Validation Design

### Primary Analysis: Frozen Transport

The MIMIC pipeline is frozen from `mimic-study-498508.non_traumatic_sah_study.phenotype_cluster_assignments`.

Frozen components:

- MIMIC median imputation;
- `log1p` transformation for creatinine and INR;
- MIMIC StandardScaler mean and SD;
- MIMIC PCA eigenvectors;
- MIMIC phenotype centroids in 3-PC space;
- ordered phenotype labels P1, P2, and P3.

eICU patients are transformed using these frozen MIMIC parameters and assigned to the nearest MIMIC phenotype centroid.

### Sensitivity Robustness

The improved validation adds prespecified sensitivity analyses that address the main reviewer-facing weaknesses:

- ICU LOS >=48h sensitivity, to reduce concern that a 48-hour feature window is partly unavailable in shorter stays;
- no recorded RBC sensitivity, because eICU transfusion units are heterogeneous and should not be used as a hard primary exclusion;
- strict SAH sensitivity, requiring SAH evidence from diagnosis ICD/text rather than admissionDx-only evidence;
- low-missing and complete-case sensitivity, to test dependence on imputation;
- INR-free transport sensitivity, because INR is the most missing eICU core feature;
- Hb-free anemia sensitivity, because Hb is part of the primary phenotype and anemia adjustment would otherwise be partly circular.

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

These results were generated on July 7, 2026 by running:

```bash
bq query --use_legacy_sql=false --project_id=mimic-study-498508 --location=US < 14_create_eicu_external_validation_cohort.sql
python scripts/15_run_eicu_external_validation.py
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

### Frozen Transport Outcome Gradient

The frozen MIMIC classifier assigned all 843 eICU validation patients to one of the three phenotypes.

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
| Median nearest-centroid distance | 1.337 |
| Median assignment margin | 1.050 |
| Low margin <0.10 | 4.4% |
| Low margin <0.25 | 12.0% |

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
| 1 | 450 | 5.8% | 9.8% |
| 2 | 293 | 18.1% | 29.9% |
| 3 | 100 | 42.0% | 53.5% |

However, concordance with frozen transport labels is low:

| Metric | Value |
| --- | ---: |
| Adjusted Rand Index | -0.003 |
| Normalized mutual information | 0.002 |
| Same ordered label rate | 43.9% |
| Silhouette | 0.269 |
| Minimum de novo cluster size | 100 |

Interpretation: eICU independently recovers a risk gradient, but its patient-level partition boundaries differ from the MIMIC-frozen classifier. This supports using de novo clustering only as a structural sensitivity analysis. It should not be presented as external validation of the exact cluster membership.

### Hb-Free Anemia Sensitivity

In the eICU Hb-free transport model, phenotype remains strongly associated with mortality, while early anemia is not statistically significant after adjustment:

| Term | OR | 95% CI | P value |
| --- | ---: | ---: | ---: |
| P2 vs P1 | 6.16 | 3.74-10.13 | 8.30e-13 |
| P3 vs P1 | 10.27 | 5.68-18.57 | 1.22e-14 |
| Early anemia | 1.47 | 0.92-2.36 | 0.105 |
| Age, per year | 1.02 | 1.01-1.04 | 0.001 |

Interpretation: the eICU validation supports the MIMIC conclusion that anemia is enriched in high-risk physiology but is not a stable independent mortality factor after accounting for an Hb-free phenotype structure.

## What Succeeded

The strongest successes are:

- frozen MIMIC transport produced a clear and clinically large external mortality gradient;
- APACHE severity and predicted mortality increased monotonically across transported phenotypes;
- shock index extraction was substantially improved by nearest HR/SBP pairing;
- all prespecified sensitivity analyses preserved the P1-to-P3 mortality ordering;
- Hb-free anemia sensitivity reproduced the non-independent anemia signal;
- de novo eICU clustering recovered a risk gradient, supporting the presence of risk-stratifying physiological structure.

## What Did Not Succeed

The main unsuccessful parts are:

- de novo eICU labels did not agree with frozen MIMIC labels at the patient level; ARI was approximately zero;
- INR remained highly missing and showed informative missingness;
- complete-case analysis reduced sample size to 428 patients, so complete-case estimates are supportive but less efficient;
- P3 remains a smaller group, so its estimates are directionally strong but less precise.

## What Still Needs Improvement

Recommended next improvements before manuscript submission:

- keep INR-free transport as a required sensitivity analysis, not an optional appendix;
- describe de novo clustering as structural sensitivity only, not as successful exact subtype replication;
- report shock index pairing logic explicitly, including the 15-minute HR/SBP window;
- consider a stricter 0-24h version if reviewers focus on post-baseline treatment contamination;
- avoid causal wording for RBC and other process-of-care variables unless time-varying methods are implemented.

## Manuscript Interpretation

Recommended primary wording:

> In the eICU external validation, the frozen MIMIC-derived phenotype classifier transported successfully and identified a monotonic hospital mortality gradient from P1 to P3. Transported phenotypes also showed monotonic increases in independent eICU APACHE severity scores and predicted mortality, supporting external criterion validity.

Recommended sensitivity wording:

> The mortality gradient was preserved across LOS >=48h, no-recorded-RBC, strict-SAH, low-missing, complete-case, and INR-free transport analyses. De novo eICU clustering also produced a mortality gradient, but patient-level agreement with frozen transport labels was low; therefore, de novo clustering was retained as a structural sensitivity analysis rather than used to redefine the phenotypes.

Recommended limitation:

> INR had substantial and informative eICU missingness, and eICU diagnosis definitions relied partly on diagnosis text and admission diagnosis fields rather than fully harmonized ICD coding. These limitations were addressed using INR-free and strict-SAH sensitivity analyses but should be reported transparently.

## Bottom Line

The improved eICU results provide **supportive external validation** for the MIMIC-derived phenotype model:

- the frozen transport classifier assigns eICU patients into all three phenotypes;
- hospital and ICU mortality increase strongly across transported phenotypes;
- APACHE severity externally validates the phenotype ordering;
- early anemia and RBC exposure increase across phenotype severity;
- Hb-free sensitivity preserves strong phenotype mortality associations while early anemia remains non-significant;
- multiple robustness analyses preserve the mortality gradient;
- de novo clustering recovers a risk gradient but does not reproduce exact frozen classifier boundaries.

This is best described as evidence for **transportable risk-stratifying physiological phenotypes**, not proof of discrete biological subtype entities.
