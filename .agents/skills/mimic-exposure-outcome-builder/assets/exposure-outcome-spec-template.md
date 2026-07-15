# Exposure / Outcome Definition Specification

## Identity

- Concept name and version:
- Analytic role: exposure / outcome / censoring / competing event
- Clinical meaning:
- Analysis unit and unique key:
- Owner / clinical adjudicator:

## Temporal contract

- Eligibility time:
- Index / assignment / landmark time:
- Evidence window:
- Follow-up start:
- Follow-up end or censoring:
- Recurrence / episode rule:

## Operational definition

- Inclusion evidence:
- Exclusion evidence:
- Proxy status and limitations:
- First-event rule:
- Dose / duration / severity aggregation:
- Composite components if applicable:

## Source and provenance map

| Priority | Source table | Code / itemid set | Timestamp | Value / dose / unit | Status fields | Meaning |
|---:|---|---|---|---|---|---|
| 1 |  |  |  |  |  |  |

## Normalization and adjudication

- Unit normalization:
- Name / route / status normalization:
- Multi-source combination rule:
- Discordance review rule:
- Manual adjudication sample and process:

## Final variables

| Variable | Type | Unit | Window | Derivation | Missing meaning |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

## QC results

| Check | Expected | Observed | Status / action |
|---|---|---|---|
| Target-key uniqueness | Unique |  |  |
| Event rate | Plausible |  |  |
| Timestamp order | Valid |  |  |
| Source concordance | Reported |  |  |

## Sensitivity definitions

| Variant | Rule changed | Rationale | Count / rate impact | Analysis impact |
|---|---|---|---|---|
|  |  |  |  |  |

## Artifact manifest

- Codebook:
- Extraction / aggregation SQL:
- Event-level audit location:
- Concordance report:
- Data dictionary:
