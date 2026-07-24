# Quasi-experimental causal manuscript routes

Apply the common manuscript quality contract, the shared causal section, exactly one IV, RD, DiD, or ITS subtype section named in the frozen study manifest, and the completion checks. Ignore every sibling subtype section. Draft only from the frozen identification contract, codebook, reviewed analysis, and versioned results; do not import another subtype's methods or invent missing diagnostics.

## Shared causal evidence and claim boundaries

- Name the frozen subtype, intervention or assignment mechanism, target population, analysis and inference units, complete time contract, causal estimand, estimator, assumptions, protocol deviations, and result versions.
- Report sample structure, treatment or exposure contrast, outcome, missingness, uncertainty, and only the diagnostics and sensitivity analyses that were performed and frozen.
- Treat identifying assumptions as substantive conditions supported by design knowledge and evidence, not facts proved by a diagnostic. Preserve failed, weak, null, heterogeneous, and imprecise findings.
- Among the subtype sections below, apply only the frozen subtype; the shared causal section and completion checks still apply. TARGET reporting is not a substitute for IV, RD, DiD, or ITS reporting.

## Instrumental variables

### Methods

- Define instrument construction, coding, timing, level of assignment, eligible population, exposure, outcome, follow-up, and whether the instrument can affect treatment before outcome ascertainment.
- State the actual instrument-specific estimand, such as a LATE for the population whose treatment is changed by the instrument under the frozen assumptions. Do not default to an ATE.
- Describe the first-stage and outcome estimators, included covariates, reduced-form analysis, inference unit, clustering or repeated-record handling, missing data, and weak-instrument-robust inference actually used.
- State the relevance, independence, exclusion-restriction, monotonicity, and treatment-version assumptions to the extent applicable, with the frozen clinical and institutional rationale for each.

### Results, diagnostics, and displays

- Report instrument and treatment distributions, analysis denominators, outcome events or follow-up, and the first-stage effect with uncertainty.
- Report the performed weak-instrument diagnostics, such as the relevant first-stage statistic or partial strength measure, and any instrument-level clustering. Do not substitute a conventional cutoff for the full first-stage evidence.
- Present the reduced-form estimate and the IV estimate with uncertainty and identify the estimator and estimand. Report overidentification, balance, falsification, alternative specifications, or weak-instrument-robust intervals only when performed.
- Show instrument-to-treatment, instrument-to-outcome, and IV effect evidence in separate, clearly labeled displays so diagnostics cannot be mistaken for proof of identification.

### Interpretation boundary

- Interpret the estimate as the actual LATE or other instrument-specific estimand for the population and treatment margin identified by this instrument, not automatically as a population ATE.
- First-stage strength and falsification diagnostics do not prove independence, exclusion, or monotonicity and do not remove all confounding. Discuss violations, treatment versions, instrument specificity, and transportability directly.

## Regression discontinuity

### Methods

- State whether the frozen design is sharp or fuzzy, define the running variable, assignment rule, cutoff, treatment, outcome timing, and the local estimand at the cutoff.
- Report bandwidth selection, kernel, polynomial or other functional form, side-specific trends, covariate adjustment, robust bias-corrected or other frozen inference, and clustering or repeated observations.
- Report which density or manipulation assessments, covariate-continuity checks, bandwidth and functional-form sensitivities, and donut or placebo analyses the frozen protocol prespecified, which were performed, and any deviations. Do not create planned-but-unperformed methods during authoring.

### Results, diagnostics, and displays

- Report observations and support on each side of the cutoff, the selected bandwidth, the outcome discontinuity with robust uncertainty, and the treatment discontinuity for fuzzy RD.
- Report density or manipulation and covariate-continuity evidence that was performed, plus bandwidth, kernel, functional-form, donut, or placebo sensitivity results when available.
- Plot the running variable against treatment and outcome with the cutoff, local fits, uncertainty, bins or raw support, and analysis bandwidth identified; do not let a global fit obscure the local comparison.

### Interpretation boundary

- Interpret a sharp RD as the local effect at the cutoff under continuity and no precise manipulation; interpret a fuzzy RD using its compliance-based local estimand and first-stage discontinuity.
- Keep the conclusion strictly local to units near the cutoff. Diagnostics inform continuity and manipulation concerns but do not prove the identifying assumptions or justify population-wide effects.

## Difference-in-differences

### Methods

- Define treated and comparison groups, treatment timing, outcome, observation periods, and whether the data are a panel or repeated cross-section; name the frozen ATT and target population.
- State parallel-trends, no-anticipation, and no-spillover assumptions, how composition and time-varying confounding were handled, and the clinical or policy rationale for the comparison group.
- Describe the estimator, reference period, covariates, inference unit, and clustered standard errors exactly as performed. Report a dynamic or event-study specification, staggered-adoption handling, and treatment-effect heterogeneity only when applicable and present in frozen/performed evidence. For a two-period design that cannot support an event study or a common intervention date with no staggered adoption, record the design-based inapplicability rationale and evidence status rather than inventing an analysis.

### Results, diagnostics, and displays

- Show raw group-specific outcome trends before adjusted estimates, with group-period denominators and the treatment date or cohort-specific adoption dates.
- Report the ATT with intervals, the reference period when applicable, and the clustering level. Report dynamic event-study estimates, event-time support, and heterogeneous effects only when applicable and available in frozen results; otherwise record the design-based applicability rationale and evidence status without inventing results. Preserve heterogeneous, delayed, adverse, null, or imprecise effects that were evaluated.
- Report pre-treatment coefficients, placebo timing or groups, alternative windows, composition checks, spillover analyses, and staggered-adoption sensitivity only when performed.

### Interpretation boundary

- Interpret the estimate for the treated groups, periods, and weighting induced by the frozen estimator; do not generalize beyond that support or average over heterogeneity without disclosure.
- A non-significant pretrend does not prove parallel trends. Limited power, anticipation, spillovers, concurrent changes, and composition shifts remain threats even when pre-treatment coefficients are imprecise. Interpret staggered-adoption or heterogeneous-effect evidence only when applicable and frozen/performed; otherwise give the design-based inapplicability rationale and evidence status without inventing evidence.

## Interrupted time series

### Methods

- Define the intervention point, series unit, outcome aggregation and frequency, pre-intervention and post-intervention observation counts, population composition, and any control series.
- Specify the segmented model, baseline trend, immediate level change, slope change, transition or lag structure, and effect scale actually estimated.
- Report treatment of seasonality, autocorrelation, nonlinearity, overdispersion, changing denominators, missing intervals, and inference. Identify concurrent interventions and secular changes from the frozen design assessment.
- Describe control-series analyses, placebo dates, alternative interruption points, lag choices, or other sensitivity analyses only when prespecified or performed.

### Results, diagnostics, and displays

- Report observed pre-intervention and post-intervention levels and slopes, estimated level and slope changes with uncertainty, and model-based effects at prespecified times when available.
- Show the full series with the intervention point, fitted segmented trajectory, counterfactual continuation, uncertainty, denominators, and any control series; do not replace it with aggregate pre/post bars.
- Report residual autocorrelation, seasonality, dispersion, influential points, model-fit evidence, control-series contrasts, and placebo-date results only when evaluated.

### Interpretation boundary

- Do not reduce ITS to a simple before-after comparison. Attribute a series-level change to the intervention only to the extent that the segmented design, assumptions, controls, and concurrent-change assessment support it.
- Do not translate an aggregate series-level level or slope change into an individual-level causal effect. Discuss concurrent interventions, history, composition, measurement, seasonality, and model dependence.

## Completion checks

- Exactly one frozen subtype route supplies the manuscript's identification contract, methods, diagnostics, estimand, displays, and claim boundary.
- IV reporting includes instrument construction and timing, first stage, weak-instrument evidence, reduced form, assumptions, inference, and the actual LATE or instrument-specific estimand without claiming that diagnostics prove assumptions.
- RD reporting preserves sharp or fuzzy design, cutoff, bandwidth, manipulation and continuity evidence, robust inference, treatment discontinuity when fuzzy, and local interpretation.
- DiD reporting includes raw trends, no anticipation, spillovers, clustered inference, and no claim that a non-significant pretrend proves parallel trends. It reports event studies, staggered-adoption handling, and heterogeneity only when applicable and frozen/performed; otherwise it records the design-based inapplicability rationale and evidence status without invented analyses or results.
- ITS reporting includes series structure, level and slope, seasonality, autocorrelation, concurrent changes, and full-series evidence; it is neither a simple before-after analysis nor an individual-level effect.
- Every method, diagnostic, estimate, display, and interpretation is traceable to frozen upstream evidence; unperformed optional checks are not presented as required results.
