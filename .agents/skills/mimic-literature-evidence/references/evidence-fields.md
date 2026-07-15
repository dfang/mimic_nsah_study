# Evidence and citation fields

## Search log

Record one entry for each database and query revision:

- database and platform;
- date searched and coverage end date;
- exact query as executed;
- filters and limits;
- raw result count;
- export filename or stable search URL when available;
- notes explaining query changes.

## Screening log

Record a stable record ID, source database, duplicate group, title/abstract decision, full-text decision, exclusion reason, and reviewer note. Use a controlled set of exclusion reasons and explain exceptions.

## Evidence table

Required fields:

- record ID;
- verified citation;
- DOI and DOI verification status;
- PMID and PMID verification status;
- publication type and status;
- country/setting;
- database and version;
- cohort dates and sample size;
- population and eligibility;
- design and analysis grain;
- time zero and windows;
- exposure/intervention and comparator;
- outcomes and horizon;
- statistical methods;
- main estimate and uncertainty;
- validation;
- code/data availability;
- major limitations and risk-of-bias concerns;
- relevance to the proposed MIMIC study.

## Verification status vocabulary

- `verified`: authoritative metadata resolves and agrees.
- `partial`: one identifier resolves but another field is missing.
- `conflict`: authoritative records disagree.
- `not_found`: the claimed identifier does not resolve.
- `not_applicable`: the publication legitimately has no identifier.

Do not convert `partial`, `conflict`, or `not_found` into `verified` through inference.

## Manuscript bibliography fields

- `citation_key`: stable unique key used by Pandoc citations. Prefer `firstauthorYYYYkeyword`; when keys collide, append a deterministic short suffix derived from stable record metadata.
- `bibliography_eligible`: `yes` only when the record identity and the metadata needed for the target reference are verified or come from an explicitly authoritative source.
- `bibliography_exclusion_reason`: required when eligibility is `no`; use a concrete reason such as unresolved identifier, metadata conflict, retraction, replacement, or insufficient source access.

Once a citation key appears in a frozen manuscript, do not change it merely because punctuation, capitalization, author truncation, or other display metadata changes. A `partial`, `conflict`, or `not_found` verification result does not become bibliography-eligible through inference. Preserve the record and its exclusion reason so a later authoritative resolution remains auditable.
