# Validation and transportability overlay

Apply this optional overlay after the common manuscript contract and the selected primary design reference. Use it only when frozen upstream artifacts contain an assessed, applicable validation or transportability analysis, or when the manuscript makes such a claim. It supplements rather than selects or replaces the primary design route, and it defers design-specific methods and metrics to that route.

## When this overlay applies

- Identify the exact claim that needs evaluation: performance of a model, replication of an association, assignment or structural replication of a phenotype, or transport of a defined quantity to a target population or setting.
- Require a reviewed validation plan and versioned evidence before drafting a positive validation or transportability claim. If the analysis was not applicable, not performed, or not assessable from the supplied artifacts, report that status and its rationale.
- Keep development, locked evaluation, replication, transportability assessment, and updating as separate stages. Do not infer a stronger stage from the name of a dataset, a different calendar period, a different hospital, or a similar result.

## Classify the evidence

Assign each reported analysis to one of the following classes from its actual development--evaluation relationship:

| Evidence class | Required interpretation |
| --- | --- |
| **Internal validation** | Resampling, bootstrap, cross-validation, or a participant-level holdout within the development source evaluates optimism or stability of the development procedure. A random participant split is not external validation. |
| **Temporal or geographic within-development evaluation** | A later period, site, or region is held out but remains inside the planned development program or can influence selection, tuning, calibration, thresholds, or specification. Report the time or place separation without upgrading it to independent external validation. |
| **Internal-external validation** | Development is repeated across defined clusters such as sites, systems, or periods while each cluster is held out in turn. It assesses heterogeneity across clusters represented in the development collection; it is distinct from both ordinary internal validation and independent external validation. |
| **Independent external validation** | An unchanged, frozen object and intended-use contract are evaluated in an independently eligible population that did not contribute to fitting, preprocessing, selection, tuning, calibration, threshold choice, or the decision to report the object. Independence and provenance must be demonstrated, not assumed from a dataset label. |
| **Association replication** | A prespecified exposure--outcome association, effect measure, direction, and analysis specification are re-estimated in a separately defined population using mapped definitions. Replication does not validate a prediction model or convert an association into a causal effect. |
| **Phenotype assignment evaluation** | Frozen preprocessing, centroids or other learned representation, labels, and the assignment rule are applied unchanged to eligible records. Report assignment coverage, ambiguity, and the prespecified phenotype claims assessed. |
| **Phenotype structural replication** | A new population is re-clustered under a prespecified comparison to ask whether a comparable structure appears. Re-clustering and finding similar-looking groups is not validation of the original assignment rule. |
| **Transportability assessment** | A source population, target population or setting, transported quantity, and assumptions are defined, then population and measurement differences and any selection or transport adjustment are assessed. External evaluation alone does not establish transportability to every target. |

When an analysis combines classes, name each stage and its evidence separately. Do not use a generic `validated` label that hides which class was performed.

## Frozen object and data relationship

- Before locked evaluation, identify the evaluated object and its frozen version or hash: the complete model, preprocessing pipeline, feature and outcome definitions, coefficients or parameters, centroid or prototype, assignment rule, decision threshold, and any postprocessing required by the selected design. Freeze only the elements that are applicable; do not invent absent components.
- Record the relationship of every development and evaluation population: source and version, institution or system, collection period, eligibility, analysis unit, participant overlap, grouping boundary, and chronology.
- State whether evaluation records or their summaries influenced preprocessing, feature selection, model or cluster selection, tuning, calibration, threshold choice, phenotype naming, association specification, or the decision to update. Any such use belongs to development or updating, not the preceding locked evaluation.
- Preserve a versioned evaluation plan that names the primary claims, estimands or performance questions, uncertainty method, subgroup and sensitivity status, and decision rules for any update before evaluation results are inspected.
- If the development--evaluation relationship is missing, or the relevant frozen transform, model, centroid, or assignment rule cannot be verified, mark the validation claim `not assessed`. Do not reconstruct independence or freezing from narrative implication.

## Cohort, variable, and measurement mapping

- Map each eligibility criterion and cohort-flow step from the development population to the evaluation or target population. Label each item as aligned, modified with rationale, unavailable, or not comparable, and report the resulting population difference.
- Map every required predictor, exposure, outcome, confounder, phenotype input, and assignment input. Record source field, definition, unit, coding, time origin and window, aggregation, missingness, permissible proxy, and transformation.
- Distinguish semantic availability from measurement comparability. The same variable name can differ in assay, device, sampling frequency, clinical workflow, coding practice, adjudication, or observation opportunity.
- Report unresolved mappings and deviations visibly. Do not silently drop an unmapped variable, substitute an outcome-adjacent proxy, or refit a frozen preprocessing step to conceal incompatibility.
- Characterize population shift and measurement shift separately, including changes in case mix, prevalence or baseline risk, care setting and practice, event ascertainment, measurement frequency, missingness, and follow-up as applicable.

## Performance, replication, updating, and shift

- Use the selected primary design reference to choose the appropriate estimands, metrics, diagnostics, and uncertainty. This overlay governs stage labels, evidence relationships, mappings, and claim strength rather than duplicating design-specific analysis rules.
- Present the locked, pure evaluation first. Preserve its full result, including null, unfavorable, imprecise, or failed findings, before showing any recalibration, refitting, relabeling, threshold change, feature change, centroid change, or assignment-rule change.
- Prespecify whether updating is prohibited, optional, or triggered by an explicit criterion. For every update, state which evaluation information was used, what changed, what data were used to estimate the change, and which later population evaluates the updated object.
- Label updated performance or fit as post-update evidence. It does not replace the pre-update evaluation and must not be described as pure evaluation of the original object.
- For association replication, report the prespecified direction and effect scale, estimate with uncertainty, definition differences, and heterogeneity evidence. Similar statistical significance alone is not replication, and disagreement should not be hidden by a post hoc specification change.
- For phenotype work, distinguish performance of the frozen assignment rule from structural replication by re-clustering. If preprocessing, centroids, prototypes, labels, or thresholds are relearned, label the result updating or redevelopment.
- Interpret performance or replication alongside documented population and measurement shift. A change can reflect case mix, baseline risk, clinical practice, measurement, mapping, or analysis differences; do not attribute it automatically to failure or success of the original object.
- For transportability, name the target population and transported quantity, state the assumptions and overlap evidence, and report any selection or transport adjustment separately from unadjusted evaluation.

## Tables and figures

- Provide a development--evaluation relationship table showing population roles, source versions, sites or systems, periods, participant overlap, chronology, and every use in fitting, selection, tuning, calibration, assignment, or updating.
- Provide cohort and variable-mapping tables with aligned definitions, deviations, units, time windows, measurement methods, missingness, proxies, and unresolved items.
- Show population flow separately for development, locked evaluation, updating, and evaluation of an updated object. Label every denominator and analysis stage.
- Summarize population shift and measurement shift in a dedicated display or clearly labeled table rather than burying them in a single baseline comparison.
- Separate pure-evaluation results from post-update results in table sections or figure panels. Identify the frozen object version, population, claim or estimand, uncertainty, and applicable mapping limitations in each display.
- For phenotype analyses, use distinct displays for frozen-rule assignment and re-clustered structural replication so visual similarity cannot imply validation of the original assignment.

## Claim boundaries and completion checks

- The manuscript names the evidence class rather than using an unqualified validation label.
- The development--evaluation relationship, independence boundary, chronology, and participant or cluster overlap are explicit.
- The relevant model, preprocessing pipeline, centroid, prototype, threshold, or assignment rule was frozen before locked evaluation and is traceable to reviewed artifacts.
- Cohort, variable, outcome, time-window, unit, proxy, and measurement mappings are reported with unresolved items and deviations.
- Population shift and measurement shift are assessed separately and connected to interpretation.
- Pure evaluation appears before and separately from updating; update eligibility, triggers, inputs, changes, and later evaluation are prespecified and visible.
- Random participant splitting is reported as internal validation, not external validation.
- Temporal or geographic separation within the development program is not promoted automatically to independent external validation, and internal-external validation is named separately.
- Association replication, phenotype assignment evaluation, phenotype structural replication, independent external validation, and transportability assessment are not treated as interchangeable.
- Re-clustering similar groups is not validation of the original phenotype assignment rule; changed centroids, preprocessing, labels, or rules are updating or redevelopment.
- Missing relationship or frozen-transform evidence leaves the validation claim `not assessed`, not inferred or upgraded.
- Every classification, mapping, method, result, table, figure, and claim is traceable to frozen upstream evidence; unavailable evidence remains a visible source placeholder.
