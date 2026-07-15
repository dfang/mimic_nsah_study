---
name: mimic-clinical-manuscript
description: Author MIMIC clinical manuscripts and supplements from frozen study artifacts. Use for introductions, methods, results, discussions, tables and figures, limitations, reproducibility statements, reporting-checklist alignment, quantitative claim tracing, and cautious interpretation of observational, prediction, causal, or phenotyping studies.
---

# MIMIC Clinical Manuscript

Author from verified artifacts; do not independently approve the study. After the complete manuscript package is drafted, route it to `mimic-review` with `journal-reviewer`, resolve blocking and major findings, and re-review corrections before calling the manuscript frozen or submission-ready. Route final journal packaging to `mimic-submission-packager` only after that gate passes.

## Governance and source gate

Apply `mimic-data-governance` before reading study materials. Do not send restricted notes, images, row-level data, sensitive derived data, or unsafe small cells to an unverified external service.

For an early Introduction/Methods draft, require a frozen protocol/SAP or explicit exploratory label plus verified literature and data-version provenance. Clearly label the draft pre-results; it does not advance or freeze the manuscript stage.

For Results, Discussion, or a complete manuscript package, additionally require:

- frozen cohort, analysis, figure, and table artifacts with paths/hashes;
- an issue register with no unresolved blocking findings;
- a verified literature evidence table from `mimic-literature-evidence`;
- exact MIMIC/module versions, derived metadata, and code/environment provenance.

Do not invent a missing number, citation, method, ethics statement, or result. Mark unavailable material as a placeholder with its required source.

## Select reporting standards

- Routinely collected EHR observational study: STROBE plus RECORD; consider CODE-EHR minimum standards.
- Prediction development/evaluation: TRIPOD+AI; use PROBAST+AI to appraise quality, risk of bias, and applicability.
- Target trial emulation within TARGET's stated scope: TARGET 2025 as the standalone primary checklist; add STROBE/RECORD only when the journal requires it or the report contains relevant material outside TARGET's scope.
- IV, RD, DiD, or ITS: use guidance specific to the actual quasi-experimental design; do not route these studies to TARGET solely because they are causal.
- Phenotyping: report feature windows, preprocessing, missingness, cluster selection, stability, assignment rules, and external validation status.

Create a checklist-to-page/section map; do not merely name the guideline.

## Write from the evidence chain

### Introduction

- State the clinical decision or evidence gap, not just algorithm novelty.
- Cite only records with verified DOI/PMID or authoritative guideline provenance.
- Explain why MIMIC can address the question and what it cannot establish.

### Methods

Report governance/ethics, data/module versions, setting, eligibility, cohort flow, analysis grain, the complete named time contract, exposures/outcomes, code lists, feature sources, missing data, sample-size/event rationale, analysis methods, validation, multiplicity, sensitivity analyses, software/environment, and protocol deviations.

For prediction, state subtype, intended use, subject-level splitting, preprocessing fit boundaries, internal validation, calibration, clinical utility, fairness, and model availability; diagnostic models also report the reference standard and blinding, while prognostic models report censoring and competing events. For causal work, state the subtype and estimand. Target-trial reports include grace-period handling, confounder rationale, positivity, balance, censoring, and sensitivity analyses; IV/RD/DiD/ITS reports include their assignment mechanism, identifying assumptions, diagnostics, and failure conditions.

### Results

- Start with cohort flow, denominators, missingness, and baseline characteristics.
- Report effect/performance estimates with uncertainty and diagnostic evidence.
- Separate primary, sensitivity, subgroup, and external-validation results.
- Report negative and adverse findings.
- Trace every quantitative statement to a frozen table, figure, or result artifact.

### Discussion

- Interpret clinical magnitude and intended use before statistical significance.
- Compare against verified prior evidence.
- Separate association, prediction, phenotype discovery, and causal claims.
- Discuss single-center EHR data, coding/measurement/selection bias, informative missingness, residual confounding, temporal drift, fairness, and transportability as applicable.

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

Include code lists, cohort definitions and flow, feature/outcome dictionary, time contract, SQL/pipeline summary, missingness, diagnostics, sensitivity analyses, model card or phenotype stability, reporting checklist, and reproducibility statement. Reference public code without including restricted data.

## Output contract

Return manuscript/supplement paths; `references.bib`, `journal.csl`, and citation-verification artifact paths; unresolved citation keys, source placeholders, legacy numbers, and intentionally uncited records; reporting-checklist coverage; quantitative-claim provenance; citation-verification status; and deviations from the frozen protocol. If the target journal style has not been verified, report the missing CSL requirement rather than guessing. If writing into `dist/`, use a dated directory and include a generation note; never place restricted patient-level material there.
