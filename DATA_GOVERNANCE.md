# Data Governance Record

## Current decision

```yaml
governance_decision: PROCEED_PUBLIC_ONLY
scope: "Public code, SQL text, protocol/SAP, aggregate manuscripts, submission documents, and figure metadata"
data_classes: [PUBLIC, AGGREGATE_REVIEW]
source_projects_and_versions:
  - "MIMIC-IV 3.1"
  - "eICU-CRD 2.0"
authorized_user_confirmed: false
processing_destinations:
  - "local workspace"
service_evidence:
  zero_retention: unknown
  no_training: unknown
  no_human_review: unknown
  subprocessors_and_region: unknown
  verified_on: null
controls:
  - "Do not read, print, upload, or publish patient-level rows or restricted query outputs."
  - "Do not include credentials, service-account files, tokens, or connection strings in Git."
  - "Treat aggregate tables and figures as AGGREGATE_REVIEW until author/institution disclosure review."
  - "Run restricted BigQuery work only in an authorized user's approved environment."
excluded_paths:
  - ".git/"
  - ".env* and credentials"
  - "patient-level exports and local data directories"
  - "notebook outputs, logs, caches, model weights, embeddings, and checkpoints"
release_plan: "Public code and documentation are separated from restricted source data; aggregate outputs require disclosure review; derived patient-level data and models remain restricted."
blockers:
  - "Individual PhysioNet authorization, training, and DUA status is not confirmed in this repository."
  - "Institutional disclosure review of aggregate tables and figures is not recorded."
  - "External-service retention, training, human-review, subprocessors, and region evidence is not verified."
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
