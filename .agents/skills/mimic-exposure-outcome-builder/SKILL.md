---
name: mimic-exposure-outcome-builder
description: Define, implement, and audit reusable exposure and outcome variables for MIMIC-IV studies. Use for medications, fluids, procedures, devices, organ support, infections, laboratory or physiologic states, mortality, complications, readmission, duration endpoints, or composite outcomes that require source triangulation, clinical adjudication, temporal ordering, provenance, SQL quality control, and definition-sensitivity analyses. Use after the cohort and time origin are established and before statistical or prediction analysis.
---

# MIMIC Exposure and Outcome Builder

Convert clinical concepts into auditable, time-aligned variables without confusing orders with administrations, proxies with adjudicated events, or future information with baseline evidence.

Apply `mimic-data-governance` before reading patient-level events or adjudication samples. Keep raw evidence and discordant cases in the approved environment and publish only cleared definitions, code, and aggregate QC.

## Required definition contract

For every exposure and outcome, define:

- clinical meaning and intended analytic role;
- analysis unit and keys;
- eligibility, index, assignment or landmark, exposure, follow-up, and censoring times;
- source tables, codes or itemids, timestamp fields, units, and evidence priority;
- operational algorithm, allowable gaps, recurrence rule, and episode aggregation;
- expected failure modes, adjudication plan, and sensitivity definitions.

Copy [assets/exposure-outcome-spec-template.md](assets/exposure-outcome-spec-template.md) before writing production SQL. Keep exposure and outcome definitions versioned independently from the cohort.

## Workflow

1. **Write the clinical definition first.** Specify what counts, what does not count, and why the event is clinically meaningful. Label a database proxy as a proxy.
2. **Map evidence sources.** Read [references/definition-patterns.md](references/definition-patterns.md) for medications, procedures, devices, infections, duration measures, and composite outcomes. Use the clinical codebook for auditable ICD and itemid sets.
3. **Fix temporal ordering.** End baseline evidence before treatment assignment or the prediction landmark. Start outcomes from the declared follow-up origin. Do not classify treatment from future exposure without an explicit grace-period strategy.
4. **Implement at event grain.** Preserve raw source, code/itemid, label, event time, amount, unit, status, and cancellation or completion evidence. Normalize units and status before aggregating.
5. **Aggregate deterministically.** Collapse event evidence to the target patient, admission, stay, or episode grain before joining the cohort. Define first event, count, dose, duration, and component flags explicitly.
6. **Triangulate and adjudicate.** Compare independent sources when no single table is authoritative. Quantify concordant, discordant, and source-only cases; adjudicate a sample or all high-risk disagreements when feasible.
7. **Run QC.** Check source availability, matched labels, timestamp bounds, duplicate events, unit distributions, event rates, time-from-index distributions, impossible sequences, and join cardinality. Run `mimic-bigquery-qc` on production SQL.
8. **Test definition sensitivity.** Vary defensible windows, evidence requirements, status rules, code sets, or composite construction. Report how cohort counts and estimates change.
9. **Publish provenance.** Produce the completed specification, versioned code/codebook, source-concordance table, QC report, and final data dictionary.

## Hard gates

- Do not treat a prescription or order as administration without explicit justification.
- Do not infer a procedure or device exposure only from a diagnosis code when direct event evidence is required.
- Do not use post-exposure severity, monitoring, or treatment response as baseline evidence.
- Do not let an outcome component occur before follow-up starts.
- Do not hide disagreement between sources behind an `OR` rule without reporting concordance.
- Do not combine composite components with different clinical meaning or surveillance without reporting each component separately.
- Do not use a future event to define baseline exposure groups unless the design explicitly handles the resulting immortal time.

## Completion criteria

Finish only when the clinical and operational definitions agree, time ordering is valid, raw evidence remains traceable, target-grain uniqueness is verified, source disagreements and proxy limitations are reported, definition sensitivities are assessed, and downstream users receive a versioned data dictionary plus QC evidence.
