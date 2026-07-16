# Literature search log

## Review scope

- Review type: Targeted citation update and rapid evidence verification; this is not a systematic review.
- Clinical question: Which authoritative records support background and methods claims for early neuro-systemic physiological phenotypes and outcomes in adult non-traumatic or aneurysmal subarachnoid hemorrhage (SAH), including systemic organ dysfunction, anemia/transfusion, severity scales, critical-care phenotyping, database provenance, transportability, and reporting guidance?
- Population: Adults with non-traumatic SAH or aneurysmal SAH; broader critically ill adult cohorts were eligible only for general severity scales or phenotype methodology.
- Exposure/intervention: Early physiology and organ dysfunction; anemia/hemoglobin and red-cell transfusion strategies; unsupervised phenotype derivation and transport.
- Comparator: As defined by each report (for example liberal versus restrictive transfusion, phenotype classes, or validation cohorts); none required for descriptive database or reporting records.
- Outcomes: Mortality, neurological/functional outcomes, organ dysfunction, phenotype reproducibility/transport, and reporting or provenance suitability.
- Eligible designs: Authoritative guidelines and original scale statements; randomized and observational clinical studies; relevant reviews; database/data-resource descriptions; official PhysioNet version records; STROBE/RECORD statements.
- Exclusions: Pediatric-only or traumatic SAH; non-SAH transfusion studies without methodological relevance; case reports; non-clinical studies; non-authoritative database summaries; records unable to support an audited manuscript claim.
- Date/language limits: English language, publication dates from 1800-01-01 through 2026-07-15. The lower bound operationalizes database inception for the E-utilities request.
- MIMIC-specific novelty question: Does published work already establish a reproducible, externally transported early multimodal neuro-systemic phenotype framework for adult non-traumatic SAH across MIMIC-IV and eICU-CRD? The targeted search found related MIMIC SAH analyses and general ICU phenotype studies, but did not establish an identical prior framework; this is a scoped observation, not proof of exhaustive novelty.
- Privacy boundary: Only public search terms, titles, DOI values, and PMID values were sent to external services. No manuscript results or patient-level data were uploaded.

## PubMed/MEDLINE searches

Platform for all rows: PubMed via NCBI E-utilities ESearch. Original search date: 2026-07-15; audit rerun: 2026-07-16; coverage end held at 2026-07-15. Every rerun used the literal request parameters `db=pubmed`, `retmode=json`, `retmax=20`, `sort=relevance`, `datetype=pdat`, `mindate=1800/01/01`, and `maxdate=2026/07/15`; the `term` value is the exact query shown below. Raw counts are the ESearch `count` before screening or deduplication. Language was enforced inside every `term` with `english[lang]`.

| ID | Database and platform | Exact query as executed | Filters/limits | Raw results | Export or URL | Notes |
|---|---|---|---|---:|---|---|
| Q1 | PubMed/MEDLINE (NCBI E-utilities) | `("Subarachnoid Hemorrhage"[Mesh] OR "subarachnoid hemorrhage"[tiab] OR "subarachnoid haemorrhage"[tiab]) AND ("systemic inflammation"[tiab] OR extracerebral[tiab] OR "organ dysfunction"[tiab] OR "cardiac dysfunction"[tiab] OR "pulmonary complications"[tiab] OR "renal dysfunction"[tiab]) AND english[lang]` | Shared parameters above; English; first 20 relevance-ranked records returned | 325 | Exact query and parameters are rerunnable; returned PMIDs audited below | SAH systemic/extracerebral complications. |
| Q2 | PubMed/MEDLINE (NCBI E-utilities) | `("Subarachnoid Hemorrhage"[Mesh] OR "subarachnoid hemorrhage"[tiab] OR "subarachnoid haemorrhage"[tiab]) AND (anemia[tiab] OR anaemia[tiab] OR hemoglobin[tiab] OR haemoglobin[tiab] OR "red blood cell transfusion"[tiab] OR transfusion[tiab]) AND english[lang]` | Shared parameters above; English; first 20 relevance-ranked records returned | 737 | Exact query and parameters are rerunnable; returned PMIDs audited below | SAH anemia/transfusion. |
| Q3 | PubMed/MEDLINE (NCBI E-utilities) | `(("Critical Illness"[Mesh] OR "critical illness"[tiab] OR "critical care"[tiab] OR ICU[tiab] OR sepsis[tiab] OR "acute respiratory distress syndrome"[tiab]) AND (phenotyp*[tiab] OR subphenotyp*[tiab] OR cluster*[tiab]) AND (unsupervised[tiab] OR "latent class"[tiab] OR "machine learning"[tiab] OR k-means[tiab])) AND english[lang]` | Shared parameters above; English; first 20 relevance-ranked records returned | 777 | Exact query and parameters are rerunnable; returned PMIDs audited below | Critical-care phenotyping. |
| Q4 | PubMed/MEDLINE (NCBI E-utilities) | `((MIMIC-IV[tiab] OR "Medical Information Mart for Intensive Care IV"[tiab] OR eICU-CRD[tiab] OR "eICU Collaborative Research Database"[tiab] OR PhysioNet[tiab]) AND (database[tiab] OR dataset[tiab] OR "data resource"[tiab])) AND english[lang]` | Shared parameters above; English; first 20 relevance-ranked records returned | 4236 | Exact query and parameters are rerunnable; returned PMIDs audited below | Broad count reflects frequent downstream analyses that mention the database names. |
| Q5 | PubMed/MEDLINE (NCBI E-utilities) | `((("subarachnoid hemorrhage"[tiab] OR "subarachnoid haemorrhage"[tiab]) AND ("Hunt and Hess"[tiab] OR "World Federation of Neurosurgical Societies"[tiab] OR WFNS[tiab] OR "Glasgow Coma Scale"[tiab])) OR ("APACHE II"[tiab] OR "Sequential Organ Failure Assessment"[tiab] OR "STROBE statement"[tiab] OR "RECORD statement"[tiab])) AND english[lang]` | Shared parameters above; English; first 20 relevance-ranked records returned | 17977 | Exact query and parameters are rerunnable; returned PMIDs audited below | Audit rerun added the previously missing English filter; the old 19,554 count is superseded. |

Raw aggregate across the audited Q1–Q5 rerun was 24,052 citations before deduplication; this sum is not a count of unique studies. The first 20 relevance-ranked records from each query produced 100 candidate slots and 100 unique PMIDs. Legacy-reference identity searches and known-item checks were performed separately and are not added to the raw aggregate.

## Candidate-level screening trace

The table below is the complete ordered `retmax=20` response from each audited ESearch call. All 100 PMIDs were unique, so `duplicate_group` is `none` throughout. Screening used PubMed title/abstract metadata; excluded records were not advanced to full text. Controlled reasons: `INC-CORE` (retained in the evidence table), `EXC-PRECLINICAL`, `EXC-WRONG-POPULATION`, `EXC-PUBLICATION-TYPE`, `EXC-NOT-SOURCE-RECORD`, `EXC-NOT-CANONICAL`, `EXC-INDIRECT-OR-REDUNDANT`, and `EXC-NARROW-OR-REDUNDANT`.

| screening_id | query | rank | PMID | duplicate_group | title/abstract decision | full-text decision | reason | reviewer note |
|---|---|---:|---:|---|---|---|---|---|
| Q1-01 | Q1 | 1 | 28775014 | none | exclude | not_assessed | EXC-NARROW-OR-REDUNDANT | Potentially related but narrower or redundant with the retained guideline/review/trial evidence |
| Q1-02 | Q1 | 2 | 32986813 | none | exclude | not_assessed | EXC-NARROW-OR-REDUNDANT | Potentially related but narrower or redundant with the retained guideline/review/trial evidence |
| Q1-03 | Q1 | 3 | 27885969 | none | exclude | not_assessed | EXC-PUBLICATION-TYPE | Conference supplement rather than a directly usable report |
| Q1-04 | Q1 | 4 | 37936706 | none | exclude | not_assessed | EXC-NARROW-OR-REDUNDANT | Potentially related but narrower or redundant with the retained guideline/review/trial evidence |
| Q1-05 | Q1 | 5 | 37446118 | none | include | abstract_or_metadata_extracted | INC-CORE | Retained as EV-003 |
| Q1-06 | Q1 | 6 | 40378483 | none | exclude | not_assessed | EXC-NARROW-OR-REDUNDANT | Potentially related but narrower or redundant with the retained guideline/review/trial evidence |
| Q1-07 | Q1 | 7 | 11527524 | none | exclude | not_assessed | EXC-NARROW-OR-REDUNDANT | Potentially related but narrower or redundant with the retained guideline/review/trial evidence |
| Q1-08 | Q1 | 8 | 36476130 | none | exclude | not_assessed | EXC-NARROW-OR-REDUNDANT | Potentially related but narrower or redundant with the retained guideline/review/trial evidence |
| Q1-09 | Q1 | 9 | 33618416 | none | exclude | not_assessed | EXC-NARROW-OR-REDUNDANT | Potentially related but narrower or redundant with the retained guideline/review/trial evidence |
| Q1-10 | Q1 | 10 | 34525222 | none | exclude | not_assessed | EXC-NARROW-OR-REDUNDANT | Potentially related but narrower or redundant with the retained guideline/review/trial evidence |
| Q1-11 | Q1 | 11 | 25105123 | none | exclude | not_assessed | EXC-NARROW-OR-REDUNDANT | Potentially related but narrower or redundant with the retained guideline/review/trial evidence |
| Q1-12 | Q1 | 12 | 33556594 | none | exclude | not_assessed | EXC-NARROW-OR-REDUNDANT | Potentially related but narrower or redundant with the retained guideline/review/trial evidence |
| Q1-13 | Q1 | 13 | 17544451 | none | exclude | not_assessed | EXC-NARROW-OR-REDUNDANT | Potentially related but narrower or redundant with the retained guideline/review/trial evidence |
| Q1-14 | Q1 | 14 | 26836901 | none | exclude | not_assessed | EXC-NARROW-OR-REDUNDANT | Potentially related but narrower or redundant with the retained guideline/review/trial evidence |
| Q1-15 | Q1 | 15 | 36346451 | none | exclude | not_assessed | EXC-NARROW-OR-REDUNDANT | Potentially related but narrower or redundant with the retained guideline/review/trial evidence |
| Q1-16 | Q1 | 16 | 31993953 | none | exclude | not_assessed | EXC-NARROW-OR-REDUNDANT | Potentially related but narrower or redundant with the retained guideline/review/trial evidence |
| Q1-17 | Q1 | 17 | 41227384 | none | exclude | not_assessed | EXC-NARROW-OR-REDUNDANT | Potentially related but narrower or redundant with the retained guideline/review/trial evidence |
| Q1-18 | Q1 | 18 | 30961425 | none | exclude | not_assessed | EXC-NARROW-OR-REDUNDANT | Potentially related but narrower or redundant with the retained guideline/review/trial evidence |
| Q1-19 | Q1 | 19 | 41412009 | none | exclude | not_assessed | EXC-NARROW-OR-REDUNDANT | Potentially related but narrower or redundant with the retained guideline/review/trial evidence |
| Q1-20 | Q1 | 20 | 21761273 | none | exclude | not_assessed | EXC-NARROW-OR-REDUNDANT | Potentially related but narrower or redundant with the retained guideline/review/trial evidence |
| Q2-01 | Q2 | 1 | 39382241 | none | exclude | not_assessed | EXC-NARROW-OR-REDUNDANT | Potentially related but narrower or redundant with the retained guideline/review/trial evidence |
| Q2-02 | Q2 | 2 | 37202712 | none | exclude | not_assessed | EXC-NARROW-OR-REDUNDANT | Potentially related but narrower or redundant with the retained guideline/review/trial evidence |
| Q2-03 | Q2 | 3 | 39655786 | none | include | abstract_or_metadata_extracted | INC-CORE | Retained as EV-007 |
| Q2-04 | Q2 | 4 | 28722880 | none | exclude | not_assessed | EXC-WRONG-POPULATION | Population/topic outside adult SAH or general adult critical-care phenotype scope |
| Q2-05 | Q2 | 5 | 39030593 | none | exclude | not_assessed | EXC-PRECLINICAL | Animal, molecular, or omics study not direct clinical evidence for the audited claim set |
| Q2-06 | Q2 | 6 | 39034417 | none | exclude | not_assessed | EXC-PRECLINICAL | Animal, molecular, or omics study not direct clinical evidence for the audited claim set |
| Q2-07 | Q2 | 7 | 40108663 | none | exclude | not_assessed | EXC-PRECLINICAL | Animal, molecular, or omics study not direct clinical evidence for the audited claim set |
| Q2-08 | Q2 | 8 | 39981761 | none | exclude | not_assessed | EXC-PRECLINICAL | Animal, molecular, or omics study not direct clinical evidence for the audited claim set |
| Q2-09 | Q2 | 9 | 34480226 | none | exclude | not_assessed | EXC-NARROW-OR-REDUNDANT | Potentially related but narrower or redundant with the retained guideline/review/trial evidence |
| Q2-10 | Q2 | 10 | 41328986 | none | exclude | not_assessed | EXC-NARROW-OR-REDUNDANT | Potentially related but narrower or redundant with the retained guideline/review/trial evidence |
| Q2-11 | Q2 | 11 | 37232189 | none | exclude | not_assessed | EXC-NARROW-OR-REDUNDANT | Potentially related but narrower or redundant with the retained guideline/review/trial evidence |
| Q2-12 | Q2 | 12 | 39346537 | none | exclude | not_assessed | EXC-PRECLINICAL | Animal, molecular, or omics study not direct clinical evidence for the audited claim set |
| Q2-13 | Q2 | 13 | 25535426 | none | exclude | not_assessed | EXC-NARROW-OR-REDUNDANT | Potentially related but narrower or redundant with the retained guideline/review/trial evidence |
| Q2-14 | Q2 | 14 | 25366599 | none | exclude | not_assessed | EXC-NARROW-OR-REDUNDANT | Potentially related but narrower or redundant with the retained guideline/review/trial evidence |
| Q2-15 | Q2 | 15 | 25051263 | none | exclude | not_assessed | EXC-NARROW-OR-REDUNDANT | Potentially related but narrower or redundant with the retained guideline/review/trial evidence |
| Q2-16 | Q2 | 16 | 20380973 | none | exclude | not_assessed | EXC-NARROW-OR-REDUNDANT | Potentially related but narrower or redundant with the retained guideline/review/trial evidence |
| Q2-17 | Q2 | 17 | 37634181 | none | exclude | not_assessed | EXC-NARROW-OR-REDUNDANT | Potentially related but narrower or redundant with the retained guideline/review/trial evidence |
| Q2-18 | Q2 | 18 | 27740993 | none | exclude | not_assessed | EXC-NARROW-OR-REDUNDANT | Potentially related but narrower or redundant with the retained guideline/review/trial evidence |
| Q2-19 | Q2 | 19 | 11949877 | none | exclude | not_assessed | EXC-NARROW-OR-REDUNDANT | Potentially related but narrower or redundant with the retained guideline/review/trial evidence |
| Q2-20 | Q2 | 20 | 28168536 | none | exclude | not_assessed | EXC-NARROW-OR-REDUNDANT | Potentially related but narrower or redundant with the retained guideline/review/trial evidence |
| Q3-01 | Q3 | 1 | 34213593 | none | exclude | not_assessed | EXC-INDIRECT-OR-REDUNDANT | Review, biomarker/endotype, or treatment-stratification study not needed beyond retained sepsis/ARDS exemplars |
| Q3-02 | Q3 | 2 | 31104070 | none | include | abstract_or_metadata_extracted | INC-CORE | Retained as EV-008 |
| Q3-03 | Q3 | 3 | 40163135 | none | exclude | not_assessed | EXC-INDIRECT-OR-REDUNDANT | Review, biomarker/endotype, or treatment-stratification study not needed beyond retained sepsis/ARDS exemplars |
| Q3-04 | Q3 | 4 | 33165028 | none | exclude | not_assessed | EXC-INDIRECT-OR-REDUNDANT | Review, biomarker/endotype, or treatment-stratification study not needed beyond retained sepsis/ARDS exemplars |
| Q3-05 | Q3 | 5 | 24853585 | none | include | abstract_or_metadata_extracted | INC-CORE | Retained as EV-009 |
| Q3-06 | Q3 | 6 | 38035100 | none | exclude | not_assessed | EXC-INDIRECT-OR-REDUNDANT | Review, biomarker/endotype, or treatment-stratification study not needed beyond retained sepsis/ARDS exemplars |
| Q3-07 | Q3 | 7 | 40013975 | none | exclude | not_assessed | EXC-WRONG-POPULATION | Population/topic outside adult SAH or general adult critical-care phenotype scope |
| Q3-08 | Q3 | 8 | 39040114 | none | exclude | not_assessed | EXC-INDIRECT-OR-REDUNDANT | Review, biomarker/endotype, or treatment-stratification study not needed beyond retained sepsis/ARDS exemplars |
| Q3-09 | Q3 | 9 | 40972498 | none | exclude | not_assessed | EXC-INDIRECT-OR-REDUNDANT | Review, biomarker/endotype, or treatment-stratification study not needed beyond retained sepsis/ARDS exemplars |
| Q3-10 | Q3 | 10 | 36470834 | none | exclude | not_assessed | EXC-INDIRECT-OR-REDUNDANT | Review, biomarker/endotype, or treatment-stratification study not needed beyond retained sepsis/ARDS exemplars |
| Q3-11 | Q3 | 11 | 38239341 | none | exclude | not_assessed | EXC-PRECLINICAL | Animal, molecular, or omics study not direct clinical evidence for the audited claim set |
| Q3-12 | Q3 | 12 | 34883088 | none | exclude | not_assessed | EXC-WRONG-POPULATION | Population/topic outside adult SAH or general adult critical-care phenotype scope |
| Q3-13 | Q3 | 13 | 28864056 | none | exclude | not_assessed | EXC-INDIRECT-OR-REDUNDANT | Review, biomarker/endotype, or treatment-stratification study not needed beyond retained sepsis/ARDS exemplars |
| Q3-14 | Q3 | 14 | 38029626 | none | exclude | not_assessed | EXC-PRECLINICAL | Animal, molecular, or omics study not direct clinical evidence for the audited claim set |
| Q3-15 | Q3 | 15 | 37633303 | none | exclude | not_assessed | EXC-INDIRECT-OR-REDUNDANT | Review, biomarker/endotype, or treatment-stratification study not needed beyond retained sepsis/ARDS exemplars |
| Q3-16 | Q3 | 16 | 40360520 | none | exclude | not_assessed | EXC-INDIRECT-OR-REDUNDANT | Review, biomarker/endotype, or treatment-stratification study not needed beyond retained sepsis/ARDS exemplars |
| Q3-17 | Q3 | 17 | 30078618 | none | exclude | not_assessed | EXC-INDIRECT-OR-REDUNDANT | Review, biomarker/endotype, or treatment-stratification study not needed beyond retained sepsis/ARDS exemplars |
| Q3-18 | Q3 | 18 | 29537985 | none | exclude | not_assessed | EXC-INDIRECT-OR-REDUNDANT | Review, biomarker/endotype, or treatment-stratification study not needed beyond retained sepsis/ARDS exemplars |
| Q3-19 | Q3 | 19 | 40898225 | none | exclude | not_assessed | EXC-PRECLINICAL | Animal, molecular, or omics study not direct clinical evidence for the audited claim set |
| Q3-20 | Q3 | 20 | 37701433 | none | exclude | not_assessed | EXC-PRECLINICAL | Animal, molecular, or omics study not direct clinical evidence for the audited claim set |
| Q4-01 | Q4 | 1 | 37653418 | none | exclude | not_assessed | EXC-NOT-SOURCE-RECORD | Downstream database analysis or bibliometric paper, not an authoritative MIMIC/eICU source descriptor |
| Q4-02 | Q4 | 2 | 36596836 | none | include | abstract_or_metadata_extracted | INC-CORE | Retained as EV-010 |
| Q4-03 | Q4 | 3 | 40418571 | none | exclude | not_assessed | EXC-NOT-SOURCE-RECORD | Downstream database analysis or bibliometric paper, not an authoritative MIMIC/eICU source descriptor |
| Q4-04 | Q4 | 4 | 39059317 | none | exclude | not_assessed | EXC-NOT-SOURCE-RECORD | Downstream database analysis or bibliometric paper, not an authoritative MIMIC/eICU source descriptor |
| Q4-05 | Q4 | 5 | 37542106 | none | exclude | not_assessed | EXC-NOT-SOURCE-RECORD | Downstream database analysis or bibliometric paper, not an authoritative MIMIC/eICU source descriptor |
| Q4-06 | Q4 | 6 | 40065235 | none | exclude | not_assessed | EXC-NOT-SOURCE-RECORD | Downstream database analysis or bibliometric paper, not an authoritative MIMIC/eICU source descriptor |
| Q4-07 | Q4 | 7 | 38882552 | none | exclude | not_assessed | EXC-NOT-SOURCE-RECORD | Downstream database analysis or bibliometric paper, not an authoritative MIMIC/eICU source descriptor |
| Q4-08 | Q4 | 8 | 40096948 | none | exclude | not_assessed | EXC-NOT-SOURCE-RECORD | Downstream database analysis or bibliometric paper, not an authoritative MIMIC/eICU source descriptor |
| Q4-09 | Q4 | 9 | 40896465 | none | exclude | not_assessed | EXC-NOT-SOURCE-RECORD | Downstream database analysis or bibliometric paper, not an authoritative MIMIC/eICU source descriptor |
| Q4-10 | Q4 | 10 | 36059447 | none | exclude | not_assessed | EXC-NOT-SOURCE-RECORD | Downstream database analysis or bibliometric paper, not an authoritative MIMIC/eICU source descriptor |
| Q4-11 | Q4 | 11 | 38954672 | none | exclude | not_assessed | EXC-NOT-SOURCE-RECORD | Downstream database analysis or bibliometric paper, not an authoritative MIMIC/eICU source descriptor |
| Q4-12 | Q4 | 12 | 37696627 | none | exclude | not_assessed | EXC-NOT-SOURCE-RECORD | Downstream database analysis or bibliometric paper, not an authoritative MIMIC/eICU source descriptor |
| Q4-13 | Q4 | 13 | 38617935 | none | exclude | not_assessed | EXC-NOT-SOURCE-RECORD | Downstream database analysis or bibliometric paper, not an authoritative MIMIC/eICU source descriptor |
| Q4-14 | Q4 | 14 | 39290253 | none | exclude | not_assessed | EXC-NOT-SOURCE-RECORD | Downstream database analysis or bibliometric paper, not an authoritative MIMIC/eICU source descriptor |
| Q4-15 | Q4 | 15 | 39072271 | none | exclude | not_assessed | EXC-NOT-SOURCE-RECORD | Downstream database analysis or bibliometric paper, not an authoritative MIMIC/eICU source descriptor |
| Q4-16 | Q4 | 16 | 39288404 | none | exclude | not_assessed | EXC-NOT-SOURCE-RECORD | Downstream database analysis or bibliometric paper, not an authoritative MIMIC/eICU source descriptor |
| Q4-17 | Q4 | 17 | 40540448 | none | exclude | not_assessed | EXC-NOT-SOURCE-RECORD | Downstream database analysis or bibliometric paper, not an authoritative MIMIC/eICU source descriptor |
| Q4-18 | Q4 | 18 | 40456706 | none | exclude | not_assessed | EXC-NOT-SOURCE-RECORD | Downstream database analysis or bibliometric paper, not an authoritative MIMIC/eICU source descriptor |
| Q4-19 | Q4 | 19 | 40814334 | none | exclude | not_assessed | EXC-NOT-SOURCE-RECORD | Downstream database analysis or bibliometric paper, not an authoritative MIMIC/eICU source descriptor |
| Q4-20 | Q4 | 20 | 38630522 | none | exclude | not_assessed | EXC-NOT-SOURCE-RECORD | Downstream database analysis or bibliometric paper, not an authoritative MIMIC/eICU source descriptor |
| Q5-01 | Q5 | 1 | 30020670 | none | exclude | not_assessed | EXC-NOT-CANONICAL | Outcome/complication study or secondary summary, not the canonical scale/reporting source sought |
| Q5-02 | Q5 | 2 | 26440803 | none | include | abstract_or_metadata_extracted | INC-CORE | Retained as EV-022 |
| Q5-03 | Q5 | 3 | 38836919 | none | exclude | not_assessed | EXC-NOT-CANONICAL | Outcome/complication study or secondary summary, not the canonical scale/reporting source sought |
| Q5-04 | Q5 | 4 | 12074438 | none | exclude | not_assessed | EXC-NOT-CANONICAL | Outcome/complication study or secondary summary, not the canonical scale/reporting source sought |
| Q5-05 | Q5 | 5 | 32312942 | none | exclude | not_assessed | EXC-NOT-CANONICAL | Outcome/complication study or secondary summary, not the canonical scale/reporting source sought |
| Q5-06 | Q5 | 6 | 30819681 | none | exclude | not_assessed | EXC-NOT-CANONICAL | Outcome/complication study or secondary summary, not the canonical scale/reporting source sought |
| Q5-07 | Q5 | 7 | 34806656 | none | exclude | not_assessed | EXC-NOT-CANONICAL | Outcome/complication study or secondary summary, not the canonical scale/reporting source sought |
| Q5-08 | Q5 | 8 | 40564163 | none | exclude | not_assessed | EXC-NOT-CANONICAL | Outcome/complication study or secondary summary, not the canonical scale/reporting source sought |
| Q5-09 | Q5 | 9 | 37873354 | none | exclude | not_assessed | EXC-NOT-CANONICAL | Outcome/complication study or secondary summary, not the canonical scale/reporting source sought |
| Q5-10 | Q5 | 10 | 30735864 | none | exclude | not_assessed | EXC-NOT-CANONICAL | Outcome/complication study or secondary summary, not the canonical scale/reporting source sought |
| Q5-11 | Q5 | 11 | 25280913 | none | exclude | not_assessed | EXC-NOT-CANONICAL | Outcome/complication study or secondary summary, not the canonical scale/reporting source sought |
| Q5-12 | Q5 | 12 | 23298672 | none | exclude | not_assessed | EXC-NOT-CANONICAL | Outcome/complication study or secondary summary, not the canonical scale/reporting source sought |
| Q5-13 | Q5 | 13 | 28409729 | none | exclude | not_assessed | EXC-NOT-CANONICAL | Outcome/complication study or secondary summary, not the canonical scale/reporting source sought |
| Q5-14 | Q5 | 14 | 35773634 | none | exclude | not_assessed | EXC-NOT-CANONICAL | Outcome/complication study or secondary summary, not the canonical scale/reporting source sought |
| Q5-15 | Q5 | 15 | 40951928 | none | exclude | not_assessed | EXC-NOT-CANONICAL | Outcome/complication study or secondary summary, not the canonical scale/reporting source sought |
| Q5-16 | Q5 | 16 | 33682040 | none | exclude | not_assessed | EXC-NOT-CANONICAL | Outcome/complication study or secondary summary, not the canonical scale/reporting source sought |
| Q5-17 | Q5 | 17 | 39486277 | none | exclude | not_assessed | EXC-NOT-CANONICAL | Outcome/complication study or secondary summary, not the canonical scale/reporting source sought |
| Q5-18 | Q5 | 18 | 35967154 | none | exclude | not_assessed | EXC-NOT-CANONICAL | Outcome/complication study or secondary summary, not the canonical scale/reporting source sought |
| Q5-19 | Q5 | 19 | 31707576 | none | exclude | not_assessed | EXC-NOT-CANONICAL | Outcome/complication study or secondary summary, not the canonical scale/reporting source sought |
| Q5-20 | Q5 | 20 | 34472399 | none | exclude | not_assessed | EXC-NOT-CANONICAL | Outcome/complication study or secondary summary, not the canonical scale/reporting source sought |


## Supplementary known-item verification

- PubMed PMID resolution and metadata: `https://pubmed.ncbi.nlm.nih.gov/<PMID>/` and NCBI ESummary/EFetch, checked 2026-07-15.
- DOI resolution: `https://doi.org/<DOI>`, checked 2026-07-15. HTTP 403/405 from a publisher after DOI routing was treated as access blocking, not DOI failure, when PubMed metadata and the DOI registry route agreed.
- Official dataset records: [MIMIC-IV v3.1](https://physionet.org/content/mimiciv/3.1/) and [eICU-CRD v2.0](https://physionet.org/content/eicu-crd/2.0/), checked 2026-07-15.
- Citation chaining/known-item additions: the AHA/ASA 2023 aSAH guideline; original WFNS scale report; APACHE IV; RECORD; the SAHARA trial; and related anemia/phenotype reports. These were added to fill explicit claim gaps, not by unrestricted browsing.

## Screening summary

| Stage | Count |
|---|---:|
| Raw results across five audited queries (non-unique aggregate) | 24,052 |
| Relevance-ranked candidate slots inspected (20/query) | 100 |
| Unique PMIDs in that bounded candidate set | 100 |
| Legacy citation strings independently checked | 13 |
| Retained authoritative evidence records | 22 |
| Retained PubMed records assessed from metadata/abstract | 20 |
| Retained official dataset-version records assessed from full web record | 2 |

The workflow did not export and screen all 24,052 records. Counts therefore describe a reproducible targeted update, not PRISMA flow or systematic-review completeness.

## Key identity findings

- Legacy reference 5 could not be verified as written. Its title/journal/pages do not resolve to a PubMed or DOI record and appear to combine details from distinct Naidech publications. It remains `conflict`/ineligible; PMID 17717494 is a verified related report, not an assumed repair.
- Legacy reference 9 maps by title and authors to PMID 39655786 / DOI 10.1056/NEJMoa2410962, published online 2024-12-09 but assigned to the 2025 print volume. The incomplete “N Engl J Med. 2024” string is retained as a conflict and is not bibliography-eligible; the authoritative 2025 record is separately eligible.
- Legacy reference 10 resolves to PMID 37446118 / DOI 10.3390/ijms241310943; the old string omitted authors.
- The AHA/ASA 2023 guideline has a linked erratum (PMID 38011240). It does not change the guideline's bibliographic identity. The correction text was not accessible in this audit, so no claim-level assertion is made that it is immaterial; the corrected guideline must be consulted before citing a specific recommendation. This evidence table uses the guideline only for broad aSAH clinical context.
- The MIMIC-IV data paper has two linked author corrections (PMIDs 36646711 and 37072428). The first restored missing “Hospital admissions” and “ICU admissions” headings in Table 1; the second restored omitted author Sicheng Hao and associated metadata. These do not alter the paper's identity or the limited provenance/content claim for which it is retained.
- The eICU source paper and official PhysioNet v2.0 record establish database provenance/version. The official eICU v2.0 SchemaSpy page confirms that `apachepatientresult` contains `acutephysiologyscore`, `apachescore`, `apacheversion`, predicted/actual ICU and hospital mortality, and predicted/actual length-of-stay fields. It does **not** establish the version value used in the manuscript extract or validate these fields as independent NSAH criterion measures. EV-019 therefore supplies APACHE IV model background only, and CLM-016 remains an evidence gap pending extraction-level version audit and population-appropriate validation.

## Deviations and limitations

- This was a targeted citation update, not a registered or systematic review. Only PubMed/MEDLINE was searched bibliographically; Embase, Web of Science, Scopus, and Cochrane Central were not searched.
- Screening was bounded to the first 20 relevance-ranked results per broad query plus explicit legacy/known-item verification. Raw-result counts can change with future indexing even when the query is unchanged.
- Evidence extraction for most journal records was abstract/metadata-only. Original older scale papers without abstracts were assessed at metadata/title level; claims requiring detailed full-text methods should be rechecked by a human with full-text access before submission.
- Paywall or anti-bot restrictions affected some publisher pages. Identifier identity was accepted only when PubMed metadata and DOI routing agreed; access restriction is recorded in the evidence table.
- The search did not find direct, claim-complete support for a 5-unit/24-hour transfusion exclusion threshold, the comparative scarcity of neurocritical phenotyping, or the superiority of fixed classifier transport over de novo reclustering. These claims should remain operational/cautious rather than be upgraded through indirect evidence.
- Evidence current through: 2026-07-15.
