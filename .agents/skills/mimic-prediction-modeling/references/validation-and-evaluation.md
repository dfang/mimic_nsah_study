# Prediction Validation and Evaluation Rules

## Temporal design

- Define the prediction landmark independently from cohort entry. Include only patients who are eligible and at risk at that landmark.
- End every predictor window no later than the landmark. Start the outcome window after the landmark unless the diagnostic target is explicitly contemporaneous.
- Handle early death, discharge, transfer, and insufficient follow-up explicitly; report their counts and the population to which the model applies.
- Avoid random splitting when the intended test is temporal transport; use an earlier development period and a later evaluation period.

## Patient-level partitioning

- Generate partitions from unique `subject_id` values, then join assignments back to admissions or stays.
- Preserve patient grouping in every cross-validation, bootstrap, calibration, and threshold-selection step.
- Fit all data-dependent preprocessing inside training folds.
- Keep a final evaluation set untouched when one is declared. If the sample cannot support this, use resampling and state that no independent holdout estimate exists.

## Internal validation

- Prefer bootstrap optimism correction for a prespecified model-development process and adequate repeated resampling.
- Use nested cross-validation when algorithm or hyperparameter selection occurs; the outer loop estimates performance and the inner loop selects settings.
- Repeat split-based procedures when instability is material and report the distribution of results.
- Include the entire modeling process, including variable selection and tuning, in resampling.

## Performance

- Report sample size, unique patients, outcome events, prevalence or incidence, and confidence intervals.
- Discrimination: AUROC and, for imbalanced outcomes, AUPRC with the event prevalence as context.
- Calibration: calibration-in-the-large or intercept, slope, flexible calibration curve, and clinically relevant risk strata.
- Overall accuracy: Brier score or another proper scoring rule when appropriate.
- Clinical utility: decision-curve net benefit across defensible thresholds and comparison with treat-all, treat-none, and clinical baselines.
- Do not choose a threshold from the final evaluation set. Report the consequence of false positives and false negatives.

## Fairness and subgroup evaluation

- Predefine groups that matter for intended use, data quality, or known health inequities.
- Report group size, events, missingness, discrimination, calibration, and decision consequences with uncertainty.
- Treat small groups as uncertain rather than declaring equivalence or disparity from unstable point estimates.
- Distinguish measurement bias, representation, model performance, and downstream policy effects.

## Freezing and external use

Freeze and version:

- cohort and outcome definition;
- landmark, horizon, and predictor windows;
- feature names, order, units, and allowed missingness;
- preprocessing and imputation objects;
- model coefficients or serialized estimator;
- calibration and decision thresholds;
- software environment and deterministic prediction entry point.

Do not refit, recalibrate, or redefine predictors during external validation without labeling the result as model updating rather than pure validation.
