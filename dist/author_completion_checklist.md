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

- [x] Retained and documented the descriptive same-hospital association; the current manuscript does not present a 48 h landmark or bedside prediction estimand.
- [x] Counted 1,173 distinct `subject_id` values among 1,186 stays (13 repeated-subject admission rows) and froze subject-grouped full-pipeline bootstrap results.
- [x] Ran the include-all sensitivity analysis without the post-entry `>=5 units/24 h` red-cell exclusion; it added no otherwise eligible cases and did not change the primary cohort.
- [ ] Validate or externally support the ICD/text NSAH identification algorithm, especially traumatic-SAH exclusion, and report expected misclassification.
- [x] Reconciled the implemented exploratory regression formula with `sap.md` v1.0.1 and recorded the post-outcome documentation correction, unadjusted multiplicity, and stay-level covariance in the deviations log; no analysis result changed.
- [x] Froze data provenance: query dates, source table versions, row counts, analysis environment, package lock, and immutable analysis artifact hashes.
- [ ] Conduct a final disclosure-control review of all aggregate tables and figures before public release.
- [ ] Provide dated author/institution approval for public aggregate disclosure; repository visibility is not an approval record.
- [x] Exported and privately hashed a versioned `DERIVED_SENSITIVE` MIMIC transform bundle, reran eICU through the fail-closed pure-evaluation entry point, and reconciled the resulting 539/222/82 aggregates on 2026-07-24.
- [x] Assessed eICU hospital dependence with 2,000 hospital-cluster bootstrap replicates and 66 leave-one-hospital-out analyses; only aggregate outputs without hospital identifiers were retained.

## C. Technical production before upload

- [x] Render the English manuscript, Chinese reference manuscript, ESM, and STROBE checklist with Pandoc 3.10 citeproc and WeasyPrint 69.0; inspect every page for pagination, citations, tables, figures, and reference typography.
- [ ] Produce the journal-preferred editable DOCX. Current PDFs must be regenerated from the post-rerun sources and remain non-submission artifacts while author metadata, disclosure approval, and independent rereview are open.
- [x] Regenerate charts as vector artwork or at the journal-required effective resolution. Referenced figures now have 600 dpi PNG and vector PDF versions; final production should prefer the vector files.
- [ ] Add the complete title page and corresponding-author details to the ESM source/PDF after authors supply them.
- [ ] Recheck final word count, abstract length, take-home message length, figure/table limits, accessibility text, and file naming after typesetting.

## D. Already completed in this revision

- [x] Verified all cited identities and metadata; no unresolved cited key, duplicate DOI/PMID, or known retraction was found.
- [x] Added the official MIMIC-IV 3.1, eICU-CRD 2.0, PhysioNet, STROBE, and RECORD citations where they support the text.
- [x] Corrected SAHARA publication metadata and narrowed the claim to its supported 12-month outcome.
- [x] Designated `manuscript_non_traumatic_sah_phenotypes_cited.md` as the reviewed English submission source and aligned `manuscript_non_traumatic_sah_phenotypes_cn_cited.md` to it on 2026-07-23.
- [x] Kept the English structured abstract within 250 words, retained five keywords, kept the take-home message within 65 words, and retained two correctly matched main figures.
- [x] Removed non-central prediction-model results from the submission manuscript because the current analysis does not establish a time-anchored, leakage-free bedside prediction estimand.
- [x] Reframed mortality findings as descriptive same-hospital associations and documented the 0-48 h outcome-overlap limitation.
- [x] Removed the admission-origin Cox/Kaplan-Meier results from the submission manuscript and documented the future-informed phenotype, within-window death, and competing-discharge boundary in the ESM.
- [x] Corrected the analysis unit to 1,186 ICU stays from 1,173 patients and synchronized the subject-grouped bootstrap ARI (mean 0.8554).
- [x] Completed pure frozen eICU re-execution with counts 539/222/82 and de novo ARI -0.0017; interpretation remains exploratory transport rather than confirmatory external validation.
- [x] Added hospital-clustered precision and single-hospital influence analyses; the mortality order remained in all 66 leave-one-hospital-out analyses.
- [x] Reclassified the hemoglobin-free anemia analysis as post hoc exploratory and reported the specification-sensitive odds ratios (0.99 versus 1.54).
- [x] Completed a bilingual language, AI-pattern, and unsupported-claim audit without changing reported study estimates.
- [x] Prepared STROBE and RECORD mappings and a submission-readiness review.
- [x] Regenerated all referenced figures as 600 dpi PNG plus vector PDF and removed conflicting embedded figure numbers.
- [x] Corrected the MIMIC-IV 3.1 coverage period to 2008-2022 against the official version page.
- [x] Reconciled phenotype label ordering with the outcome-blind physiological severity-score implementation.
- [x] Added draft governance, study/run manifests, DAG, provenance, seed, deviation, issue-register, and release-audit artifacts.
- [x] Added a tested PDF-build guard that blocks unresolved Pandoc citation syntax.
- [x] Passed Pandoc 3.10 citeproc preflights for the reviewed English and aligned Chinese manuscripts with no unresolved citation keys; no stale PDF was overwritten.
