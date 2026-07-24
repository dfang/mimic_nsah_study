# Prediction manuscript route

Apply the common manuscript quality contract, the shared prediction sections, and exactly one diagnostic or prognostic subsection named in the frozen study manifest. Ignore the sibling subtype subsection. Route by the prediction target and time contract, not by algorithm. Draft only from the frozen protocol, model specification, reviewed analysis, and versioned evaluation artifacts; leave the minimum inline source placeholder rather than inventing a method, threshold, metric, or result, and keep full source bookkeeping in the authoring records.

## Shared prediction evidence

- State the intended use, intended user, setting, eligible population, prediction target, output, decision point, and anticipated consequence from the frozen artifacts.
- Identify source versions, analysis unit, patient grouping, sample size, unique-patient count, outcome count, prevalence or incidence, missingness, and the complete predictor-to-target time contract.
- Name the frozen model or index-test version and distinguish candidate development, final model fitting, threshold selection, internal validation, external validation, and updating wherever each occurred.
- Report preprocessing, feature selection, tuning, calibration, and threshold selection only as performed. State which data or resampling boundary contained each data-dependent step.
- Preserve all reviewed comparators, subgroup analyses, diagnostics, uncertainty, and negative results. Trace each quantitative statement and display to a frozen artifact.

## Diagnostic prediction

Use this subsection for a model or index test intended to identify a condition at the diagnostic index time.

- Define the intended diagnostic use and population, the index test or model, the target condition, and the reference standard. Explain who applied or adjudicated the reference standard and how indeterminate reference-standard results were handled.
- State the timing of index-test inputs, index-test output, and reference-standard ascertainment relative to the diagnostic index time. Do not silently use information that would be unavailable at intended use.
- Report blinding between index-test interpretation and reference-standard assessment exactly as performed. If blinding evidence is unavailable, mark it unresolved rather than assuming independence.
- Report the diagnostic-population denominator, target-condition prevalence, verified and unverified cases when applicable, exclusions, and indeterminate index-test or reference-standard results. Describe any reviewed handling of partial or differential verification.
- Report threshold-specific sensitivity, specificity, predictive values, likelihood ratios, or other performed accuracy measures with intervals and the denominator for each threshold when applicable, performed, frozen, and available. When probabilities are produced, also report calibration evidence that was evaluated. If a metric is applicable and material to the intended diagnostic claim but was not performed, frozen, or available, record a material evidence gap; if it is genuinely not applicable, record `not_applicable` with the frozen rationale.
- Explain the clinical consequences of false-positive, false-negative, and indeterminate results for the intended use. Accuracy alone does not demonstrate clinical utility or improved outcomes.
- Keep development performance and optimism-corrected or resampled internal validation distinct from evaluation in an eligible external diagnostic population.

## Prognostic prediction

Use this subsection for a model that estimates the risk of a future outcome among people eligible and at risk at a defined prediction time.

- Define cohort eligibility time, prediction landmark, prediction horizon, target outcome, intended decision, and the risk set at the landmark. Report how people with the outcome, death, discharge, transfer, or insufficient observation before the landmark were handled.
- End the predictor-availability window at or before the landmark and identify the cutoff explicitly. Do not describe post-landmark measurements as predictors available for the stated decision.
- Define follow-up from landmark to horizon and report the frozen censoring strategy, loss to follow-up assumptions, and handling of competing events. Do not relabel a competing event as non-informative censoring without the reviewed analysis's justification.
- Report outcome events or cumulative incidence with the applicable risk-set denominator and numbers at risk when supported by the frozen artifacts.
- Compare the model with clinically meaningful baseline comparators that were frozen and evaluated; do not substitute an algorithm-only comparison for the intended-use question.
- Report discrimination, calibration, and an overall probabilistic performance measure with intervals when performed. Add horizon- or prevalence-sensitive measures only when they are appropriate to the frozen target and analysis, were performed and frozen, and are available in the reviewed artifacts. If such a measure is applicable and material to the intended prognostic claim but was not performed, frozen, or available, record a material evidence gap; if it is genuinely not applicable, record `not_applicable` with the frozen rationale. Do not invent or derive a metric during authoring.
- Report utility only when the reviewed artifacts evaluate decision consequences against relevant alternatives. Include subgroup and fairness results with group denominators, event counts, missingness, uncertainty, and the performance or decision measure actually assessed.
- Classify a temporal split by its actual development--evaluation relationship, not categorically by source name. A split that remains part of development, selection, tuning, calibration, threshold choice, or reporting decisions is internal or within-development evaluation. A later-period population may retain its frozen reviewed temporal-external label only when the complete model and intended-use contract were locked before evaluation and the validation overlay demonstrates independence and non-use. Keep any updating separate from the locked evaluation, and do not infer transportability from temporal separation alone.

## Performance, calibration, utility, and fairness displays

- For every performance display, identify the model version, population, validation stage, denominator, event count or prevalence/incidence, uncertainty method, and whether any threshold was selected or prespecified.
- Pair discrimination with calibration when risk probabilities are claimed. A receiver-operating-characteristic curve, area under that curve, or accuracy value alone does not establish calibrated risk.
- Show calibration with the assessed intercept or calibration-in-the-large, slope, curve, and relevant risk ranges when available; do not infer calibration from discrimination.
- For diagnostic prediction, give every performed discrimination analysis a named display, then present threshold-specific classification results and intervals with reference-standard status and prevalence. Make the consequences of false positives and false negatives interpretable for the intended diagnostic use.
- For prognostic prediction, preserve the landmark, horizon, risk set, censoring, and competing-event estimand in tables and figures; include numbers at risk or horizon-specific denominators when applicable.
- Label decision-curve, net-benefit, cost, impact, or other utility evidence by its assumptions and comparators. Accuracy, discrimination, or calibration alone is not evidence of clinical utility.
- For subgroup or fairness displays, report group definitions, denominators, event counts, missingness, performance, calibration or decision consequences, and uncertainty. Do not declare equivalence, disparity, or fairness from unstable point estimates alone.

## Validation labels and claim boundaries

- **Development** describes fitting, feature selection, tuning, calibration, or threshold selection. Apparent performance on development data is not validation.
- **Internal validation** evaluates the complete development process using resampling, held-out partitions, or a reviewed within-source design while preserving patient grouping and training boundaries. It estimates internal optimism or stability; it is not external validation.
- **External validation** evaluates a frozen model and intended-use contract in an independently eligible evaluation population under the reviewed validation plan. A random split, cross-validation, or bootstrap is not external validation. A later-period population is temporal-external only when the complete object and intended-use contract were locked before evaluation and the validation overlay demonstrates independence and non-use; otherwise it is internal or temporal within-development evaluation.
- **Updating** includes refitting, recalibration, coefficient revision, new predictors, or threshold changes for a new setting. Report the external evaluation before updating when available and label post-update performance separately; updating is not pure external validation.
- Calibrate every claim to the strongest completed stage. Internal validation does not establish transportability, and external accuracy alone does not establish clinical utility, workflow benefit, safety, or patient benefit.
- Keep diagnostic accuracy claims tied to the reference standard, index time, spectrum, prevalence, and threshold. Keep prognostic claims tied to the landmark, horizon, risk set, censoring, competing events, and intended decision.

## Completion checks

- The diagnostic or prognostic subtype matches the frozen target and time contract; the two timing structures are not blended.
- Diagnostic reporting names intended use, index test or model, reference standard, timing, blinding, prevalence, indeterminate cases, threshold-specific accuracy with intervals, and error consequences where supported.
- Prognostic reporting names eligibility time, landmark, horizon, risk set, predictor cutoff, censoring, competing events, baseline comparators, calibration, overall performance, utility status, and subgroup or fairness denominators where supported. Horizon- or prevalence-sensitive measures appear only when appropriate, performed, frozen, and available; an applicable claim-critical omission is a material evidence gap, while genuine non-applicability retains its frozen `not_applicable` rationale.
- Development, internal validation, external validation, and updating are labeled separately and agree with the reviewed artifacts.
- No claim infers clinical utility from accuracy or transportability from internal validation.
- Every method, metric, threshold, result, and claim is traceable to frozen upstream evidence; unresolved evidence remains an explicit placeholder.
