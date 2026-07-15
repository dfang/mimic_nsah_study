---
name: mimic-review
description: Run an independent, evidence-traceable audit of a MIMIC study, protocol, SQL pipeline, analysis, model, manuscript, or workspace. Use when users request comprehensive review, publication-readiness assessment, cross-disciplinary quality control, blocking-issue triage, or a consolidated clinical, statistical, SQL, reproducibility, and journal review.
---

# MIMIC Comprehensive Review

Act as a read-only audit gate. Do not modify research artifacts unless the user separately requests fixes. Do not duplicate specialist standards from memory; load and apply the current specialist skills.

## Gate workspace access

Apply `mimic-data-governance` before scanning or reading files. Do not open restricted patient-level tables, notes, images, derived datasets, model weights, or unsafe small-cell outputs in an unverified external environment.

If governance evidence is missing, restrict review to non-sensitive protocol, SQL text, schemas, aggregate-safe reports, and manuscript text. Mark excluded material `not assessed`.

## Define review scope

Prefer an explicit study manifest or a user-supplied file list. If neither exists:

1. List candidate files without reading their contents.
2. Exclude `.git/`, `.omx/`, environments, caches, dependencies, raw-data directories, model weights, generated binaries, and this skills library's own docs.
3. Classify candidates by sensitivity and study stage.
4. Read only the smallest relevant, governance-approved set.

For PDF/DOCX or visual figures, use a format-aware render/inspection workflow. A filename scan is not document review.

When a stage `artifact` is a bundle index, verify the index against the stage `sha256`, expand every member, verify each member hash, and review the member contents required by the declared gate. The coverage matrix must list every member as assessed or `not-assessed`; reviewing only bundle metadata cannot produce a passing verdict.

Create a coverage matrix before judging readiness:

| Domain | Artifacts supplied | Reviewer | Status |
|---|---|---|---|
| governance | policy/manifest | `mimic-data-governance` | assessed/not assessed |
| protocol/time | protocol/SAP | `mimic-study-protocol-sap` | assessed/not assessed |
| SQL/data | SQL/QC | `mimic-bigquery-qc` | conditional |
| clinical | cohort/definitions/results | `clinical-reviewer` | assessed/not assessed |
| statistics | SAP/code/results | `statistics-reviewer` | assessed/not assessed |
| reporting | manuscript/tables/figures | `journal-reviewer` | assessed/not assessed |
| reproducibility | code/manifests/release | `mimic-reproducibility-release` | assessed/not assessed |

## Load current review passes

Read each selected specialist `SKILL.md` completely before applying it. When installed skills can be invoked directly, invoke them. When working from this repository, resolve sibling skill directories. Record the version/commit and artifacts supplied to each pass.

Always apply governance, clinical, and statistical review when relevant material exists. Apply conditionally:

- SQL and data pipeline: `mimic-bigquery-qc`.
- Prediction: `mimic-prediction-modeling` plus `statistics-reviewer`.
- Causal/HTE: `mimic-causal-analysis-guardrails`, using subtype-specific target-trial, IV, RD, DiD, or ITS gates.
- Phenotyping: `mimic-phenotyping-pipeline`.
- External validation: `mimic-external-validation`.
- Manuscript: `journal-reviewer` and reporting-guideline checks.
- Release/code provenance: `mimic-reproducibility-release`.

Keep builder findings separate from independent reviewer findings. Deduplicate only when the underlying issue and required correction are identical; preserve the strongest severity and all evidence locations.

## Use a traceable issue register

For every finding record:

```yaml
id: REV-001
stage: question | protocol | concepts | cohort | features | analysis | validation | analysis_review | manuscript | manuscript_review | release | submission
domain: governance | design | data | clinical | statistics | reporting | reproducibility
severity: blocking | major | minor | note
confidence: high | medium | low
status: open | resolved | accepted-risk | not-assessed
artifact: path
location: line, query block, table, figure, or section
evidence: observed fact
impact: validity or publication consequence
action: smallest verifiable correction
owner: responsible role
verification: evidence required to close
closure_evidence: null # actual evidence, or accepted-risk authority record
closed_by: null
closed_at: null # ISO 8601 timestamp
```

Never report a vague concern without evidence or turn absent material into a pass. `resolved` requires populated `closure_evidence`, `closed_by`, and `closed_at`; `accepted-risk` must identify the accepting authority in `closure_evidence`.

## Synthesize the verdict

Use:

- `READY`: assessed required domains have no open blocking/major findings.
- `REVISE`: no redesign-level flaw, but open major findings remain.
- `REDESIGN`: time leakage, invalid estimand/risk set, fatal cohort/exposure/outcome error, or another flaw invalidates the primary analysis.
- `NOT_ASSESSABLE`: required evidence is unavailable or governance prevents review.

`READY` means ready for the next declared gate, not automatically accepted by a journal.

## Report structure

Return:

1. review scope, exclusions, governance mode, and coverage matrix;
2. verdict and the gate it applies to;
3. blocking and major findings ordered by downstream impact;
4. minor findings;
5. deduplicated action plan with owner and verification evidence;
6. resolved findings;
7. not-assessed domains and missing artifacts;
8. specialist passes used and their source versions.
