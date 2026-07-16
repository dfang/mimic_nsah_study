# Author Completion and Authorized Reanalysis Checklist

This is the single handoff list for work that cannot be completed from the current public, aggregate repository state. Items are separated so form-filling is not confused with analyses that require an authorized MIMIC/eICU user.

## A. Authors and institution must complete

- [ ] Confirm author names, order, degrees, affiliations, corresponding author, email address, and ORCID identifiers on the title page.
- [ ] Confirm each author's CRediT roles and final approval; collect one ICMJE disclosure form per author.
- [ ] Complete funding and grant numbers, sponsor role, conflicts of interest, and acknowledgements/non-author contributors.
- [ ] Provide the submitting institution's ethics/IRB determination and identifier; approve exact consent or waiver wording.
- [ ] Confirm that every data analyst completed the applicable PhysioNet credentialing, training, and data-use requirements.
- [ ] Approve the data-availability and code-availability statements and provide the permanent public repository/release URL, if code will be public.
- [ ] Confirm originality, no simultaneous submission, prior abstract/congress/preprint disclosure, and any overlap with related manuscripts.
- [ ] Approve the AI-use disclosure. Current draft records generative drafting and editorial assistance; authors remain accountable for all content.
- [ ] Confirm that all authors reviewed the final English manuscript, figures, tables, citations, STROBE checklist, and RECORD checklist.

## B. Authorized reanalysis or design decisions

- [ ] Choose and document the estimand: retain the current descriptive same-hospital association, or rerun a 48 h landmark analysis among patients alive and observed at 48 h.
- [ ] Count distinct `subject_id` values and repeated admissions; rerun bootstrap and any retained cross-validation with patient-grouped resampling if repeats exist.
- [ ] Run an include-all sensitivity analysis without the post-entry `>=5 units/24 h` red-cell exclusion, or justify and freeze the exclusion as a post hoc design choice.
- [ ] Validate or externally support the ICD/text NSAH identification algorithm, especially traumatic-SAH exclusion, and report expected misclassification.
- [ ] Reconcile implemented analyses with `protocol.md` and `sap.md`; freeze both as retrospective/post-outcome documents and maintain a deviations log.
- [ ] Freeze data provenance: query dates, source table versions, row counts, analysis environment, package lock, and immutable artifact hashes.
- [ ] Conduct a final disclosure-control review of all aggregate tables and figures before public release.

## C. Technical production before upload

- [ ] Render the English manuscript and ESM with a verified Pandoc/citeproc toolchain; visually inspect numeric citation order, reference de-duplication, DOI links, and reference typography.
- [ ] Produce the journal-preferred editable DOCX and a submission PDF. Current PDFs in `dist/pdf/` predate these revisions and must not be submitted.
- [x] Regenerate charts as vector artwork or at the journal-required effective resolution. Referenced figures now have 600 dpi PNG and vector PDF versions; final production should prefer the vector files.
- [ ] Add the complete title page and corresponding-author details to the ESM PDF.
- [ ] Recheck final word count, abstract length, take-home message length, figure/table limits, accessibility text, and file naming after typesetting.

## D. Already completed in this revision

- [x] Verified all cited identities and metadata; no unresolved cited key, duplicate DOI/PMID, or known retraction was found.
- [x] Added the official MIMIC-IV 3.1, eICU-CRD 2.0, PhysioNet, STROBE, and RECORD citations where they support the text.
- [x] Corrected SAHARA publication metadata and narrowed the claim to its supported 12-month outcome.
- [x] Promoted citation-aware English and Chinese manuscripts to canonical filenames and synchronized their citation sets.
- [x] Reduced the structured abstract to the ICM limit, kept five keywords, and reduced the main display set to three figures.
- [x] Removed non-central prediction-model results from the submission manuscript because the current cross-validation has unresolved leakage/grouping risk.
- [x] Reframed mortality findings as descriptive same-hospital associations and documented the 0-48 h outcome-overlap limitation.
- [x] Completed a language/humanization pass without changing reported study estimates.
- [x] Prepared STROBE and RECORD mappings and a submission-readiness review.
- [x] Regenerated all referenced figures as 600 dpi PNG plus vector PDF and removed conflicting embedded figure numbers.
- [x] Corrected the MIMIC-IV 3.1 coverage period to 2008-2022 against the official version page.
- [x] Reconciled phenotype label ordering with the outcome-blind physiological severity-score implementation.
- [x] Added draft governance, study/run manifests, DAG, provenance, seed, deviation, issue-register, and release-audit artifacts.
- [x] Added a tested PDF-build guard that blocks unresolved Pandoc citation syntax.
