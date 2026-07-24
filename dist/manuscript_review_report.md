# Manuscript Review Report

> **Superseded gate status, 2026-07-24:** The prior READY recommendation below is
> retained as historical review evidence only. Audit
> `MR-20260724T120911+0800-418f7e0` found one blocking and five major issues.
> Remediation changed the manuscripts, validation entry point, result contract,
> bundles, and rendered outputs. The current gate is
> **PENDING INDEPENDENT REREVIEW**, not READY. See
> `reproducibility/issue-register.yaml` and
> `reproducibility/bundles/manuscript-review.yaml`.
>
> **Post-review update:** An authorized pure frozen-transport rerun and hospital-level
> robustness analysis were subsequently completed on 2026-07-24. Statements below
> describing those analyses as not assessed are retained only as the historical scope
> of this superseded review; a fresh independent review remains required.

**Scientific-content verdict:** READY

**Journal-upload package:** NOT READY

**Target:** Intensive Care Medicine, Original Paper

**Review date:** 2026-07-23

**Governance scope:** Public code, protocol/SAP, aggregate-reviewed manuscripts, ESM, figures, and reproducibility metadata. No patient-level data, restricted query result, credential, or new BigQuery analysis was accessed.

## Scope and decision boundary

This review focused on Purpose, Methods, and Conclusion in the English and Chinese cited manuscripts, with Results, ESM, frozen analysis evidence, and code inspected where needed to test consistency. `READY` means that no open blocking or major scientific-content finding remains in the reviewed manuscript package. It does not mean the journal upload package is ready: author metadata, institutional ethics wording, declarations, disclosure approval, editable production files, and final visual inspection remain open under REV-007.

Not assessed in this review were patient-level chart validation, a new authorized MIMIC/eICU rerun, subject-clustered regression re-estimation, hospital-clustered eICU uncertainty, cluster-specific bootstrap Jaccard summaries not present in the public aggregate package, and final DOCX/PDF typography.

## Five review rounds

| Round | Main finding | Severity at detection | Correction and closure evidence | Outcome |
| :---: | :--- | :--- | :--- | :--- |
| 1 | The manuscript implied a priori feature/model choices, the reconstructed SAP did not match the implemented main logistic formula, multiplicity and stay-level covariance were not explicit, and the revised abstract exceeded 250 words. | Major | SAP v1.0.1 now records the implemented post-outcome exploratory formula; both manuscripts and ESM label unadjusted P values and stay-level covariance; abstract reduced to 250 words. DEV-009 and DEV-010. | Closed |
| 2 | ESM Model 2 confidence intervals did not match the frozen log, and the same-window process model contained exactly duplicate etiology indicators, leaving parameters non-estimable. | Major | Removed the rank-deficient process model from inferential tables and prose claims while retaining its audit trail; the implemented main model and frozen primary estimates were unchanged. DEV-011. | Closed |
| 3 | Cohort prose incorrectly made MIMIC repeat-stay and massive-transfusion exclusions appear applicable to eICU; the eICU INR 49.4% rate used the pre-eligibility denominator rather than the final transport cohort. | Major | Database-specific eligibility is now separated. INR missingness is reported as 446/903 (49.4%) before feature eligibility and 390/843 (46.3%) in the transported cohort. DEV-012. | Closed |
| 4 | Repetitive and nonstandard wording, especially `same-hospital`, made the manuscript read formulaically and obscured the conventional outcome definition. | Minor | Bilingual language and unsupported-claim audit replaced formulaic wording with observed in-hospital, descriptive, non-causal language; no study estimate changed. | Closed |
| 5 | Independent mechanical, bilingual, citation, test, and privacy-oriented acceptance review. | Gate | All 42 repository tests passed; both Pandoc 3 citeproc preflights passed; 18 citation keys and figure paths align across languages; abstract is 250 words; no em/en dashes or disallowed overclaim phrases remain. | READY |

## Coverage matrix

| Domain | Evidence reviewed | Assessment |
| :--- | :--- | :--- |
| Purpose and estimand | Abstract, Introduction, protocol/SAP, freeze validation | Objective now matches an exploratory phenotyping study with descriptive in-hospital mortality associations and fixed eICU assignment. No prediction or treatment-effect estimand is implied. |
| Cohort and clinical definitions | Manuscripts, ESM cohort flow, cohort SQL, NSAH validation note | MIMIC and eICU eligibility rules, analysis grain, repeated admissions, traumatic-SAH handling, and the study-specific MIMIC transfusion exclusion are distinguishable and reproducible. Manual chart validation remains unavailable and is disclosed. |
| Time contract | Manuscripts, protocol/SAP, ESM Note 1 | The 0-48 h feature window, overlapping deaths/discharges, treatment influence, and absence of a 48 h landmark are explicit. Cox/prediction claims are not presented. |
| Phenotyping | Analysis code, stability script, ESM, freeze validation | Eight features, transformations, PCA, K=2-5 comparison, K=3 post-outcome exploratory status, seed, outcome-blind label ordering, and subject-grouped full-pipeline bootstrap are reported. |
| Regression and anemia | Implemented code, SAP v1.0.1, frozen log, manuscripts, ESM Tables 9 and 11A | Main formula now matches code. Estimates are exploratory, P values unadjusted, covariance stay-level, and Hb/anemia circularity is handled through a clearly post hoc Hb-free sensitivity analysis. The rank-deficient process model is not interpreted. |
| External transport | eICU code/results, ESM, manuscripts | The authorized pure frozen evaluation loads a privately hashed MIMIC transform bundle and is distinguished from de novo eICU clustering. Mortality ordering is reported as crude; ARI -0.0017 prevents a cluster-replication claim. INR denominator and imputation burden are explicit. |
| Conclusions | English and Chinese abstract/main conclusions | Conclusions are restricted to eligible stays, observed mortality ordering, specification-sensitive anemia estimates, and need for time-anchored prospective work. No clinical-use or causal claim remains. |
| Bilingual and writing quality | English/Chinese manuscripts | Citation keys, figures, quantitative claims, uncertainty boundaries, and section intent align. Formulaic AI-style transitions and inflated claims were not detected in the final pass. |
| Reproducibility and governance | Manifests, bundles, deviation and issue logs, release checklist | Public/restricted boundary remains intact. This revision changes reporting artifacts and SAP documentation only; it does not claim a new analysis rerun or bitwise regeneration. |

## Remaining non-blocking scientific limitations

- The ICD/text NSAH algorithms were not validated against manual chart review. External code evidence and aggregate dictionary/QC checks support candidate identification but do not establish study-specific sensitivity or positive predictive value.
- Thirteen rows came from patients with repeated admissions. Resampling was grouped by patient, but regression confidence intervals used stay-level covariance and may be slightly narrow.
- eICU INR missingness was informative and substantial; the INR-free sensitivity supports the crude ordering but does not remove all missingness bias.
- The post-review hospital-cluster bootstrap and leave-one-hospital-out analyses addressed multicenter dependence and single-hospital influence, but de novo clusters still did not reproduce the fixed patient-level boundaries.
- K=3, the feature set, and regression models were frozen after outcome access. All results therefore remain exploratory rather than confirmatory.

## Validation evidence

- `pytest -q`: 42 passed.
- Pandoc 3 citeproc preflight: English and Chinese manuscripts passed with no unresolved citation keys.
- English structured abstract: 250 words; take-home message: within 65 words.
- Bilingual citation-key set: 18/18 aligned; main figure paths aligned.
- `git diff --check`: passed at review time.
- No new BigQuery execution or patient-level validation was performed.

## Final recommendation

Proceed with the reviewed bilingual manuscript content. Keep the analysis labeled `FROZEN_EXPLORATORY`. Do not submit the journal package until REV-007 is closed through author/institution completion, final disclosure approval, editable-source production, fresh rendering, and visual inspection.
