# Stage contracts

Use this reference to decide whether a stage can be frozen. One study manifest represents one primary scientific question. Store only paths, counts, hashes, and aggregate validation evidence in the manifest.

Every stage's canonical `artifact` field points to a **bundle index**, and the stage `sha256` hashes that index. The bundle index records each member artifact's `role`, `path`, `version`, and `sha256`; it must not embed restricted contents. This lets a stage freeze multiple deliverables without changing the manifest field shape.

For prediction and causal designs, route the gate with `design_subtype`: `diagnostic` or `prognostic` for prediction, and `target_trial`, `iv`, `rd`, `did`, or `its` for causal designs. Other design families use `not_applicable`. `other_with_gate_plan` is allowed only when the protocol bundle contains a design-specific gate plan naming its assumptions, diagnostics, acceptance evidence, specialist reviewer, and stop/redesign conditions; it is not a generic fallback.

| Stage | Required inputs | Required outputs | Acceptance evidence |
|---|---|---|---|
| question | clinical area, intended use, data access | ranked question and design | novelty evidence plus design-specific sufficiency/precision: descriptive target precision, association/causal estimand precision and applicable overlap/ESS, prediction outcome frequency/parameters/shrinkage/evaluation precision, or phenotype stability/minimum-cluster support; unknowns require explicit stopping rules |
| protocol | selected question, evidence table | protocol, design-specific analysis plan, time contract, target parameter; `target_trial` requires target-trial/DAG/identification artifacts, while `iv`/`rd`/`did`/`its` require subtype-specific assignment mechanism, assumptions, diagnostics, and gate plan | signed-off primary analysis and deviation policy |
| concepts | protocol | codebook and concept provenance | matched descriptions, clinician review, versioned code lists |
| cohort | protocol, codebook | cohort SQL/table, flow table | unique target key, exclusion counts, time sanity checks |
| features | cohort, feature definitions | feature table and dictionary | window audit, missingness/range QC, no forbidden leakage |
| analysis | frozen SAP and inputs | results, diagnostics, figures | assumptions, uncertainty, sensitivity analyses, code hash |
| validation | frozen analysis object/specification; branch-specific evidence below | prediction validation, phenotype replication/assignment transport, causal subtype-specific replication/transport, descriptive/association replication, or a documented `not_applicable` decision | branch-specific acceptance evidence below |
| analysis_review | frozen protocol, cohort, code, QC, analysis, and any external validation | review input snapshot, validated pass receipts, coverage matrix, issue register and gate verdict | registry-required governance, protocol-time, SQL/data, clinical and statistics passes plus the design-specific pass; one `review_run_id`; identical input hashes; reviewer identities and skill versions; `READY` verdict with no open `requires_redesign`, `blocks_ready`, blocking or major findings before manuscript authoring |
| manuscript | frozen results and analysis-review verdict | manuscript, tables, figures, and supplement | number-to-artifact trace, reporting checklist, citation verification |
| manuscript_review | complete manuscript package | review input snapshot, validated pass receipts, coverage matrix, independent issue register and gate verdict | registry-required governance, clinical, statistics, journal and reproducibility passes plus applicable design/evidence/validation passes; one `review_run_id`; identical input hashes; independent reviewer identities; page-mapped checklist, claims reconciled to frozen results, and a `READY` verdict with no open `requires_redesign`, `blocks_ready`, blocking or major findings |
| release | code, reviewed manuscript, and non-sensitive artifacts | reproducibility bundle | clean-room check, environment lock, no restricted data |
| submission | journal instructions, manuscript-review verdict, and release | submission package | live instruction check, disclosures, checklist page mapping |

Introduction and Methods may be drafted early from a frozen Protocol and verified evidence, but this does not advance the `manuscript` stage. Freezing that stage still requires frozen results, analysis-review verdict, complete tables/figures/supplement, and traceable claims.

## Validation branch contract

- **Applicable branch**: requires a genuine external dataset plus frozen input, assignment, or target specification as applicable. The bundle index must reference concept/cohort mapping, deviations, design-specific metrics or estimates, uncertainty, and interpretation limits.
- **Not-applicable branch**: does not require an external dataset. It requires a documented applicability assessment, its bundle index and hash, and a concise `rationale`. If the protocol or claims seek transportability, deployment, or cross-setting replication, the assessment must include dataset-search and mapping-feasibility evidence. Use manifest `status: not_applicable`; do not use this branch when external validation is required by the protocol or when required evidence is merely missing.

## Bundle index schema

```yaml
bundle_version: "1.0"
stage: protocol
artifacts:
  - role: protocol
    path: path/to/protocol.md
    version: "1.0.0"
    sha256: "<sha256>"
```

## Review run contract

Formal `analysis_review` and `manuscript_review` gates use `mimic-review` in `mode: gate`. Copy `skills/mimic-review/assets/templates/review-input.yaml` into the study repository and freeze it as a member of the review-stage bundle index.

The review input records `operation: audit`, one `review_run_id`, the canonical gate, requested passes, design route, governance receipt, repository commit and dirty state, and every artifact path/version/SHA-256. Resolve passes from `skills/mimic-review/references/review-pass-registry.json`. Every specialist pass copies `skills/mimic-review/assets/templates/review-pass-receipt.yaml` and records the same input hashes plus its `reviewer_identity` and skill version. Hash disagreement or invalid receipt creates `not-assessed` coverage and blocks aggregation into a passing verdict.

`manuscript_review` always requires governance, clinical, statistics, journal and reproducibility receipts. Missing clinical or statistics evidence is `not-assessed`, never `not_applicable`.

Focused review may use the same `review-input.yaml` schema with `mode: focused`, but its output is not acceptance evidence for freezing a lifecycle review gate.

## Issue register schema

Record each finding with:

```yaml
id: REV-001
severity: blocking | major | minor | note
gate_effect: blocks_ready | requires_redesign | none
confidence: high | medium | low
stage: cohort
domain: data
artifact: path/to/file
location: line, table, figure, or query block
evidence: concise observation
risk: consequence for validity or reporting
recommended_action: smallest verifiable correction
owner: role or person
verification: evidence required to close
status: open | resolved | accepted-risk | not-assessed
closure_evidence: null # actual evidence or accepted-risk authority record once closed
closed_by: null
closed_at: null # ISO 8601 timestamp
```

Do not convert missing material into a pass. Use `not-assessed` and list the missing evidence. `resolved` requires populated `closure_evidence`, `closed_by`, and `closed_at`; `accepted-risk` additionally identifies the authority accepting the risk in `closure_evidence`.
