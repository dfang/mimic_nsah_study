# Massive-Transfusion Sensitivity Analysis Design

## Status and scope

This design resolves one documented freeze blocker in the non-traumatic SAH phenotyping study: the role of post-entry massive RBC transfusion in the primary cohort and sensitivity analyses.

The primary analysis will continue to exclude ICU stays with massive transfusion during 0–24 hours. A new sensitivity analysis will include those stays. This is a retrospective, outcome-informed design decision and must not be described as a pre-outcome prespecification. The protocol and SAP remain `DRAFT_BLOCKED` after this work because other freeze blockers remain unresolved.

No BigQuery query execution, result regeneration, or patient-level data access is included in this change. Verification is limited to code review, static checks, and Python syntax checks.

## Rationale

The existing SQL defines `massive_transfusion_24h` as either:

- at least five RBC events during the first 24 hours after ICU admission; or
- at least five total units when recorded amounts can be interpreted as units.

Because this exclusion is determined after cohort entry and may reflect early treatment or severity, it can introduce treatment-related selection. Retaining the exclusion in the primary cohort preserves continuity with the current analysis and manuscript, while the inclusive sensitivity analysis tests whether the phenotype structure and outcome patterns depend materially on that exclusion.

## Cohort contract

The existing primary cohort definition remains unchanged:

```text
eligible_primary_analysis =
    core_feature_missing_count <= 2
    AND massive_transfusion_24h = 0
```

The new inclusive sensitivity cohort is:

```text
eligible_include_massive_transfusion_sensitivity =
    core_feature_missing_count <= 2
```

The new flag changes only the massive-transfusion restriction. It must not silently alter age, non-traumatic SAH evidence, ICU-stay selection, ICU length-of-stay, feature windows, missingness threshold, or any other eligibility rule.

Existing `eligible_sensitivity_48h_los` and `eligible_no_transfusion_sensitivity` definitions remain unchanged.

## SQL changes

`10_create_non_traumatic_sah_cohort.sql` will:

1. Add `eligible_include_massive_transfusion_sensitivity` to `physiology_features_48h`.
2. Add its row count to the final wide-table validation query.
3. Add a clearly named sensitivity row to `cohort_flowchart_counts`.
4. Preserve `massive_transfusion_24h`, RBC event counts, and convertible unit totals for audit.
5. Clarify comments so that the massive-transfusion exclusion is not presented as a biologically intrinsic cohort criterion.

The existing primary flag and table names will not be renamed, preserving downstream compatibility.

## Python analysis changes

`11_bigquery_notebook_non_traumatic_sah_analysis.py` will:

1. Load the new eligibility flag.
2. Register it in `SENSITIVITY_COHORT_FLAGS` under the stable analysis name `include_massive_transfusion`.
3. Query the minimal analysis superset with `eligible_include_massive_transfusion_sensitivity = 1`, then derive the primary dataframe in memory with `eligible_primary_analysis = 1`.
4. Use the primary dataframe for every existing primary workflow and pass the unfiltered analysis superset only to the cohort-sensitivity pathway, preventing massive-transfusion rows from being discarded before sensitivity filtering.
5. Reuse the existing sensitivity-analysis pathway so preprocessing and clustering are independently refit within each sensitivity cohort, consistent with the current sensitivity framework.
6. Preserve the primary `COHORT_FLAG = "eligible_primary_analysis"`.
7. Compute `ari_vs_primary_subset` on stays overlapping the primary assignments, record `primary_overlap_n`, and do not require newly included stays to have primary labels.
8. Persist each sensitivity phenotype's raw feature means and standardized K-means centers for all seven implemented `FEATURES` columns.
9. Label each output row with its actual eligibility flag rather than the primary flag.

No new estimator, dependency, random seed, feature set, or outcome definition is introduced.

## Protocol, SAP, and deviation record

`protocol.md` and `sap.md` will be brought into the active worktree from their current source versions and revised to state:

- the primary estimand-like descriptive target is restricted to patients without observed massive RBC transfusion in the first 24 hours;
- this restriction occurs after cohort entry and may induce treatment-related selection;
- the inclusive sensitivity cohort removes only this restriction;
- phenotype structure, cluster size, cluster-profile shifts, and outcome-association direction will be compared without choosing a preferred analysis based on results;
- material instability will be reported as treatment sensitivity and will limit substantive phenotype naming;
- this decision was fixed after outcome access and is exploratory.

An append-only `deviations.md` entry will record the decision date, prior implementation, rationale, affected files, and the fact that outcome access preceded this decision. It will not claim that the change restores prospective freezing.

The documents will remain `DRAFT_BLOCKED`. The massive-transfusion checklist item may be marked resolved, but unrelated blockers—such as the mortality time contract, repeated-patient inference, complete freeze artifacts, environment lock, and independent approval—remain open.

## Interpretation and reporting rules

The sensitivity analysis is supportive rather than co-primary. It will be interpreted using the following prewritten rules:

- Similar cluster profiles and outcome gradients support robustness to the exclusion.
- Meaningful changes in cluster composition, centers, or association direction indicate treatment sensitivity.
- The analysis will not be used to estimate the causal effect of RBC transfusion.
- Results will not justify relabeling an outcome-informed analysis as confirmatory.

Where available in the existing pipeline, comparisons should report sample size, cluster sizes, phenotype profiles, mortality estimates, and stability metrics. Absence of an implemented metric must be documented rather than replaced with a post hoc success threshold.

## Verification

Verification will include:

- search-based confirmation that the new flag appears in the SQL definition, validation count, flowchart, Python selected columns, and sensitivity registry;
- confirmation that the primary flag still excludes `massive_transfusion_24h = 1`;
- confirmation that the inclusive flag contains no massive-transfusion condition;
- Python syntax compilation for modified Python files;
- a synthetic behavioral test showing that newly included massive-transfusion stays reach sensitivity clustering, overlap ARI is finite on primary-overlap stays, profile/center columns are populated, and the output cohort flag is the actual sensitivity flag;
- repository diff review for unintended changes;
- documentation checks that `DRAFT_BLOCKED`, outcome-access disclosure, and non-causal language remain intact.

BigQuery execution and result-level validation are explicitly out of scope unless separately authorized in a compliant environment.

The active protocol/SAP must describe the implemented main pipeline accurately: seven core features, median imputation, Z-score standardization, and direct K-means in seven-dimensional scaled space. PCA and the earlier eight-feature contract are not part of the implemented primary or massive-transfusion sensitivity pathway and must not be repeated as implemented behavior.

## Rejected alternatives

### Runtime-only Python filtering

Rejected because it would hide the cohort contract in downstream code and weaken SQL-level auditability.

### Separate inclusive wide table

Rejected because it would duplicate cohort data and selection logic without adding analytical value.

### Reversing the primary and sensitivity cohorts

Rejected because it would materially change the current manuscript population and analysis lineage. Such a change would require a broader redesign rather than resolution of the existing blocker.
