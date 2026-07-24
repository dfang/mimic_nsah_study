# Phenotyping manuscript route

Apply the common manuscript quality contract and draft only from the frozen protocol, discovery specification, reviewed analysis, and versioned result artifacts. Keep discovery, internal stability, clinical characterization, downstream analyses, replication, assignment, and external validation as distinct stages in the text and displays. Leave an explicit source placeholder when evidence for a required stage is absent.

## Frozen discovery contract

- State the discovery population, analysis unit, patient-grouping rule, cohort entry, feature-window start and end, and the point after which downstream follow-up begins. Do not use measurements that occur after the frozen feature window to define a phenotype.
- Classify every variable by its frozen role: clustering input, preprocessing or technical variable, clinical characterization variable, downstream outcome or treatment-response variable, or assignment-only input. A variable cannot silently move from a downstream role into solution discovery.
- Report the frozen missingness thresholds, exclusions, imputation method and fit boundary, missingness indicators, scaling, transformations, correlation handling, and any dimensionality reduction. Distinguish choices made before discovery from deviations made after results were known.
- Name the algorithm, distance or likelihood definition, hyperparameters, software implementation, random seeds, candidate cluster-number criteria, minimum-size rule, stability plan, clinical-coherence rule, phenotype naming rule, and the rule for choosing the final solution.
- Define the assignment rule that maps a new eligible record to a frozen phenotype, including the required inputs and preprocessing, learned parameters or prototypes, handling of missing or out-of-range values, ambiguous assignments, and records that cannot be assigned.
- Record when investigators first inspected downstream outcomes. If an outcome, treatment response, or future measurement influenced the selected cluster number or final solution, label the analysis as the corresponding supervised or nested design; do not describe it as pure unsupervised discovery.

## Solution selection without downstream outcomes

- Select the cluster number and final solution using only the frozen unsupervised criteria, resampling stability, minimum-size rule, and prespecified clinical-coherence assessment. Preserve the actual evidence for each candidate rather than presenting the selected solution alone.
- Keep downstream outcomes, treatment responses, and future measurements hidden from cluster-number selection, algorithm or hyperparameter choice, candidate-solution ranking, label merging, and the decision to retain or discard a phenotype.
- Distinguish exploratory candidate generation from selection of the frozen solution and report any protocol deviation or post hoc choice. A clinically recognizable outcome gradient is not an unsupervised selection criterion.
- When supervised information was used within a nested design, report the supervised selection target, the nesting or holdout boundary, and the evaluation stage explicitly. Do not recover an unsupervised label merely because the clustering step itself omitted the outcome column.

## Stability and uncertainty

- Report random-seed repetition, bootstrap, subsampling, or consensus procedures exactly as performed, with resampling grouped at the highest unit needed to preserve patient dependence.
- For each candidate and selected phenotype, report supported membership stability, solution reproducibility, cluster size, assignment ambiguity or probability, and sensitivity to preprocessing or algorithm choices. Do not hide an unstable or very small phenotype behind a clinical name.
- Keep stability distinct from clinical characterization and downstream association. Internal resampling describes uncertainty in the discovery process; it is not replication or external validation.
- State whether uncertainty was propagated into downstream analyses or whether hard assignments were treated as fixed, and describe the resulting limitation without inventing an unperformed correction.

## Clinical characterization

- Characterize the frozen phenotypes with standardized input profiles, non-input clinical variables, missingness patterns, and measurement opportunity supported by the reviewed artifacts. Preserve denominators, units, uncertainty, and the feature window.
- Treat clustering inputs as the coordinates that created the groups, not as independent discoveries that validate or explain them. Differences in those inputs are descriptive properties of the fitted solution.
- Apply the frozen naming rule only after reviewing the complete profile. Use neutral labels when a phenotype is unstable, heterogeneous, or not clinically specific; do not turn an algorithmic group into a disease entity.
- Keep variables reserved for characterization out of solution selection. If characterization prompted merging, relabeling, or choosing a different solution, disclose the post hoc change and its consequences for the discovery claim.

## Downstream association or prognostic validity

- Begin downstream follow-up after the frozen feature window and define the outcome, treatment response, time origin, horizon, censoring or competing events, denominator, adjustment set, and uncertainty from the reviewed analysis.
- Present downstream outcome differences as characterization or association unless a separate prognostic or causal design supports a stronger claim. Report absolute quantities and adjusted estimates only when available in frozen artifacts.
- Keep primary, secondary, subgroup, treatment-response, sensitivity, and exploratory analyses distinct. Report multiplicity handling and negative, null, imprecise, or adverse findings as performed.
- Do not use downstream performance or association strength to retroactively justify the selected cluster number, rename a phenotype, or declare the solution stable. Outcome-guided selection requires the honest supervised or nested label described above.

## Replication, assignment, and external validation

- **Replication** asks whether an independently analyzed population yields a comparable unsupervised structure under a prespecified comparison. Report differences in eligibility, features, preprocessing, cluster number, matching criteria, and uncertainty; similar clusters alone do not validate the original assignment rule.
- **Assignment evaluation** applies the frozen preprocessing and assignment rule to eligible records without re-clustering, relearning prototypes, changing thresholds, or renaming phenotypes. Report coverage, unassigned records, ambiguity, distribution shift, phenotype sizes, and the performance of the frozen rule.
- **Genuine external validation** evaluates the frozen assignment rule and prespecified phenotype claims in an independently eligible external population under a reviewed validation plan. Separate validation of assignment, phenotype characterization, and downstream association or prognosis.
- Re-clustering another dataset can support structural replication, but it does not validate how the original frozen assignment rule classifies new records. Refitting preprocessing, prototypes, labels, or thresholds is updating or redevelopment and must be reported separately from pure external validation.
- Agreement between cluster membership and a severity score measured in the same cohort is within-cohort characterization or convergent evidence, not external validation. A random, resampled, or temporal partition from the same source is also not automatically external validation.
- If no eligible external population was evaluated, state that external validation was not performed and limit transportability claims accordingly; do not substitute internal stability, score agreement, or replication by re-clustering.

## Tables and figures

- Show discovery and analysis flow with population, exclusions, feature-window timing, patient grouping, discovery partitions, assignment evaluation, replication, and external-validation populations where applicable.
- Summarize variable roles, preprocessing, candidate-solution criteria, minimum sizes, stability evidence, and the frozen selection decision in traceable tables or displays.
- Present phenotype profiles with consistent scales, denominators, missingness, and uncertainty. Visually distinguish clustering inputs from characterization variables and downstream outcomes.
- Present downstream associations or prognostic results separately from discovery and stability evidence. Label every panel by population and stage so internal characterization cannot be mistaken for validation.
- For replication or external validation, show the frozen rule, eligibility, mapping or assignment coverage, distribution shift, unassigned or ambiguous records, and prespecified comparison evidence supported by the artifacts.

## Claim boundaries and completion checks

- Feature windows, variable roles, missingness handling, scaling, transformations, algorithm, random seeds, cluster-number criteria, stability plan, minimum-size rule, clinical-coherence rule, naming rule, and assignment rule match the frozen reviewed artifacts.
- The cluster number and final unsupervised solution were selected without downstream outcomes, treatment responses, or future measurements. Any outcome-guided selection is labeled and evaluated as the corresponding supervised or nested design.
- Discovery, internal stability, clinical characterization, downstream association or prognosis, replication, assignment evaluation, updating, and genuine external validation are named separately and agree with what was performed.
- Clustering inputs are not presented as independently rediscovered findings, and phenotype names do not imply a verified disease entity.
- Within-cohort agreement with a severity score is not called external validation, and re-clustering another dataset is not called validation of the frozen assignment rule.
- Every method, candidate decision, number, display, and claim is traceable to frozen upstream evidence; missing evidence remains an explicit placeholder rather than an invented method or result.
