# Focused Methods Review

## Review status

- Review run: `MR-METHODS-20260724T165020+0800-418f7e0`
- Mode: focused, read-only scientific audit
- Primary target: `dist/manuscript_non_traumatic_sah_phenotypes_cited.md`
- Recommendation: **revise**
- Formal lifecycle gate: not issued
- Evidence level: current public working-tree text, code, aggregate frozen records, and recorded job provenance; no live BigQuery re-execution and no access to the private frozen-transform artifact
- Independence boundary: the reviewer previously participated in wording reconciliation, so this is an advisory evidence-based review rather than an independent formal acceptance decision

## Overall reviewer assessment

The study is methodologically coherent as a retrospective, post-outcome-access, exploratory early-course phenotyping analysis. The cohort grain, half-open 0–48 h windows, subject-grouped full-pipeline bootstrap, same-hospital descriptive estimand, post hoc Hb-free sensitivity, and non-causal interpretation are substantially better specified than in a typical exploratory EHR clustering manuscript.

The manuscript does not require a redesign to remain publishable as an exploratory analysis. The revised body Methods now makes a defensible distinction between frozen transport as a method property and exact artifact-level reproducibility. Targeted revision is still needed because the abstract overstates outcome-blind K selection and broadens overall partition stability, while the eICU measurement mapping remains under-described.

## Major findings

### METH-002 — “Mortality informed neither K selection” is not established after outcome access

- Severity: major
- Evidence:
  - The abstract says mortality informed neither K selection, fitting, nor label ordering (`manuscript`, line 22).
  - The same paragraph states K=3 was frozen after outcome review.
  - The protocol states that K=3 and the feature set were locked after outcomes had been accessed (`protocol.md`, lines 127–129).
  - The SAP states that K=3 is a post-outcome exploratory main specification (`sap.md`, lines 157–168).
  - The internal metrics do not uniquely choose K=3: K=2 has the best silhouette and Calinski–Harabasz values; K=4 has a slightly higher silhouette and lower Davies–Bouldin value but a sub-5% minimum cluster.
- Risk: exclusion of mortality from the algorithm is demonstrable; independence of the human K-selection decision from known outcomes is not.
- Smallest correction: replace the claim with “Mortality was not an input to PCA/K-means or label ordering; K=3 was selected as a post-outcome exploratory specification using internal metrics, minimum cluster size, and clinical interpretability.”
- Verification: the abstract and Methods must no longer imply prospectively outcome-blind K selection.

### METH-003 — Available stability evidence supports the overall partition, not every phenotype or individual assignment

- Severity: major
- Evidence:
  - The abstract broadly says “K=3 patient-grouped stability” was assessed and reports mean bootstrap ARI (`manuscript`, lines 22 and 26).
  - The 200-iteration full-pipeline subject bootstrap is genuine and technically appropriate.
  - The frozen contract records mean ARI 0.8554 and mean OOB ARI 0.8578, but cluster-specific Jaccard, assignment-margin distributions, and multiple-seed summaries are `not_assessed` (`reproducibility/canonical-results.yaml`, lines 22–31).
  - The SAP explicitly says these retained values support only overall partition stability (`sap.md`, lines 176–199).
  - P3 is the smallest group (108 stays), and the minimum cluster size across bootstrap iterations was 51.
- Risk: overall ARI can conceal instability of the small P3 membership and borderline individual assignments.
- Smallest correction without rerunning: consistently say “overall partition stability” and explicitly state that cluster-specific and assignment-level stability were not assessed.
- Stronger closure: recover or rerun cluster-wise Jaccard, assignment margins, and multiple-seed fits.

### METH-004 — Cross-database feature equivalence and eICU uncertainty are insufficiently described for the transport claim

- Severity: major
- Evidence:
  - eICU GCS motor uses `apacheapsvar.motor` as an untimed fallback when charted 0–48 h motor values are absent (`14_create_eicu_external_validation_cohort.sql`, lines 177–245).
  - The number of patients assigned using this fallback is not reported.
  - MIMIC and eICU use different pairing windows and some different clinical range filters: shock-index pairing is ±30 min in MIMIC and ±15 min in eICU; platelet, SpO2, and MAP filters are not identical.
  - INR was missing in 390/843 transported patients (46.3%) and missingness was associated with severity.
  - Hospital-clustered uncertainty was not assessed (`reproducibility/eicu-validation-results.yaml`, lines 8–11), although eICU is multicenter.
- Risk: apparent mortality ordering can partly reflect site-specific measurement, proxy-variable, missingness, and hospital-composition effects rather than transport of the same physiological rule.
- Smallest correction: add a compact MIMIC-to-eICU mapping table or ESM crosswalk with source, window, range, fallback frequency, and known differences; call mortality/APACHE patterns crude descriptive ordering and explicitly state that hospital-level uncertainty was not estimated.
- Stronger closure: rerun the authorized artifact path and add hospital-clustered or hospital-stratified precision analyses.

## Minor findings

### METH-001 — Frozen transport is methodologically defensible, but artifact-level reproducibility must remain qualified

- Severity: minor
- Evidence:
  - The current body Methods states that MIMIC-derived parameters were reconstructed from MIMIC and applied to eICU without fitting, tuning, or recalibration on eICU (`manuscript`, line 60). That satisfies the essential no-eICU-refitting property of exploratory frozen transport.
  - The exact serialized transform from the historical run was not retained, so byte-identical post hoc verification and exact replay remain unavailable.
  - The take-home, abstract, and introduction use shorter “frozen assignment” wording, while the Discussion says the rule is reproducible (`manuscript`, line 110).
- Risk: “reproducible” can be read as exact replay of the historical run, which is stronger than the available artifact evidence.
- Smallest correction without rerunning: keep “frozen transport,” but qualify it once as historical and exploratory, explicitly state that eICU did not participate in fitting, and replace “This makes the rule reproducible” with wording such as “This defines a transportable assignment rule; exact replay of the historical run is limited by the missing serialized artifact.”
- Stronger optional closure: export and privately hash the exact transform artifact, then execute the fail-closed eICU evaluation path.

### METH-005 — The 0–48 h phenotype is an early-course summary with unequal observation opportunity

- Severity: minor
- Evidence:
  - Sixty-six deaths and 91 ICU discharges occurred before the nominal 48 h window end (`reproducibility/freeze-validation.md`, lines 33–36).
  - Eligibility requires ICU LOS ≥24 h, so deaths and discharges before 24 h are excluded, while events during 24–48 h may truncate feature ascertainment.
  - The manuscript correctly rejects a 48 h landmark prediction interpretation (`manuscript`, lines 54, 64, and 112).
- Risk: readers may still interpret the groups as baseline phenotypes rather than treatment- and observation-dependent early-course summaries.
- Recommended action: retain “early-course” consistently and report the 66/91 truncation counts in Results or the ESM flow description.

### METH-006 — Regression uncertainty and functional-form diagnostics remain limited

- Severity: minor
- Evidence:
  - Thirteen stay rows came from repeat patients; bootstrap was grouped but logistic covariance was stay-level (`manuscript`, lines 66 and 112).
  - Age is entered linearly and no functional-form or influential-observation diagnostics are described.
  - Multiplicity is explicitly unadjusted and the model is correctly labeled exploratory.
- Risk: confidence intervals may be slightly optimistic and age adjustment may be misspecified, although the repeat burden is small.
- Recommended action: if rerunning, add subject-clustered covariance or a first-admission sensitivity and check nonlinear age; otherwise retain the current limitation and avoid confirmatory p-value language.

### METH-007 — The three-component PCA rule lacks an explicit selection rationale

- Severity: minor
- Evidence:
  - Three components were fixed and explain 56.41% of variance (`manuscript`, line 58; `sap.md`, lines 144–166).
  - No scree, eigenvalue, cumulative-variance threshold, or sensitivity to retained dimension is specified as the reason for choosing three components.
- Risk: dimensionality is another post-outcome analytic degree of freedom.
- Recommended action: state the exploratory rationale for three components and, if available without rerunning, show the scree/cumulative variance already generated; otherwise list PCA dimensionality as a specification limitation.

## Reproducibility follow-up

The current English manuscript hash is `315674c1e06e80b60be0259add84ab7d08d6d410a059c61ebee910a7db59a32d`, while `reproducibility/bundles/manuscript.yaml` still records `c72399b4c13d9fa6ec527641de98f29dd77b3bf4df555870ac91c8379920ffd5`. The Chinese source also differs from its recorded bundle hash. Consequently, the existing PDFs and generation manifest cannot be treated as synchronized submission artifacts after the latest wording changes. This is packaging work, not a reason to rerun the scientific analysis.

## What is already methodologically well handled

- The analysis is explicitly post-outcome and exploratory rather than retrospectively presented as prespecified.
- The unit is 1,186 ICU stays from 1,173 patients, and repeated-subject resampling is handled by `subject_id`.
- The bootstrap refits imputation, scaling, PCA, and K-means within each resample.
- Mortality is not an algorithmic clustering input and is not used for label ordering.
- The 0–48 h/death overlap is correctly separated from a landmark prognostic estimand.
- Hb circularity is recognized, and the Hb-free estimate is labeled post hoc and specification-sensitive.
- Treatment variables are not interpreted causally.
- Manual chart validation and eICU hospital clustering limitations are disclosed.

## Submission-oriented decision

No MIMIC or BigQuery rerun is necessary to resolve METH-001, METH-002, METH-003, METH-005, or METH-007 through appropriately narrowed reporting. “Frozen transport” may be retained as the method description because the documented historical workflow did not fit, tune, or recalibrate on eICU. A real eICU rerun is necessary only if the authors want to claim exact artifact-level reproducibility of the historical execution. Otherwise, the existing aggregate result can remain as historical exploratory frozen transport with the missing-artifact limitation.
