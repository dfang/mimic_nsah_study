---
name: mimic-submission-packager
description: Assemble and audit journal submission and revision packages for MIMIC clinical research. Use for live author-instruction checks, manuscript component packaging, CRediT and disclosure statements, ethics/DUA and data-code availability text, reporting-checklist page mapping, cover letters, point-by-point rebuttals, and clean/redline version reconciliation.
---

# MIMIC Submission Packager

Build a journal-ready submission package whose files, declarations, checklists, and revisions agree with the manuscript. Never rely on remembered journal requirements when live instructions are available.

Apply `mimic-data-governance` before opening study outputs. Submission packages must contain cleared aggregate material only; never attach restricted patient-level examples, notes, images, embeddings, model weights, or credentials.

Require an independent final-manuscript review from `mimic-review` that includes `journal-reviewer`, covers the manuscript, tables, figures, supplement, and reporting checklist, returns `READY`, and has no open `requires_redesign`, `blocks_ready`, blocking, or major findings. If that evidence is absent, the package may be inventoried but the submission verdict must remain not ready.

Also require a completed `mimic-reproducibility-release` verdict and hashed release manifest showing the public/restricted artifact split, environment and provenance evidence, and no open release blockers. If the release gate is absent or incomplete, inventory work may proceed but the submission verdict must remain not ready.

## Freeze the target requirements

1. Confirm the journal, article type, submission stage, and submission-system locale.
2. Retrieve the current author instructions, article-type requirements, reporting policies, AI policy, data/code policy, and file specifications from authoritative journal pages.
3. Record each URL, retrieval date, stated update date when available, and requirement in the submission manifest.
4. Flag inaccessible, conflicting, or ambiguous instructions. Do not silently choose a remembered rule.

Read `references/submission-components.md` to select declarations and reporting checklists. Copy the needed files from `assets/templates/` into the manuscript workspace.

## Inventory and reconcile files

- List the title page, blinded manuscript where required, abstract, highlights, key points, tables, figures, legends, supplements, reporting checklists, cover letter, declarations, and revision materials.
- Check title, short title, author order, affiliations, corresponding-author details, word counts, references, table/figure numbering, supplement links, and filenames across all files.
- Keep blinded and unblinded files distinct. Search blinded materials for author names, institutions, acknowledgements, file metadata, and tracked-change identities.
- Do not infer author approval, contribution, conflicts, funding, ethics determinations, or signatures. Mark missing confirmations as blockers.

## Complete declarations

- Record each author's CRediT roles and obtain confirmation; do not assign roles from author order.
- Reconcile conflicts of interest, funding, sponsor role, acknowledgements, and contributor statements across the title page, manuscript, forms, and submission portal.
- State the applicable ethics/IRB determination, deidentification context, authorized MIMIC access, training/DUA compliance, and consent waiver or non-applicability only from supplied evidence.
- Write data and code availability statements that distinguish restricted source data, shareable code, aggregate outputs, and any sensitive derived artifacts.
- Follow the journal's current AI-use disclosure policy and accurately describe tool, purpose, human verification, and excluded authorship responsibility where required.

Use `assets/templates/author-declarations.md` as a completeness record, not as evidence that a declaration is true.

## Map reporting checklists

- Select reporting guidance from the actual study design and journal policy, such as STROBE/RECORD for routinely collected observational data, TRIPOD+AI for prediction models, TARGET 2025 for target trial emulations, or other design-specific checklists.
- Retrieve the current official checklist version rather than reusing an old local copy.
- Map every checklist item to final page/line numbers or a precise supplement location using `assets/templates/checklist-page-map.csv`.
- Mark genuinely non-applicable items with a reason. Never use `N/A` to hide missing reporting.
- Regenerate the mapping after pagination changes.

## Draft the cover letter

- Use `assets/templates/cover-letter.md` and follow journal-specific content rules.
- State the clinical question, main contribution, fit for the journal, manuscript type, and required exclusivity/originality declarations.
- Keep novelty and result claims consistent with the manuscript and verified evidence. Do not add promotional claims, invented editor names, or unsupported priority assertions.
- Mention related manuscripts, preprints, prior conference reports, or overlapping cohorts when disclosure is required.

## Prepare a revision and rebuttal

- Copy `assets/templates/rebuttal.md` and preserve every editor and reviewer comment verbatim enough to maintain its meaning.
- Number comments and answer each separately with: response, action taken, exact file/page/line location, and concise before/after text when useful.
- If no change is made, give an evidence-based rationale without dismissive language.
- Keep clean and redline manuscripts synchronized. Confirm every claimed change exists and every material diff is explained.
- Record added/removed analyses, changed denominators or estimates, revised tables/figures, and downstream text affected by those changes.

## Final gate

Before handoff, verify:

- live journal requirements are logged with dates and URLs;
- the independent final-manuscript review gate passed and its evidence is recorded;
- the reproducibility-release gate passed and its manifest/hash are recorded;
- all required files are present and open correctly;
- author and declaration fields are confirmed or clearly blocked;
- checklist locations match final pagination;
- cover-letter claims match the manuscript;
- rebuttal locations and quoted revisions match the clean/redline files;
- data/code and AI statements match current policy and actual practice;
- no patient-level data, credentials, hidden comments, stale tracked changes, or identifying metadata are included accidentally.

Return a submission manifest, file inventory, blocker list, and a concise ready/not-ready verdict.
