---
name: mimic-literature-evidence
description: Build and audit a traceable literature evidence base for MIMIC clinical research. Use for novelty checks, background reviews, protocol or manuscript evidence updates, reproducible PubMed and database searches, study screening, evidence tables, DOI/PMID verification, and detecting unsupported or hallucinated citations.
---

# MIMIC Literature Evidence

Build an evidence trail that another researcher can rerun and audit. Separate what the literature establishes from what the proposed MIMIC analysis will test.

## Choose the operation

- `operation: build`: search, screen, verify, synthesize, or update bibliography artifacts.
- `operation: audit`: 只读审查现有 scope、search log、screening、evidence table、claim-citation mapping 和 citation verification；不得补搜、补筛、改 `references.bib` 或猜测修复 DOI/PMID。

When `mimic-review` invokes audit, use the same `review_run_id` and `input_hashes`, then copy `../mimic-review/assets/templates/review-pass-receipt.yaml` and return `pass_id: evidence-novelty`, `coverage_status`, `recommendation`, canonical findings, and `gate_effect`. Missing search dates, exact strategies, screening trail, full-text access, evidence table, or identifier resolution remain `not-assessed`.

## Set the review scope

1. State the clinical question, population, exposure or intervention, comparator, outcomes, study designs, date range, language limits, and MIMIC-specific novelty question.
2. Label the task as a rapid search, scoping review, systematic search, or targeted citation update. Do not imply systematic-review completeness when the workflow was narrower.
3. Record the search date and the last date covered by every database.

Copy `assets/templates/search-log.md` for the search record. Read `references/evidence-fields.md` before building the evidence or verification tables.

Match the audit standard to the declared review type:

- targeted citation update checks identity and claim support but cannot establish novelty;
- rapid evidence review records abbreviated methods and the resulting coverage limits;
- scoping review uses an applicable PRISMA-ScR workflow;
- systematic review/search uses applicable PRISMA and PRISMA-S elements, duplicate independent screening or a justified alternative, search peer review when required, protocol/deviation handling, and design-appropriate risk-of-bias assessment.

Do not infer a broad evidence gap from a narrow PubMed query. If coverage is insufficient, keep novelty `not-assessed`.

In audit, assign the evidence already produced a type rather than repeating the author's label. A single narrow query without a prespecified abbreviated review method, reproducible log, and screening trail is `targeted evidence`, not a rapid review and never a systematic search. Record that label in the receipt together with the resulting novelty limit.

## Search reproducibly

- Search at least one biomedical bibliographic database such as PubMed/MEDLINE. Add databases appropriate to the question rather than treating a general web search as equivalent.
- Preserve each database name, platform, exact query, filters, date searched, and raw result count before deduplication.
- Search concepts, synonyms, controlled vocabulary where supported, spelling variants, and relevant MIMIC names or versions.
- Use citation chaining only as a supplement. Record how each additional article was found.
- When current evidence or journal guidance matters, retrieve it live; never infer that a remembered search remains current.

## Screen and extract

- Apply explicit inclusion and exclusion criteria consistently. Record exclusion reasons at full-text screening.
- Deduplicate by DOI, PMID, and normalized title; do not collapse distinct corrections, protocols, conference abstracts, or companion reports without review.
- Copy `assets/templates/evidence-table.csv` and complete one row per included report.
- Extract the actual cohort, data source/version, design, sample size, exposure, comparator, outcomes, methods, estimates with uncertainty, limitations, and relevance to the proposed study.
- For MIMIC studies, capture database version, analysis grain, time zero, feature/exposure/outcome windows, validation setting, and code availability when reported.

## Verify every citation

For each cited source:

1. Resolve the PMID in PubMed when one is claimed.
2. Resolve the DOI through an authoritative DOI or publisher record when one is claimed.
3. Cross-check title, authors, journal, year, volume/pages or article number, DOI, and PMID across authoritative records.
4. Check publication status, correction, retraction, or replacement notices when they could affect use.
5. Mark unresolved discrepancies explicitly. Do not repair a citation by guessing.

Never invent a DOI, PMID, quotation, sample size, effect estimate, or conclusion. Do not cite a search-result snippet as evidence. If only an abstract is available, label that limitation and avoid claims requiring the full text.

## Prepare manuscript bibliography artifacts

Treat bibliography export as a downstream use of verified evidence, not as verification itself:

1. Assign a stable unique `citation_key` after the record identity is established. Prefer `firstauthorYYYYkeyword`; resolve collisions with a deterministic short suffix based on stable record metadata.
2. Record `bibliography_eligible` and any `bibliography_exclusion_reason` in the evidence and citation-verification tables. Do not make `partial`, `conflict`, or `not_found` records eligible through inference.
3. Export or reconcile `references.bib` only from eligible records, preserving verified DOI/PMID values and publication status.
4. Deduplicate by DOI, PMID, and normalized title before export, then verify that citation keys remain unique. Once a key is used in a frozen manuscript, formatting-only metadata changes do not rename it.
5. Return the bibliography path, record-to-key mapping, excluded records, and unresolved metadata conflicts.

Successful BibTeX serialization proves only that a record can be encoded; it does not prove that the citation is real, current, or suitable to support a claim. This skill does not compile the manuscript or choose a journal style whose provenance has not been verified.

## Synthesize without overclaiming

- Link each material claim to verified sources and distinguish direct evidence, inference, and the reviewer's interpretation.
- Maintain a claim-citation matrix for manuscript-facing audit: exact claim/location, supporting record, eligible evidence span, direction, population/design match, and unresolved conflict.
- Weight evidence by design quality, relevance, precision, consistency, and risk of bias rather than article count alone.
- Identify duplicated cohorts and overlapping MIMIC samples so they are not treated as independent replications.
- Describe the remaining gap in terms of a clinical decision or estimand, not merely the absence of a particular algorithm.
- Preserve contradictory and null findings.

## Deliverables

Return or save:

- scope and eligibility criteria;
- complete search log with dates and exact queries;
- screening counts and exclusion reasons;
- deduplicated evidence table;
- citation-verification table with DOI/PMID status;
- `references.bib` containing only manuscript-eligible records;
- stable record-to-citation-key mapping and bibliography eligibility/exclusion report;
- concise evidence synthesis and MIMIC-specific novelty assessment;
- unresolved records, access limits, and the date through which the review is current.
