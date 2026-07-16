# RECORD Statement Checklist

Study: Early physiological phenotypes and outcomes in critically ill adults with non-traumatic subarachnoid hemorrhage

Design: Retrospective cohort study using routinely collected MIMIC-IV 3.1 data with external validation in eICU-CRD 2.0.

Source: Benchimol EI, et al. The RECORD Statement. PLoS Med. 2015;12:e1001885. DOI: 10.1371/journal.pmed.1001885. Checklist wording was verified against the open-access article on 2026-07-16.

| RECORD item | Recommendation, abbreviated | Manuscript or artifact location | Status |
| :--- | :--- | :--- | :--- |
| 1.1 | Identify the routinely collected data and, where possible, databases in title or abstract | Structured Abstract, Methods | Addressed |
| 1.2 | Report geographic region and study time frame in title or abstract, if applicable | Structured Abstract, Methods (2008-2022; 2014-2015); US setting in Discussion | Addressed |
| 1.3 | State database linkage in title or abstract, if applicable | MIMIC and eICU cohorts were analyzed separately; no person-level linkage | Not applicable |
| 6.1 | Detail codes or algorithms used to select the study population | Methods, Cohort; ESM Tables 1-3; cohort SQL | Addressed |
| 6.2 | Cite validation studies of population-selection codes/algorithms or report study-specific validation | Methods and Discussion explicitly state that no manual-chart validation was performed | Addressed as a limitation; validation remains desirable |
| 6.3 | Show linkage process and counts when databases are linked | Databases were not linked; ESM Fig. 8 shows separate cohort flows | Not applicable |
| 7.1 | Provide complete codes and algorithms for exposures, outcomes, confounders, and effect modifiers | ESM Tables 3-6; SQL and analysis scripts | Addressed, final code release pending |
| 12.1 | Describe investigators' access to the database population used to create the cohort | Methods and Data availability describe credentialed access | Partly addressed; author must confirm access statement |
| 12.2 | Describe data-cleaning methods | Methods, Variables and preprocessing; ESM Tables 4-6; analysis code | Addressed |
| 12.3 | State whether person-, institution-, or other-level linkage occurred and describe linkage quality | MIMIC and eICU cohorts were analyzed separately; no cross-database linkage | Not applicable |
| 13.1 | Detail participant selection, including data-quality, availability, and linkage filters | Methods; ESM Fig. 8; ESM Tables 1-2 | Addressed |
| 19.1 | Discuss implications of data not collected for the research question, including misclassification, unmeasured confounding, missingness, and changing eligibility | Discussion, limitations | Addressed; code-validation limitation remains open |
| 22.1 | Explain access to protocol, raw data, or programming code | Data and Code availability; ESM reproducibility notes | Partly addressed; repository/release URL pending |

## Open items before submission

- If feasible, externally support or validate the ICD/text-based NSAH identification algorithm; the current manuscript explicitly discloses the absence of manual-chart validation.
- Authors must confirm that the credentialing/training/data-use statement accurately describes every analyst who accessed MIMIC-IV or eICU.
- Replace the provisional code-availability wording with a permanent repository or supplementary-code location.
