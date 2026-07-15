---
name: mimic-statistical-analysis
description: Execute and document statistical analyses for MIMIC-IV observational studies. Use for Table 1, effect estimates, generalized regression, survival or competing-risk analysis, repeated admissions or ICU stays, missing-data handling, multiplicity, sensitivity analyses, model diagnostics, and production of manuscript-ready statistical outputs after the cohort and analysis table are defined. Do not use for prediction-model development, unsupervised phenotyping, or causal-effect identification workflows.
---

# MIMIC Statistical Analysis

Turn a frozen MIMIC-IV analysis table and statistical analysis plan into reproducible estimates, diagnostics, tables, and figures. Preserve the distinction between descriptive association, prediction, and causal effects.

Apply `mimic-data-governance` before reading the analysis table or model outputs. Keep patient-level data and sensitive derived artifacts inside the approved environment; share only cleared aggregate outputs.

## Required inputs

Establish these before fitting a model:

- study population, analysis unit, and unique key;
- eligibility time, index time, analysis landmark when applicable, follow-up start, censoring, and outcome window;
- primary estimand, exposure or grouping variable, outcome, and covariate roles;
- primary analysis, uncertainty level, missing-data plan, and pre-specified sensitivity analyses;
- handling of multiple admissions or ICU stays from one `subject_id`.

If an estimand or time origin is ambiguous, produce the missing analysis specification instead of silently choosing a model. Do not treat model adjustment as a substitute for a valid cohort or time design.

## Workflow

1. **Audit the analysis table.** Confirm row grain, key uniqueness, cohort counts, event counts, follow-up, impossible values, missingness, and agreement with the cohort flow. Reconcile every unexplained row loss before analysis.
2. **Lock the analysis specification.** Mark analyses as primary, secondary, sensitivity, or exploratory. Record any deviation from the pre-specified plan before viewing the affected result.
3. **Choose the method.** Read [references/analysis-methods.md](references/analysis-methods.md) for Table 1, regression, survival, competing-risk, repeated-record, missing-data, multiplicity, and sensitivity-analysis rules.
4. **Fit reproducibly.** Keep transformations, reference levels, knots, interactions, variance estimators, seeds, and software versions explicit. Check model assumptions and influential observations; do not report a model that failed a blocking diagnostic without a justified alternative.
5. **Quantify uncertainty.** Report the effect scale, estimate, interval, denominator, event count, and analysis population. Prefer clinically interpretable absolute measures alongside relative measures when the design supports them.
6. **Run planned robustness checks.** Vary only defensible cohort definitions, windows, missing-data strategies, functional forms, covariate sets, or competing-event assumptions. Label post hoc analyses as exploratory.
7. **Produce standard outputs.** Copy [assets/statistical-analysis-report-template.md](assets/statistical-analysis-report-template.md) and complete every applicable section. Tie every table and figure to a named analysis and a reproducible artifact.

## Hard gates

- Do not assume repeated admissions or stays are independent. Select one episode per patient or use a justified clustered, marginal, mixed, frailty, or robust-variance method.
- Do not use observations after the analysis landmark as baseline covariates.
- Do not select covariates only from univariable p-values.
- Do not use complete-case analysis without quantifying exclusions and defending its missingness assumptions.
- Do not infer subgroup differences from significance in one subgroup and non-significance in another; test the interaction and report uncertainty.
- Do not present odds ratios as risk ratios or hazard ratios as risks.
- Do not call an association causal unless a separate identification strategy supports that claim.

## Completion criteria

Finish only when cohort totals reconcile, repeated records are handled, the primary model and diagnostics are reproducible, missingness and multiplicity are addressed, uncertainty is reported, planned sensitivity analyses are complete, and all reported numbers trace to saved code and outputs.
