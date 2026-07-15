# Statistical Analysis Method Rules

Read the sections that match the study design. Record the chosen rule and any justified departure in the analysis report.

## Descriptive tables

- Report counts and percentages for categorical variables and appropriate location and spread for continuous variables.
- Include units, denominators, missing counts, and the time window used to define every variable.
- Use standardized differences to describe group imbalance. Do not turn Table 1 into a battery of baseline hypothesis tests.
- Keep post-index variables and outcomes out of baseline sections.

## Effect estimates and regression

- Select the model from the outcome scale and estimand: linear or robust alternatives for continuous outcomes, binomial models for risks, count models for rates, and ordinal or multinomial models only when category assumptions are defensible.
- State reference groups and report transformed estimates with confidence intervals.
- Model important continuous predictors continuously; inspect nonlinearity and prefer restricted splines or pre-specified transformations over arbitrary categorization.
- Check separation, overdispersion, residual patterns, influential observations, and collinearity as applicable.
- Base confounder adjustment on design and subject-matter reasoning, not automated univariable screening.

## Survival and competing risks

- Define the time origin, risk set, event, competing events, administrative end, loss to follow-up, and censoring assumptions.
- Check proportional hazards when interpreting a Cox hazard ratio as constant. Use time-varying effects or a different summary when it fails.
- Use cumulative incidence in the presence of competing events. Choose cause-specific or subdistribution hazards according to the estimand and state the interpretation.
- Report numbers at risk and absolute event probabilities at clinically meaningful times when estimable.
- Avoid treating discharge as non-informative censoring without justification.

## Repeated patients and episodes

- Count unique `subject_id` values and quantify patients with multiple admissions or ICU stays.
- For a single-episode estimand, make episode selection deterministic and report exclusions.
- For multiple episodes, preserve patient grouping in resampling and use cluster-robust variance, GEE, mixed models, recurrent-event methods, or frailty models as the question requires.
- Do not adjust only the standard error when within-patient dependence also changes the scientific estimand.

## Missing data

- Report missingness by variable, group, and clinically relevant time window; measurement intensity may itself be informative.
- Explain why complete-case analysis, missing indicators, inverse-probability methods, or multiple imputation is appropriate.
- Fit imputation inside the analysis or resampling boundary. Include variable type, nonlinear terms, interactions, clustering, and time ordering.
- Never use post-outcome or otherwise unavailable information to impute baseline variables.
- Combine estimates and uncertainty across multiply imputed data with an appropriate pooling rule.

## Multiplicity and sensitivity

- Identify one primary estimand when possible. Classify other outcomes, subgroups, interactions, and model variants.
- Control family-wise error or false discovery rate when confirmatory claims span multiple tests; otherwise label analyses exploratory and emphasize intervals.
- Pre-specify sensitivity analyses that target plausible biases rather than enumerating every model combination.
- Include negative, null, and inconsistent sensitivity results in the final report.

## Standard artifacts

Save or identify:

- analysis-ready data schema and cohort checksum or version;
- executable analysis code and environment/version record;
- Table 1 and missingness table;
- primary estimate table with denominators and confidence intervals;
- diagnostic outputs;
- sensitivity-analysis table;
- figure source data and generation code;
- deviation log linking departures to rationale and timing.
