# Target-trial emulation manuscript route

Apply the common manuscript quality contract and draft only from the frozen target-trial protocol, codebook, reviewed analysis, and versioned result artifacts. Describe the study as an observational target-trial emulation. Observed treatment allocation is not randomized, and the manuscript must not imply otherwise.

## Required frozen evidence

- Confirm that the frozen causal subtype is target trial, then name the target population, treatment strategies, causal contrast, estimand, analysis unit, and inference unit.
- Retrieve the complete named time contract, including eligibility, assignment, exposure, follow-up, censoring, and outcome times; do not collapse these into an ambiguous time zero.
- Retrieve the prespecified confounder set, treatment and censoring models, analysis specification, protocol deviations, diagnostics, sensitivity analyses, and reviewed result versions.
- Record which optional design components were actually frozen and used. Report a grace period, cloning, artificial censoring, inverse-probability weighting, weight truncation, or other adjustment only when supported by those artifacts.
- Leave an explicit unresolved-evidence placeholder rather than inventing a conventional method, diagnostic, or result.

## Ideal target trial versus observational emulation

Require a side-by-side mapping in the manuscript or supplement. Each cell must reflect the frozen protocol and implemented emulation, including departures and their consequences.

| Component | Ideal target trial protocol | Observational emulation |
| --- | --- | --- |
| Eligibility | Define who would be eligible and when eligibility is assessed. | State the operational criteria, data availability, exclusions, and eligible analysis unit. |
| Strategies | Define the treatment and comparator strategies, including permitted initiation or adherence. | State how observed records instantiate each strategy without using future information at baseline. |
| Assignment | Specify the randomized assignment procedure for the ideal trial. | Explain how observed allocation was classified and controlled; state that it was not randomized. |
| Time zero | Align eligibility, strategy assignment, and start of follow-up. | Name the corresponding observed times and disclose any misalignment or required design remedy. |
| Follow-up | Define its start, end, censoring events, and competing events. | State the implemented follow-up and censoring rules using the same origin across strategies. |
| Outcome | Define the endpoint, ascertainment, and horizon. | Give the operational definition, measurement source, timing, and available coverage. |
| Causal contrast | Define the treatment-strategy contrast and target population. | Name the estimated contrast and any change caused by adherence, censoring, or data restrictions. |
| Assumptions | State the ideal trial conditions and causal assumptions needed for the contrast. | State consistency, exchangeability, positivity, interference, measurement, and censoring assumptions as applicable. |
| Analysis | Prespecify the estimator and inference for the ideal protocol. | Report the estimator, nuisance models, repeated-unit handling, uncertainty, and diagnostics actually used. |

## Methods

- Identify the design explicitly as an observational emulation and distinguish the ideal protocol from its implementation in routinely collected data.
- Define eligibility time, treatment-assignment time, exposure period, follow-up start, censoring time, outcome time, and the ordering of baseline confounders. Do not adjust for post-treatment mediators or colliders as baseline covariates.
- If the frozen strategies allow a grace period, explain its duration, when follow-up begins, how strategy compatibility is assessed, and how immortal time is avoided. If conditioning on survival through the grace period changed the population or estimand, state that change.
- If cloning, artificial censoring, or weighting was used, report clone creation, deviation and censoring rules, treatment and censoring weight models, stabilization or truncation, and variance estimation. Do not mention these procedures as performed when the frozen analysis did not use them.
- Describe measured-confounding control, outcome modeling, censoring, competing events, missing data, repeated eligible trials or records, and inference exactly as implemented.
- Identify every protocol deviation and analysis change, when it occurred, and whether it changes the target population, strategy, estimand, or interpretation.

## Results and diagnostics

- Report flow from eligibility through assignment, follow-up, censoring, and analysis, with strategy-specific denominators, outcomes, follow-up, and applicable unique-patient counts.
- Report balance, propensity-score or covariate overlap, positivity, extreme weights, truncation, and effective sample size when those diagnostics apply to the performed estimator. Preserve poor balance, limited overlap, or unstable weights.
- Report strategy deviation and censoring patterns, including informative-censoring diagnostics, only when evaluated; otherwise mark the evidence gap rather than claiming censoring assumptions were satisfied.
- Report the prespecified absolute and relative effects with uncertainty and their time horizon when available in frozen results. If a required effect scale is absent, flag it as unresolved rather than derive or invent it during drafting.
- Report performed sensitivity analyses for unmeasured confounding, definitions, grace-period choices, censoring, weights, model specification, or other frozen uncertainties. Keep primary and sensitivity estimates distinct.

## Tables and figures

- Include the ideal-protocol-versus-emulation mapping and a cohort or eligible-trial flow display with aligned time definitions.
- Show strategy-specific baseline description and balance using the diagnostics appropriate to the performed analysis; do not use baseline significance tests as evidence of balance.
- When supported, show overlap, weight distributions and effective sample size, censoring, cumulative incidence or survival, and absolute and relative effects with intervals. Label the population, estimand, horizon, and analysis version in every display.
- Keep protocol deviations, sensitivity analyses, and failed diagnostics visible when they are necessary to interpret the primary estimate.

## Discussion, assumptions, and claim boundaries

- Interpret the magnitude and uncertainty of the frozen causal contrast in its target population before discussing statistical significance.
- State why exchangeability, consistency, positivity, interference, measurement, and censoring assumptions may or may not be plausible; balance and model diagnostics do not prove these assumptions or eliminate residual confounding.
- Explain how departures from the ideal target trial, limited overlap, measurement error, selection, missingness, and single-center data constrain the estimate and its transportability without guessing the direction of bias.
- Use TARGET only when the study falls within its formal scope. TARGET does not absorb or replace design-specific reporting for instrumental variables, regression discontinuity, difference-in-differences, or interrupted time series.
- Calibrate causal language to the frozen identification strategy and review status. An observational emulation remains observational and must not be described as a randomized study.

## Completion checks

- The frozen subtype is target trial, and the ideal protocol and observational emulation are mapped side by side for eligibility, strategies, assignment, time zero, follow-up, outcome, causal contrast, assumptions, and analysis.
- Assignment and follow-up share a defensible time origin; grace-period handling does not create immortal time, and any estimand change is explicit.
- Cloning, censoring, weights, diagnostics, and sensitivity analyses appear only when frozen and performed; missing evidence remains visible.
- Balance, positivity, effective sample size, censoring, and absolute and relative effects are reported when supported and reconciled across text and displays.
- The manuscript never calls observed allocation randomized, never uses TARGET for another causal subtype, and never claims diagnostics prove identification assumptions.
- Every method, result, diagnostic, and claim is traceable to frozen upstream evidence.
