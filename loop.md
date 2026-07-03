# Non-traumatic SAH publication-oriented research loop

## 1. Manuscript position

Current main study:

> Early multimodal physiological phenotypes and outcomes in critically ill adults with non-traumatic subarachnoid hemorrhage using MIMIC-IV 3.1.

The manuscript should be positioned as an early ICU physiology phenotype study, not as a definitive transfusion treatment-effect paper. Early anemia and RBC transfusion remain important phenotype descriptors, exploratory effect-modification signals, and sensitivity-analysis dimensions, but the primary claim should be about interpretable early physiological phenotypes and outcome differences.

Primary question:

> Among adult ICU patients with non-traumatic SAH, can routinely available 0-48h physiological data identify clinically interpretable phenotypes associated with mortality, anemia burden, and transfusion exposure?

Primary dataset:

- `mimic-study-498508.non_traumatic_sah_study`
- Source script: `10_create_non_traumatic_sah_cohort.sql`
- Analysis script: `11_bigquery_notebook_non_traumatic_sah_analysis.py`
- Existing strategy docs:
  - `docs/non_traumatic_sah_study_transition.md`
  - `docs/early_physiological_phenotype_strategy.md`
  - `docs/next_analysis_steps.md`

## 2. Fixed decision for point 3: clinical physiology feature dictionary

Point 3 means the project must treat feature engineering as a clinical design artifact, not just as a list of model inputs.

The current fixed primary feature set is the 8-variable 0-48h physiology panel already implemented in `10_create_non_traumatic_sah_cohort.sql` and used by `11_bigquery_notebook_non_traumatic_sah_analysis.py`.

| Domain                                     | Primary variable      | Aggregation                                                  | Worse direction | Role in manuscript                                                                                             |
| ------------------------------------------ | --------------------- | ------------------------------------------------------------ | --------------- | -------------------------------------------------------------------------------------------------------------- |
| Anemia                                     | `hb_min_48h_all`      | Minimum hemoglobin from ICU admission to 48h                 | Lower           | Core clustering feature; captures early anemia burden                                                          |
| Neurologic motor response                  | `gcs_motor_min_48h`   | Minimum GCS motor component from ICU admission to 48h        | Lower           | Core clustering feature for neurologic motor severity; checked against total GCS and GCS grade alternatives    |
| Hemodynamic perfusion                      | `map_min_48h`         | Minimum MAP                                                  | Lower           | Core clustering feature; captures hypotension/perfusion vulnerability                                          |
| Hemodynamic stress                         | `shock_index_max_48h` | Maximum HR/SBP                                               | Higher          | Core clustering feature; captures circulatory stress                                                           |
| Oxygenation                                | `spo2_min_48h`        | Minimum SpO2                                                 | Lower           | Core clustering feature; chosen over PaO2/FiO2 to avoid FiO2-driven missingness                                |
| Renal / organ dysfunction                  | `creatinine_max_48h`  | Maximum creatinine                                           | Higher          | Core clustering feature; captures early renal dysfunction                                                      |
| Coagulation                                | `inr_max_48h`         | Maximum INR                                                  | Higher          | Core clustering feature; captures early coagulation abnormality                                                |
| Platelet / coagulation-inflammatory status | `platelet_min_48h`    | Minimum platelet count                                       | Lower           | Core clustering feature; captures thrombocytopenia/coagulation vulnerability                                   |

Candidate variables are not primary clustering inputs unless the audit justifies them:

| Candidate                                         | Current role                                   | Reason not primary                                                                   |
| ------------------------------------------------- | ---------------------------------------------- | ------------------------------------------------------------------------------------ |
| `lactate_max_48h`                                 | Description and sensitivity subset             | Clinically meaningful but often selectively measured                                 |
| `pao2_fio2_min_48h`                               | Oxygenation sensitivity                        | FiO2 and blood gas missingness can dominate clustering                               |
| `spo2_fio2_min_48h`                               | Oxygenation sensitivity                        | Charted FiO2 coverage and unit cleaning are unstable                                 |
| `oxygenation_min_48h`                             | Oxygenation sensitivity                        | Composite oxygenation source may mix measurement mechanisms                          |
| `epvs_mean_48h`, `epvs_first_48h`, `epvs_max_48h` | Candidate sensitivity feature                  | Derived from Hb/Hct; possible collinearity with anemia                               |
| `troponin_peak_48h`                               | Candidate mechanism descriptor                 | Assay and indication-driven missingness require audit                                |
| `sodium_max_48h`                                  | Description and sensitivity feature            | Removed from the primary panel for the Hb+INR feature-set test                       |
| `sapsiii_24h`, `sofa_24h`                         | Prediction comparison / covariate if available | Overlaps with core physiological variables and is not available in the current table |
| `gcs_grade_min_48h`                               | Descriptive / sensitivity comparison           | Kept out of primary clustering because it is derived directly from total GCS         |
| `gcs_min_48h`                                     | Descriptive / sensitivity comparison           | Kept out of primary clustering to avoid repeating information already captured by GCS motor |
| `hb_min_48h_pre_transfusion`                      | Hb sensitivity                                 | Used to assess whether transfusion timing changes anemia-related findings            |

Feature-loop pass criteria:

- Every primary feature has a clinical domain, time window, aggregation rule, source table, reasonable range filter, and missingness summary.
- No primary feature has unacceptable missingness. As a working rule, `<20%` is acceptable, `20%-40%` requires sensitivity analysis, and `>40%` should trigger replacement or demotion.
- Hb sensitivity is explicitly handled with `hb_min_48h_pre_transfusion` and/or the no-RBC 48h cohort.
- GCS redundancy is explicitly handled with `phenotype_gcs_sensitivity_summary`.
- Oxygenation sensitivity is handled without making FiO2-dependent variables primary.

## 3. Fixed decision for point 4: clinically interpretable phenotype table

Point 4 means the output of clustering must become a clinical phenotype table that an ICU/neurocritical care reviewer can understand without trusting the algorithm.

The current fixed primary phenotype solution is:

- Primary: K=3
- Exploratory high-resolution solution: K=4
- Rationale: K=3 prioritizes stability, sample size, and interpretability; K=4 is used only to test whether a small extreme high-risk subgroup exists inside the severe phenotype.

Required primary phenotype table:

| Field group          | Required columns or source table                                         | Purpose                                                           |
| -------------------- | ------------------------------------------------------------------------ | ----------------------------------------------------------------- |
| Size                 | phenotype, N, percentage                                                 | Shows whether any cluster is too small                            |
| Outcome              | hospital mortality, ICU mortality if available, ICU/hospital LOS         | Shows clinical separation                                         |
| Core physiology      | median/IQR of the 7 primary features                                     | Makes the phenotype clinically interpretable                      |
| Anemia               | `early_anemia_all`, `early_anemia_pre_transfusion`, Hb distribution      | Tests whether anemia burden differs by phenotype                  |
| RBC exposure         | `any_rbc_transfusion_48h`, `rbc_events_48h`, `rbc_units_48h` if reliable | Describes treatment exposure without overclaiming causality       |
| Etiology specificity | `nsah_evidence_level`, aneurysm diagnosis/procedure flags                | Addresses non-traumatic SAH heterogeneity                         |
| Stability            | silhouette, bootstrap ARI, hierarchical-vs-K-means ARI                   | Shows the phenotype is not a single unstable algorithmic artifact |

Required interpretation rule:

Do not label clusters as P1/P2/P3 only. Each phenotype needs a clinical label based on the dominant physiology. The exact labels must be assigned after reading `phenotype_cluster_centers_zscore` and raw summaries, but the preferred label style is:

- Low-risk / preserved physiology phenotype
- Neurologic injury-predominant phenotype
- Systemic hypoperfusion or multiorgan dysfunction phenotype

Possible labels must be data-driven. For example, a cluster should only be called "hypoperfusion" if it shows some combination of lower MAP, higher shock index, higher lactate when available, renal dysfunction, or higher vasopressor/proxy burden if later added.

Phenotype-loop pass criteria:

- `phenotype_cluster_centers_zscore` shows coherent separation across at least two physiological domains.
- `phenotype_outcome_summary` shows clinically meaningful outcome differences.
- `phenotype_baseline_characteristics` does not reveal that clusters are only age, sex, admission type, or aneurysm-evidence groups.
- `phenotype_gcs_sensitivity_summary` shows the main structure is not only dual GCS coding.
- `phenotype_bootstrap_stability` is acceptable enough to describe the clusters as reproducible. If ARI is weak, the manuscript must say "exploratory risk-stratifying phenotypes" rather than "validated phenotypes."
- K=4 is only promoted if the small subgroup has a clinically coherent extreme-risk profile and is not merely outliers or missingness.

## 4. Research loop design

This project should run as a manuscript-quality loop. Each loop has one job, one artifact, and one decision. Do not add models or variables unless they solve the current weakest manuscript problem.

Each loop has a hard iteration cap. If a loop reaches its cap without passing its decision rule, record the unresolved issue as a limitation and move on — do not loop indefinitely. Backtracking is allowed: if a later loop (e.g., Loop 6) reveals a fundamental problem that requires revisiting an earlier loop (e.g., Loop 3), return to that loop and restart its iteration counter from zero. Backtracking itself is capped at 2 occurrences across the entire project; on the third backtrack, record the issue as a limitation and proceed.

### Loop 1. Question loop

Objective:

- Keep the paper focused on non-traumatic SAH early physiological phenotypes.

Artifact:

- One-paragraph central hypothesis.
- Working title.
- Target journal tier and rationale.

Decision rule:

- Continue only if the claim can be stated without causal overreach: early 0-48h physiology identifies interpretable mortality-associated phenotypes.

Failure response:

- If the story becomes primarily transfusion HTE, split it into a later exploratory paper and keep this paper phenotype-focused.

Max iterations: 2. If unresolved after 2 rounds, proceed with the best-available framing and note the tension as a limitation.

### Loop 2. Cohort loop

Objective:

- Make the cohort clinically defensible and reproducible.

Artifact:

- `cohort_flowchart_counts`
- Cohort diagram
- Inclusion/exclusion paragraph

Decision rule:

- Adult non-traumatic SAH, ICU stay, first ICU stay, ICU LOS `>=24h`, no massive early transfusion in primary analysis, adequate core-feature completeness.

Failure response:

- If sample loss is too high, inspect which criterion causes loss before changing definitions. Do not relax criteria without recording the clinical reason.

Cohort sensitivity cohorts (defined here, executed in Loop 6):

This loop also defines the sensitivity cohorts that Loop 6 will reuse, so the definitions are consistent and the work is not duplicated:

- No-RBC 48h cohort (patients with zero RBC transfusions in the first 48h)
- ICU LOS `>=48h` cohort (exclude early deaths / early transfers)
- These cohorts are defined once here; Loop 6 re-applies the primary analysis pipeline to them.

Max iterations: 3. If unresolved after 3 rounds, document the cohort definition as final, list the remaining sample-loss concern as a limitation, and proceed.

### Loop 3. Feature loop

Objective:

- Lock the 8-feature primary physiology dictionary and candidate sensitivity variables.

Artifact:

- Feature dictionary table from section 2.
- `feature_missingness_summary`
- `oxygenation_source_missingness_summary`
- Candidate audit for lactate, ePVS, troponin, FiO2-dependent oxygenation.

Decision rule:

- Primary features stay fixed unless missingness or implausible distributions make one unusable.

Failure response:

- Replace high-missingness primary variables with lower-missingness clinically adjacent variables only after documenting why.

Max iterations: 3. If unresolved after 3 rounds, lock the best-available feature set and list the remaining missingness concern as a limitation.

### Loop 4. Phenotype loop

Objective:

- Convert K-means output into clinically meaningful phenotypes.

Artifact:

- `phenotype_cluster_centers_zscore`
- `phenotype_feature_summary_raw`
- `phenotype_outcome_summary`
- Phenotype label memo

Decision rule:

- K=3 remains primary if it is stable, interpretable, and has adequate cluster sizes. K=4 remains exploratory unless it clearly identifies a coherent extreme-risk subgroup.

Failure response:

- If clusters are not interpretable, do not force labels. Revisit feature set and missingness before trying more complex algorithms.

Max iterations: 3. If unresolved after 3 rounds, report the best-available clustering as exploratory and downgrade the phenotype claim language accordingly.

### Loop 5. Anemia and transfusion loop

Objective:

- Define how anemia and RBC exposure relate to phenotypes without overstating causality.

Artifact:

- `phenotype_anemia_feasibility`
- `phenotype_anemia_stratified_models`
- No-RBC sensitivity phenotype summary

Decision rule:

- If phenotype-by-anemia cells have enough events, report adjusted exploratory models. If cells are sparse, report descriptive event counts and interaction models only.

Failure response:

- If RBC exposure is rare or strongly confounded, keep transfusion as a descriptor/sensitivity factor rather than a main treatment-effect claim.

Max iterations: 2. If unresolved after 2 rounds, keep transfusion as a phenotype descriptor only and explicitly limit causal language.

### Loop 6. Robustness loop

Objective:

- Make the phenotype robust against obvious reviewer attacks.

This loop reuses the sensitivity cohorts defined in Loop 2 (no-RBC 48h cohort, ICU LOS `>=48h` cohort). Do not redefine them here — apply the primary analysis pipeline from Loop 4 to these pre-defined sub-cohorts.

Artifact:

- `phenotype_gcs_sensitivity_summary`
- `phenotype_bootstrap_stability`
- `phenotype_sensitivity_cohort_summary`
- `phenotype_epvs_sensitivity_summary`
- Alternative clustering comparison if available

Decision rule:

- The main clinical interpretation should survive GCS sensitivity, no-RBC cohort, ICU LOS `>=48h` cohort, and K=4 high-resolution analysis.

Failure response:

- If a sensitivity analysis changes the story, downgrade the claim and explain what the sensitivity reveals instead of hiding it.

Max iterations: 2. If unresolved after 2 rounds, report the sensitivity results transparently and let them stand as documented limitations rather than re-running the primary analysis indefinitely.

### Loop 7. Prediction and incremental-value loop

Objective:

- Show that phenotypes are useful summaries of physiology, not just decorative clusters.

Artifact:

- `phenotype_prediction_metrics`
- Calibration / Brier / AUROC comparison

Decision rule:

- Phenotype-only does not need to beat all raw features. The key question is whether phenotype plus anemia/covariates provides interpretable risk stratification beyond GCS-only.

Failure response:

- If prediction value is weak, position phenotypes as descriptive clinical profiles and avoid claiming predictive superiority.

Max iterations: 2. Prediction models are confirmatory, not generative — two rounds are enough to settle the incremental-value question.

### Loop 8. Mechanism loop

Objective:

- Connect observed phenotypes to plausible SAH pathophysiology.

Artifact:

- Mechanism memo and conceptual figure.

Mechanistic axes:

- Neurologic injury severity
- Oxygen-carrying capacity / anemia
- Systemic perfusion reserve
- Oxygenation
- Renal and platelet/coagulation vulnerability
- Possible link to secondary brain injury and delayed cerebral ischemia, stated cautiously because DCI may not be directly observed in MIMIC.

Decision rule:

- Mechanistic claims must be directly supported by phenotype profiles or framed as hypotheses.

Failure response:

- If a mechanism is not measured, write it as an interpretation hypothesis, not a finding.

Max iterations: 2. Mechanism interpretation is inherently speculative for an observational study — two rounds are enough.

### Loop 9. Reviewer loop

Objective:

- Simulate major reviewer attacks before manuscript submission.

Artifact:

- Reviewer attack-response table.

Required reviewer concerns:

- Case definition and traumatic SAH exclusion.
- Non-traumatic SAH heterogeneity and aneurysm-evidence sensitivity.
- Missing data and measurement opportunity bias.
- GCS dominance.
- Treatment contamination by RBC transfusion.
- Whether clusters are reproducible.
- Whether anemia/transfusion claims are overinterpreted.

Decision rule:

- Every major concern must map to a result table, sensitivity analysis, or explicit limitation.

Failure response:

- If a concern cannot be answered empirically, weaken the manuscript claim before submission.

Max iterations: 2. After two rounds of reviewer-attack mapping, any remaining unanswered concerns become explicit limitations.

### Loop 10. Manuscript loop

Objective:

- Keep writing synchronized with analysis(@dist/analysis_result.md).

Artifact:

- Rolling manuscript outline.
- Table/figure shell.

Suggested main figures and tables:

- Figure 1: Cohort flowchart.
- Figure 2: K=3 phenotype standardized-center heatmap.
- Figure 3: Mortality and anemia/transfusion burden across phenotypes.
- Supplementary Figure: K=4 refinement and K=3/K=4 crosstab.
- Table 1: Baseline characteristics by K=3 phenotype.
- Table 2: Raw phenotype physiology and outcomes.
- Supplementary Table: sensitivity analyses.

Decision rule:

- Each result in the abstract must be traceable to one figure or table.

Failure response:

- If a result cannot be shown cleanly, remove it from the abstract rather than expanding analysis indefinitely.

Max iterations: 2. Manuscript synchronization should converge quickly — if it doesn't, the underlying analysis loops need revisiting (backtrack).

## 5. Stop rules before submission

The study is ready for manuscript drafting when all are true:

- Cohort flow is reproducible and clinically defensible.
- The 8-feature primary dictionary is fixed and justified.
- K=3 phenotypes have readable clinical labels based on raw and z-score summaries.
- K=4 is clearly described as exploratory high-resolution analysis.
- Missingness, GCS redundancy, no-RBC, and ICU LOS `>=48h` sensitivities have been checked.
- Anemia and transfusion results are described at the correct evidentiary level.
- The main claim avoids unsupported causal or treatment-recommendation language.
- Every major reviewer concern has either a table, a sensitivity result, or a limitation.
