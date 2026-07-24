---
name: mimic-clinical-manuscript
description: Use when authoring MIMIC clinical manuscripts or supplements from frozen, reviewed study artifacts, including citation-aware reports and complete packages that require observational, prediction, phenotyping, target-trial, or quasi-experimental design routing.
---

# MIMIC Clinical Manuscript

Author from verified artifacts; do not independently approve the study or alter its frozen scientific design. Keep design-specific reporting rules in the routed references below rather than reconstructing them here.

## Governance and source gate

Apply `mimic-data-governance` before reading study materials. Do not send restricted notes, images, row-level data, sensitive derived data, or unsafe small cells to an unverified external service.

For an early Introduction/Methods draft, require a frozen protocol/SAP or explicit exploratory label plus verified literature and data-version provenance. Clearly label the draft pre-results; it does not advance or freeze the manuscript stage.

Before drafting Results, Discussion, or a complete manuscript package, require:

- frozen `study.design_family` and its required `study.design_subtype` field;
- the primary question and frozen estimand, prediction target, or phenotyping objective;
- the analysis unit and complete named time contract;
- the analysis-review verdict and issue register, with no unresolved blocking findings;
- validation status plus its applicability rationale;
- paths and SHA-256 hashes for frozen cohort, analysis, result, table, and figure artifacts;
- a verified literature evidence table from `mimic-literature-evidence`; and
- exact MIMIC/module versions, derived metadata, and code/environment provenance.

Do not invent a missing number, citation, method, ethics statement, route, hash, or result. Mark unavailable material as a placeholder with its exact required source. Missing evidence never becomes `not_applicable` without a frozen applicability assessment and rationale.

## Route from the frozen design

Route only from the frozen `study.design_family` and required `study.design_subtype`. Never infer or change the route from an algorithm, model class, result pattern, reporting guideline, title, or requested claim.

| Frozen route | Required primary reference |
| --- | --- |
| `descriptive/not_applicable` or `association/not_applicable` | `references/observational-manuscript.md`, then the exact family section |
| `prediction/diagnostic` or `prediction/prognostic` | `references/prediction-manuscript.md` plus the exact subtype section |
| `phenotyping/not_applicable` | `references/phenotyping-manuscript.md` |
| `causal/target_trial` | `references/causal-target-trial-manuscript.md` |
| `causal/iv`, `causal/rd`, `causal/did`, or `causal/its` | `references/causal-quasi-experimental-manuscript.md` plus the exact subtype section |

For every routed manuscript, section, or display request, apply `references/common-manuscript-quality.md`, then exactly one primary reference row above. Within a primary reference that contains subtype sections, apply its shared sections plus exactly one section named by the frozen subtype; ignore every sibling subtype-specific section. Within the observational reference, apply its shared section plus exactly the descriptive or association family section named by the frozen route; ignore the sibling family section.

Block every other family/subtype combination, including a supported family paired with another family's subtype. Do not repair, reinterpret, or route an inconsistent pair from surrounding methods or results; require corrected frozen, reviewed routing evidence.

Read `references/validation-transportability-overlay.md` only when the frozen validation stage is assessed and applicable or the manuscript makes a validation or transportability claim. The overlay supplements the primary route; it never selects or replaces it.

For an explicitly frozen hybrid, record one primary route and the role of each secondary analysis. Keep every claim within its named role, and do not merge primary references merely because several algorithms or analyses appear.

If routing evidence is missing, inconsistent, or unsupported by the table, block complete finalization. Return the exact missing or conflicting field, artifact, status, or hash required to resolve the route.

## Map live reporting guidance

Retrieve each reporting guideline from its current authoritative source at execution time. Record its name, authoritative URL, publication or version, retrieval date, stated scope, applicability decision, verified journal override, and checklist-to-section/page mapping. Do not embed or copy a static full checklist into this skill or the manuscript workflow.

Apply this minimum routing:

- use STROBE plus RECORD for applicable observational studies using routinely collected data;
- use TRIPOD+AI for diagnostic or prognostic prediction studies, and use PROBAST+AI when risk-of-bias and applicability appraisal is in scope;
- use TARGET 2025 only for target-trial emulations within TARGET's stated scope; and
- use current subtype-specific reporting guidance for IV, RD, DiD, and ITS.

Verified journal-specific requirements override checklist placement and word limits. They do not override the frozen design, evidence requirements, or claim boundaries. Record checklist items with no verified location as unresolved rather than asserting coverage.

## Write from the evidence chain

Keep the publication-facing manuscript clinically coherent and concise. Put route receipts, source inventories, artifact paths and hashes, checklist mechanics, claim-provenance detail, issue registers, and bundle bookkeeping in their named authoring artifacts rather than narrating them in the manuscript. Use only the minimum inline source placeholder needed to avoid fabricating a claim; preserve the full unresolved detail and blocking status outside the publication prose.

### Introduction

- State the clinical decision or evidence gap before algorithm novelty.
- Cite only records with verified DOI/PMID or authoritative guideline provenance.
- Explain why MIMIC can address the question and what it cannot establish.

### Methods

- Follow `references/common-manuscript-quality.md` and the selected primary design reference.
- Trace every operational definition and performed method to the frozen protocol, codebook, or reviewed analysis artifact.
- Report protocol deviations and omit conventional methods that were not performed.

### Results

- Start with the applicable flow, denominators, missingness, and population description.
- Keep primary, secondary, sensitivity, subgroup, exploratory, and validation results distinguishable.
- Trace every quantitative statement to a frozen member path and SHA-256 hash in the result, table, or figure bundle; preserve null, negative, adverse, and failed-diagnostic findings.

### Discussion

- Interpret the frozen estimand, prediction target, phenotype, association, or descriptive quantity before statistical significance.
- Separate direct evidence, plausible interpretation, and speculation, and calibrate claims to the routed design and validation status.
- Compare against verified prior evidence and state limitations without guessing their direction.

## Author citation-aware Markdown

Keep narrative, bibliographic metadata, journal style, and verification evidence as separate artifacts:

```text
manuscript.md
references.bib
journal.csl
citation-verification table
```

Declare the project bibliography and verified target-journal style in the Markdown metadata:

```yaml
---
bibliography: references.bib
csl: journal.csl
link-citations: true
reference-section-title: References
---
```

Use Pandoc citation syntax with stable keys registered to bibliography-eligible evidence records:

```markdown
Prior estimates differed [@smith2024; @wang2025].

@johnson2023 described the source database.

The definition is reported elsewhere [@lee2022, pp. 12-14].
```

Insert only registered keys. Do not repair an unresolved identifier, invent a key, or use an ineligible record to make a material claim appear supported. When no verified record supports a required statement, leave an explicit source placeholder and record the claim, required source, and blocking status.

Do not hand-number the References list or mix manually maintained markers such as `[1]` with Pandoc citations. The References heading may be present when the template requires it, but citeproc owns entry inclusion, order, numbering, and formatting.

For a legacy manuscript with static numeric references, preserve the original and migrate only numbers that have an unambiguous authoritative number-to-record mapping. Record unresolved numbers as placeholders rather than guessing. Formatting-only metadata changes do not rename a key already used in a frozen manuscript.

## Build the supplement

Use the common and routed design references to determine design-specific supplement content. Include the frozen code lists, cohort definitions and flow, variable dictionary, time contract, SQL/pipeline summary, missingness, performed diagnostics and sensitivity analyses, reporting-checklist map, and reproducibility statement. Reference public code without including restricted data.

## Assemble the hashed manuscript bundle

Instantiate `assets/templates/manuscript-bundle-index.yaml` for every complete manuscript package. Do not invent a missing path, version, or hash. Give every member its `role`, `path`, `version`, `sha256`, `sensitivity`, and `status`.

Include members for:

- `primary_manuscript` and `supplement`;
- each `table` and `figure`;
- `bibliography` (`references.bib`) and `citation_style` (`journal.csl`);
- `citation_verification` and `quantitative_claim_provenance`;
- `reporting_guideline_map`; and
- `unresolved_register`.

Keep only metadata and artifact paths in the index; never embed manuscript text, patient data, or other restricted content. Hash every member, then hash the completed index. When a study manifest exists, update the `manuscript` stage `artifact` pointer to the bundle-index path and its `sha256` to the index hash.

Route every required member to independent `mimic-review` plus `journal-reviewer`. They must verify the index and member hashes, mark each required member assessed or `not-assessed`, return blocking and major findings to authoring, and re-review corrected members. The manuscript author cannot freeze `manuscript_review`; keep that gate pending until the independent reviewers record its verdict and issue state. Route final journal packaging to `mimic-submission-packager` only after this gate passes.

## Output contract

Return the following as authoring records outside the publication-facing manuscript prose:

- frozen routing evidence, the selected primary route, every loaded reference path, and the validation-overlay applicability reason;
- manuscript-bundle directory and index paths, the index SHA-256, and every member's role, path, version, SHA-256, sensitivity, and status;
- citation verification status and paths for `references.bib`, `journal.csl`, and the citation-verification artifact, including unresolved keys, source placeholders, legacy numbers, and intentionally uncited records;
- quantitative-claim verification status and claim-to-member path/hash provenance;
- live reporting-guideline records and checklist coverage/map status;
- unresolved items, protocol deviations, and exact evidence still required for finalization;
- the study-manifest `manuscript` pointer/hash update status when a manifest exists; and
- independent `mimic-review` plus `journal-reviewer` handoff and `manuscript_review` status.

If the target journal style has not been verified, report the missing CSL requirement rather than guessing. If writing into `dist/`, use a dated directory and include a generation note; never place restricted patient-level material there.
