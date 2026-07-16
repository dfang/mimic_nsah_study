# External Evidence for the NSAH Identification Rule

**Review date:** 2026-07-16
**Rule under review:** adult inpatient SAH identified by normalized ICD-9-CM `430%` or ICD-10-CM `I60%`, with admissions carrying traumatic-SAH evidence excluded.

## Evidence

- McCormick et al. systematically reviewed administrative-code validation studies and found substantial between-study variability. For SAH-specific validation, at least half of included studies reported positive predictive values of at least 93%, but sensitivity estimates were less consistently available and varied widely. DOI: [10.1371/journal.pone.0135834](https://doi.org/10.1371/journal.pone.0135834); PMID: [26292280](https://pubmed.ncbi.nlm.nih.gov/26292280/).
- Hsieh et al. validated ICD-10-CM hemorrhagic-stroke codes against a registry plus medical-record and imaging review. Performance depended strongly on diagnosis position; this supports using `I60` as a candidate-identification rule but not treating any-field coding as a perfect reference standard. DOI: [10.2147/CLEP.S273259](https://doi.org/10.2147/CLEP.S273259/); PMCID: [PMC7813455](https://pmc.ncbi.nlm.nih.gov/articles/PMC7813455/).
- Øie et al. found materially lower positive predictive value for spontaneous SAH codes in a Danish registry and identified traumatic SAH among important false positives. This directly supports explicit traumatic-SAH exclusion and continued misclassification caution. DOI: [10.1177/1403494819851607](https://doi.org/10.1177/1403494819851607); PMID: [31118820](https://pubmed.ncbi.nlm.nih.gov/31118820/).
- English et al. showed that location-specific `I60.x` codes should be used cautiously for active aneurysmal SAH and aneurysm-location inference. This supports retaining aneurysm diagnosis/procedure evidence as stratification rather than requiring or overinterpreting it in the broader NSAH cohort. DOI: [10.1002/hsr2.384](https://doi.org/10.1002/hsr2.384); PMCID: [PMC8512725](https://pmc.ncbi.nlm.nih.gov/articles/PMC8512725/).

## Applicability decision

The external evidence supports ICD-9-CM `430` and ICD-10-CM `I60` as reasonable candidate-identification codes for an exploratory administrative-data study. It does not establish MIMIC-specific sensitivity or positive predictive value and does not validate the current free-text dictionary-title fallback by itself.

Before the concepts gate can be frozen, the authorized run must:

1. enumerate matched ICD codes and dictionary descriptions without exporting patient-level rows;
2. confirm that `I60`/`430` inclusions and `S06.6`/traumatic-title exclusions behave as intended;
3. report aggregate counts for overlapping nontraumatic and traumatic evidence;
4. retain misclassification as a limitation because manual chart validation is unavailable in this release.

This evidence closes the requirement for an external validation basis only after the MIMIC dictionary audit passes; it does not constitute study-specific diagnostic-accuracy validation.
