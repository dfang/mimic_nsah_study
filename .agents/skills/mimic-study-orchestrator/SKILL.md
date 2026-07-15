---
name: mimic-study-orchestrator
description: Coordinate a MIMIC clinical study from question and protocol through codebook, cohort, features, analysis, review, manuscript, and submission. Use for end-to-end study execution, resuming an existing MIMIC project, checking stage readiness, creating a study manifest, freezing analysis artifacts, or deciding which MIMIC skill must run next.
---

# MIMIC Study Orchestrator

Coordinate the study; do not replace specialist skills. Preserve a traceable chain from the research question to every reported number.

## Start with the governance gate

Apply `mimic-data-governance` before reading workspace research files or restricted data. If that skill is unavailable, do not send MIMIC patient-level data, notes, images, derived datasets, model weights, or sensitive small-cell outputs to an external service unless institutional use is allowed and input, output, logs, caches, backups, and subprocessors are verified for zero retention, no training, and no human review. Prefer local processing. Stop before reading restricted material when compliance is unclear.

## Load or create the manifest

Use `assets/study-manifest.yaml` as the canonical state record. Copy it into the study repository; do not edit the asset in this skill. Manifest v2 represents one primary scientific question; use separate manifests plus a project-level index for multiple primary questions. Record paths and hashes rather than embedding patient data.

Preserve the manifest's exact field names and shapes in every update or example. In particular, stage gates use `status`, not `state`; detailed gate evidence belongs in the referenced `artifact`, with its `sha256`, while `rationale` explains a `not_applicable` decision. Do not invent a parallel manifest schema in prose.

Before advancing, require explicit values for:

- question, scientific `design_family`, required `design_subtype`, association intent when applicable, data modalities, target population, estimand or prediction target;
- one `data.sources` record per source project/module, including release, actual schema, access date, and linkage provenance;
- structured analysis grain (`unit`, `key_columns`, and `repeat_structure`) and the complete time contract, using canonical `not_applicable` only where justified;
- primary/secondary outcomes and analysis plan status;
- artifact paths, code commit, environment, and review evidence.

Read `references/stage-contracts.md` when creating or auditing stage gates.

## Execute gated stages

Advance sequentially unless an earlier frozen artifact is already valid:

1. **Question and evidence** — use `mimic-research-topic-scout` and `mimic-literature-evidence`; reject low-value or infeasible topics.
2. **Protocol and SAP** — use `mimic-study-protocol-sap`; freeze objectives, estimand, time contract, outcomes, missingness, multiplicity, and sensitivity analyses before confirmatory execution. Require a target-trial specification only for `target_trial`; require the assignment mechanism, identifying assumptions, diagnostics, and reporting plan specific to `iv`, `rd`, `did`, or `its`.
3. **Concepts** — use `mimic-clinical-codebook` and `mimic-exposure-outcome-builder`; require versioned definitions, source/availability times, and clinical review.
4. **Cohort or risk set** — use `mimic-cohort-builder`; require cohort flow, analysis-grain/key checks, time alignment, and design-specific review.
5. **Features or analytic data** — use `mimic-derived-feature-extractor` plus domain skills; run `mimic-bigquery-qc` and record the verified derived schema plus `_metadata` or equivalent version evidence.
6. **Analysis** — route descriptive/association/regression/survival work to `mimic-statistical-analysis`, prediction to `mimic-prediction-modeling`, phenotyping to `mimic-phenotyping-pipeline`, and causal work to `mimic-causal-analysis-guardrails`. Do not route `iv`, `rd`, `did`, or `its` through target-trial-only gates.
7. **Validation, replication, or transportability** — use `mimic-external-validation` when genuine external data exist, and interpret the stage according to design family and subtype. Never call a random split external validation. A protocol scoped only to the current source with no external claim may use a hashed applicability assessment for `status: not_applicable`; when the protocol or claims require transportability, the assessment must also contain external-dataset search and mapping evidence. Record the assessment bundle path/hash and concise `rationale`.
8. **Independent analysis review** — use `mimic-review` on the frozen protocol, cohort, code, QC, analysis, and validation artifacts. A builder must not silently self-approve a blocking issue.
9. **Manuscript** — use `mimic-clinical-manuscript`; derive claims and numbers only from frozen, reviewed results.
10. **Independent manuscript review** — use `mimic-review`, including `journal-reviewer`, on the complete manuscript, tables, figures, supplement, and reporting-checklist mapping. Return blocking or major findings to the author and re-review the corrected version before freezing this gate.
11. **Reproducibility release** — use `mimic-reproducibility-release` after the manuscript review gate; keep public and restricted artifacts separate.
12. **Submission** — use `mimic-submission-packager`, then `mimic-manuscript-compiler` when a rendered PDF is required; verify live journal instructions before packaging and visually inspect the PDF.

## Enforce the time contract

Do not use one overloaded `T0`. Record, when applicable:

```text
eligibility_time
cohort_entry_time
index_time
feature_window_start
feature_window_end
prediction_landmark
target_ascertainment_window
reference_standard_time
treatment_assignment_time
exposure_end
followup_start
censoring_time
outcome_time
```

For a `0-24h` feature model, either set the decision landmark at 24 hours and define the population still eligible then, or use a valid dynamic design. Do not label post-entry measurements “baseline” without naming their relationship to the decision or assignment time.

## Gate decisions

Use only these states:

- `not_started`
- `in_progress`
- `blocked`
- `ready_for_review`
- `frozen`
- `not_applicable`
- `superseded`

Mark a stage `frozen` only when required inputs exist, acceptance checks pass, artifact hashes are recorded, and unresolved blocking findings are zero. Record every post-freeze change in the deviation log and supersede affected downstream artifacts.

Each stage `artifact` points to a bundle index whose hash is stored in the stage `sha256`. The bundle index records every member artifact's role, path, version, and hash. Do not put a single file path in `artifact` when the stage has multiple deliverables.

For prediction, use `diagnostic` or `prognostic`; for causal work, use `target_trial`, `iv`, `rd`, `did`, or `its`. `other_with_gate_plan` is allowed only when the protocol bundle contains a bespoke gate plan, diagnostics, reviewer, and stop/redesign criteria.

Use `not_applicable` only for a conditionally required stage after documenting why it does not apply and what evidence supports that decision. It is a terminal state, not a synonym for missing evidence or unfinished work.

## Report progress

Return:

- current stage and gate state;
- artifacts inspected or produced, with paths;
- blocking findings and missing evidence;
- next specialist skill and its exact required input;
- manifest fields updated;
- claims that remain not assessed.

Never claim end-to-end completion when a required stage is skipped, unverified, or based on unavailable restricted data.
