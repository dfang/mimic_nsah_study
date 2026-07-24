# Data Governance Record

## Current public-release status (2026-07-24)

The repository is publicly visible, but no author/institution disclosure-approval
record is present. Public aggregate release is therefore
`BLOCKED_PENDING_AUTHOR_INSTITUTION_APPROVAL`. The machine-readable status is
`reproducibility/governance-status.yaml`. The `PROCEED_LOCAL` record below governs
the authorized restricted analysis runs, including the 2026-07-24 frozen-transport
and hospital-level robustness rerun; it is not evidence of public release approval.
Restricted rows remained in the authorized environment and only aggregate outputs
without hospital identifiers were added to public artifacts.

## Current decision

```yaml
governance_decision: PROCEED_LOCAL
scope: "Authorized local BigQuery dry-run and execution for the declared MIMIC-IV/eICU pipeline; local statistical rerun; aggregate-only QC, reconciliation, and freeze metadata"
data_classes: [PUBLIC, MIMIC_RESTRICTED, DERIVED_SENSITIVE, AGGREGATE_REVIEW]
source_projects_and_versions:
  - "MIMIC-IV 3.1"
  - "eICU-CRD 2.0"
authorized_user_confirmed: true
authorization_confirmation_recorded_at: "2026-07-16 Asia/Shanghai"
processing_destinations:
  - "local workspace"
service_evidence:
  applicability: "not applicable to restricted processing; no restricted rows were sent to an external AI/service"
  verified_on: "2026-07-16"
controls:
  - "Execute restricted processing only through local scripts and the user's authorized BigQuery credentials."
  - "Do not print, upload, commit, or publish patient-level rows or restricted query outputs."
  - "Persist only approved aggregate outputs and non-sensitive job/source provenance in the public workspace."
  - "Do not include credentials, service-account files, tokens, or connection strings in Git."
  - "Apply conservative local disclosure review and suppress non-zero public cells below 10."
  - "Run restricted BigQuery work only in an authorized user's approved environment."
excluded_paths:
  - ".git/"
  - ".env* and credentials"
  - "patient-level exports and local data directories"
  - "notebook outputs, logs, caches, model weights, embeddings, and checkpoints"
release_plan: "Public code and documentation are separated from restricted source data; a conservative local aggregate review is complete, while author/institution approval remains required before journal/public release; derived patient-level data and models remain restricted."
blockers:
  - "Author/institutional disclosure approval is not yet recorded for journal/public release; this does not block the controlled exploratory analysis freeze."
next_review_date: null
```

## Release classes

| Class | Repository examples | Release rule |
| :--- | :--- | :--- |
| PUBLIC | SQL/Python code without patient values, protocol, SAP, templates, tests | May be reviewed for public release after secret/path scanning |
| AGGREGATE_REVIEW | Manuscripts, summary tables, figures, aggregate flow counts | Requires author/institution disclosure review before public release |
| MIMIC_RESTRICTED | Patient-level source or derived rows, event times, identifiers, query caches | Never include in the public repository |
| DERIVED_SENSITIVE | Patient-level labels, assignments, models, weights, embeddings | Keep restricted unless approved through the applicable PhysioNet route |
| SECRET | Credentials, keys, tokens, connection strings | Never read into tools or commit |

## Required re-evaluation

Repeat the governance gate before any BigQuery execution, patient-level file access, external-service upload, public release, or change in processing environment.
