# Manuscript Review Report

**Verdict:** REVISE

**Target:** Intensive Care Medicine, Original Paper

**Initial review:** 2026-07-16

**Repeat review after five additional iterations:** 2026-07-16
**Governance scope:** Public manuscript text, aggregate tables/figures, protocol/SAP, and code only. No patient-level data or restricted query was accessed.

## Coverage matrix

| Domain | Evidence reviewed | Assessment |
| :--- | :--- | :--- |
| Journal fit and format | Live ICM author instructions; English manuscript; ESM | Abstract, keywords, main word count, reference count, and three-main-figure structure are within stated limits. Editable production files and final title page are absent. |
| Clinical interpretation | English/Chinese manuscripts; ESM | Phenotypes are clinically interpretable, but the 0-48 h window overlaps same-hospital death and cannot support a 48 h landmark prediction claim. Language was corrected to descriptive association. |
| Phenotyping methods | Analysis code; protocol/SAP; ESM | Frozen transport to eICU and clustering parameters are reproducible. Outcome-based post hoc label ordering is now disclosed. Patient-grouped resampling remains unresolved. |
| Statistics | Analysis code; reported models | Estimates and uncertainty are reported. Cox analyses, process-variable adjustment, repeated admissions, and the post-entry transfusion exclusion require cautious interpretation. Non-central prediction results were removed because cross-validation leakage/grouping was unresolved. |
| Literature and citations | Manuscripts; BibTeX; evidence and verification tables | All 18 cited keys resolve; identities, DOI/PMID uniqueness, claim fit, SAHARA metadata, and retraction status were checked. Actual citeproc rendering remains unavailable. |
| Reporting guidelines | STROBE and RECORD mappings | Both mappings exist. RECORD-specific code-validation, access, and code-release disclosures are explicit or listed as open. |
| Reproducibility | Code, ESM notes, study/run manifests, DAG, provenance table, draft protocol/SAP | A traceable draft release structure now exists, but protocol/SAP remain retrospective `DRAFT_BLOCKED` reconstructions; no exact lock, authorized clean run, or immutable release has passed review. |
| Language | English and Chinese canonical manuscripts | A humanization pass removed formulaic phrasing and overclaiming without changing reported study estimates. |

## Blocking issues

| ID | Finding | Required resolution |
| :--- | :--- | :--- |
| B1 | Title page, authorship, CRediT roles, funding, conflicts, ethics/IRB, consent/waiver, and author approvals are incomplete. | Authors/institution complete and approve every declaration; collect ICMJE forms. |
| B2 | Pandoc/citeproc is unavailable; editable DOCX and updated manuscript/ESM PDFs have not been produced. Existing manuscript PDFs predate this revision. | Render citations, create editable source and fresh PDFs, and visually inspect the complete package. |
| B3 | The reproducibility gate is not frozen: protocol/SAP are post-outcome `DRAFT_BLOCKED` documents, and an exact environment lock, authorized clean run, extraction/job provenance, disclosure approval, and immutable release commit are absent. | Reconcile implemented analyses, freeze retrospective documents transparently, complete the draft release evidence, and rerun reproducibility review. |

## Major issues

| ID | Finding | Current mitigation | Remaining action |
| :--- | :--- | :--- | :--- |
| M1 | Resampling and cross-validation were row-based rather than grouped by `subject_id`; the number of repeated admissions has not been documented. | Prediction results were removed from the submission manuscript; bootstrap limitation is disclosed. | Count repeats and rerun retained resampling grouped by patient if repeats exist. |
| M2 | Excluding patients who received at least 5 red-cell units within 24 h is a post-entry, study-specific restriction that may select on early treatment/severity. | The threshold is described as operational, not validated; selection bias is disclosed. | Run an include-all sensitivity analysis or freeze a post hoc justification. |
| M3 | Physiological features collected over 0-48 h may overlap hospital death and give shorter stays less measurement opportunity. | All principal language now describes same-hospital associations, not 48 h prognosis. | Authors must accept this estimand or authorize a 48 h landmark reanalysis. |
| M4 | The ICD/text NSAH identification algorithm was not validated against manual chart review, particularly across MIMIC and eICU. | Absence of validation is stated in Methods, Discussion, and RECORD mapping. | Add supporting validation evidence or perform validation if feasible. |

## Resolved during review

- Replaced invalid/ambiguous legacy references and corrected SAHARA year/outcome wording.
- Added exact dataset-version, PhysioNet, STROBE, and RECORD citations.
- Promoted the citation-aware text to the repository's canonical English and Chinese manuscripts.
- Removed prediction-model results from the submission package because they were non-central and methodologically unresolved.
- Reduced overclaiming from “risk prediction” to observed same-hospital mortality association.
- Reduced the structured abstract to 250 words or fewer and the main display set to three figures.
- Moved the cohort flow diagram to ESM Fig. 8 and synchronized checklist references.
- Completed an English/Chinese language cleanup and corrected the Chinese sample-count typo.
- Regenerated all referenced figures as 600 dpi PNG plus vector PDF, removed conflicting embedded numbers, and passed visual QA.
- Corrected the MIMIC-IV 3.1 coverage period to 2008-2022 using the official version page.
- Reconciled phenotype labeling with the code: labels use an outcome-blind physiological severity score, not mortality ordering.
- Added a v2 study manifest, run manifest, pipeline DAG, seed registry, deviation log, artifact provenance table, governance record, and structured issue register.
- Added a tested compiler guard that prevents unresolved Pandoc citation keys from being rendered into a misleading PDF.

## Review conclusion

The repeat review remains **REVISE**. The manuscript is materially closer to submission, its citation base is defensible, and the figure-production risk is resolved. The package should not be uploaded until B1-B3 are closed. M1-M4 require authorized reanalysis or explicit, documented author decisions. The authoritative handoff list is `author_completion_checklist.md`.
