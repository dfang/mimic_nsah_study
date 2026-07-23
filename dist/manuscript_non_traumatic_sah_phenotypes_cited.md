---
bibliography: references.bib
csl: journal.csl
link-citations: true
reference-section-title: References
---

# Early physiological phenotypes and outcomes in critically ill adults with non-traumatic subarachnoid hemorrhage

## Take-home message

In critically ill adults with non-traumatic subarachnoid hemorrhage, eight routine physiological variables measured during the first 48 hours defined three early-course phenotypes with different observed in-hospital mortality. Fixed MIMIC-derived assignment preserved this ordering in eICU without replicating cluster boundaries. The adjusted anemia-mortality association was sensitive to whether hemoglobin was included in phenotype derivation.

## Structured abstract

### Purpose

To identify 0-48 h neuro-systemic physiological phenotypes among critically ill adults with non-traumatic subarachnoid hemorrhage (NSAH), describe their same-hospital mortality associations, explore whether anemia estimates depended on phenotype specification, and assess fixed transport in eICU.

### Methods

This retrospective study included 1,186 ICU stays from 1,173 MIMIC-IV 3.1 patients and 843 eICU-CRD 2.0 patients. Eight 0-48 h variables underwent median imputation, log transformation of creatinine and INR, standardization, principal component analysis, and K-means clustering. K=3 was selected from K=2-5 using internal metrics and stability. Logistic regression estimated same-hospital mortality associations; because deaths could occur during feature ascertainment, this was not landmark prediction. A post hoc hemoglobin-free sensitivity analysis examined anemia. Fixed MIMIC parameters and centroids assigned eICU patients.

### Results

P1 (n=694) had relatively preserved physiology, P2 (n=384) had severe neurological impairment, and P3 (n=108) had neurological and multisystem dysfunction. In-hospital mortality was 6.34%, 32.55%, and 61.11%, respectively. Adjusted odds ratios versus P1 were 7.59 (95% CI 5.07-11.36) and 21.21 (12.08-37.26). Mean subject-grouped bootstrap adjusted Rand index was 0.8554. The anemia odds ratio was 0.99 (0.68-1.44) with hemoglobin-containing phenotypes and 1.54 (1.06-2.22) with hemoglobin-free phenotypes. Fixed eICU transport assigned 540, 221, and 82 patients to P1, P2, and P3; mortality was 5.4%, 25.8%, and 42.7%.

### Conclusion

Course-defined NSAH phenotypes showed graded same-hospital mortality, and fixed eICU transport preserved this ordering but did not replicate cluster boundaries. The anemia association was specification-sensitive. Prospective, time-anchored validation is required; these results do not establish treatment effects or bedside predictive utility.

**Keywords:** subarachnoid hemorrhage; critical care; phenotyping; unsupervised learning; transportability.

## Introduction

Non-traumatic subarachnoid hemorrhage (NSAH) is a high-acuity neurological emergency with substantial mortality and long-term disability [@macdonald2017sah]. Clinical grading includes Hunt-Hess, WFNS, and the Glasgow Coma Scale (GCS) [@hunt1968surgicalrisk; @teasdale1988wfns; @teasdale1974gcs]. These scales capture neurological severity but do not incorporate the range of systemic measurements routinely collected in the ICU.

Studies of aneurysmal SAH describe systemic inflammation that may contribute to intracranial and extracranial injury [@chai2023inflammation] and frequent anemia during acute care [@rosenberg2013anemia]. We therefore examined neurological measurements together with renal, hematologic, circulatory, respiratory, and coagulation variables in NSAH. APACHE and SOFA summarize general illness severity and organ dysfunction, respectively, but were not developed to identify NSAH-specific physiological patterns [@knaus1985apacheii; @vincent1996sofa].

Unsupervised analyses have identified clinically distinct subgroups in sepsis and acute respiratory distress syndrome [@seymour2019sepsisphenotypes; @calfee2014ardssubphenotypes]. We applied this approach to early multimodal physiology in neurocritical care. We hypothesized that the resulting NSAH phenotypes would differ in observed mortality and that a classifier derived in MIMIC-IV would preserve the mortality ordering in an external ICU database. We additionally explored whether the association between early anemia and mortality was sensitive to phenotype specification.

## Methods

### Study design and data sources

We performed a retrospective cohort study using two de-identified, credentialed-access ICU databases: MIMIC-IV version 3.1, covering admissions during 2008-2022 [@johnson2023mimiciv; @johnson2024mimiciv31], and eICU-CRD version 2.0, covering 2014-2015 [@pollard2018eicu; @pollard2019eicu20]. Both resources are distributed through PhysioNet [@goldberger2000physionet]. MIMIC-IV was the derivation cohort, and eICU-CRD was used for an exploratory fixed-transport assessment. Database access was obtained after completion of Collaborative Institutional Training Initiative training and data-use requirements. Both source records describe de-identified resources with credentialed access and data-use requirements [@johnson2024mimiciv31; @pollard2019eicu20]. The final consent-waiver language remains to be confirmed against source database governance and local ethics requirements. Reporting was prepared against STROBE and RECORD guidance [@vonelm2007strobe; @benchimol2015record]; checklist mappings are provided separately.

### Cohort

Adults admitted to an ICU with NSAH were eligible if ICU length of stay was at least 24 h and no more than two of eight core physiological variables were missing. The analysis unit was one ICU stay per hospital admission; a patient could contribute more than one admission, and resampling was grouped by `subject_id`. MIMIC patients were identified using ICD-9 code 430 or ICD-10 I60.x codes. eICU patients were identified using ICD-9 code 430, admission diagnosis text containing subarachnoid hemorrhage, or diagnosis table entries consistent with NSAH. The cross-database NSAH identification algorithm was not formally validated against manual chart review. Patients with traumatic subarachnoid hemorrhage, multiple ICU stays during the index hospitalization, or red blood cell transfusion within 24 h meeting the study-specific operational exclusion (>=5 units) were excluded. This study-specific restriction was intended to limit distortion of baseline hemoglobin, hemodynamic, and coagulation signals; it was not treated as an externally validated massive-transfusion threshold.

### Variables and preprocessing

Eight routinely available variables were selected a priori to represent early neurological and systemic physiology: minimum GCS motor score, minimum mean arterial pressure, maximum shock index, minimum oxygen saturation, maximum creatinine, maximum international normalized ratio, minimum hemoglobin, and minimum platelet count. Variable selection was performed before outcome analyses and was based on clinical relevance and availability during early ICU care rather than associations with mortality. Measurements were summarized during the first 48 h after ICU admission to characterize early physiology, while recognizing that treatment-related changes could occur within this window. Values outside clinically plausible ranges were removed. Missing values were imputed with derivation-cohort medians. Creatinine and international normalized ratio were log1p transformed because their distributions were right skewed. All variables were standardized with derivation-cohort means and standard deviations.

### Phenotype derivation and transport assessment

Principal component analysis was used as a dimensionality-reduction step before clustering rather than as a clustering method itself. It reduced correlation and redundancy among physiological variables and generated orthogonal components representing major patterns of early neuro-systemic variation. K-means clustering was subsequently performed in this reduced feature space to identify groups with similar physiological profiles. Three principal components were retained and explained 56.41% of total variance. K-means clustering was performed in the three-component space using `random_state = 42` and `n_init = 100`. Candidate solutions ranging from K=2 to K=5 were evaluated using internal clustering indices, including silhouette coefficient, Calinski–Harabasz index, and Davies–Bouldin index, together with minimum cluster size, subject-grouped bootstrap stability, and clinical interpretability. Outcome variables were not considered during cluster number selection. The three-cluster solution was selected because it provided the best balance between statistical performance, stability, and clinical interpretability. After clustering, phenotype labels were assigned post hoc for presentation using a direction-weighted physiological severity score calculated from standardized cluster centers. Original physiological variables were then used to characterize and interpret the resulting phenotypes. Mortality was used neither for clustering nor for label ordering.

The exploratory eICU assessment used fixed transport. eICU data were imputed, transformed, and standardized with MIMIC parameters, projected with MIMIC principal component loadings, and assigned to the nearest MIMIC phenotype centroid. Because unsupervised clusters are data-dependent, the assessment focused on preservation of mortality and severity ordering rather than exact replication of patient-level cluster membership. Transported phenotypes were evaluated against mortality and eICU-provided severity variables that were not used for phenotype assignment. De novo eICU clustering was used only as a structural sensitivity analysis.

### Outcomes and statistical analysis

The primary outcome was in-hospital mortality. Secondary outcomes included ICU mortality and length of stay; early anemia, defined as a hemoglobin nadir <10 g/dL during 0-48 h, and red blood cell transfusion were examined as exploratory secondary variables. Continuous variables were summarized using appropriate measures of central tendency and dispersion, and categorical variables as frequencies and percentages. Because death or discharge could occur during the 0-48 h feature window, mortality analyses describe same-hospital associations rather than prognosis from a 48 h landmark. Multivariable logistic regression assessed the association between phenotype and hospital mortality. The primary model adjusted for age, sex, admission type, NSAH evidence level, aneurysm diagnosis, and early anemia. A process-of-care model also included nimodipine, vasopressors, mechanical ventilation, red blood cell transfusion, renal replacement therapy, EVD/ICP monitoring, and fluid balance. We interpreted process variables as exploratory severity and treatment-selection markers, not causal treatment effects. Because minimum hemoglobin was both a primary clustering input and the basis of the early-anemia definition, a post hoc exploratory sensitivity analysis re-derived phenotypes without hemoglobin and repeated the adjusted anemia-mortality model. Statistical tests were two-sided with p < 0.05 considered statistically significant. Other sensitivity analyses included complete-case, strict aneurysm, ICU stay >=48 h, 0-24 h window, INR-free, K=4, and 200 subject-grouped bootstrap analyses.

## Results

### Cohort and phenotype structure

The MIMIC derivation cohort included 1,186 ICU stays from 1,173 unique patients and demonstrated substantial heterogeneity in neurological severity and systemic physiology. Overall in-hospital mortality was 19.81%, early anemia occurred in 26.56%, and red blood cell transfusion within 48 h occurred in 2.02%. Missingness was low in the derivation cohort: maximum INR was missing in 5.48%, and all other core features were missing in <=0.08%.

The three retained principal components explained 56.41% of total variance. The K=3 solution identified three clinically interpretable phenotypes (Fig. 1; ESM Fig. 6). P1 included 694 stays (58.5%) and had mild neurological and systemic impairment. P2 included 384 stays (32.4%) and had severe neurological impairment with relatively preserved systemic physiology. P3 included 108 stays (9.1%) and combined severe neurological impairment with hypotension, elevated shock index, hypoxemia, renal dysfunction, coagulopathy, thrombocytopenia, and lower hemoglobin.

![Phenotype heatmap](figures/fig2_primary_log_pca_heatmap.png)
**Fig. 1.** Early physiological profiles of the three MIMIC-derived phenotypes. Values represent standardized cluster centers with raw medians and interquartile ranges.

### Outcomes and anemia

Mortality increased across phenotypes (Fig. 2). In-hospital mortality was 6.34% in P1, 32.55% in P2, and 61.11% in P3. ICU mortality followed the same order: 3.60%, 26.56%, and 50.93%, respectively.

![Outcome and anemia patterns](figures/fig3_outcomes_anemia.png)
**Fig. 2.** Outcome, anemia, and early red blood cell transfusion patterns in MIMIC-IV. Red blood cell transfusion is shown as a descriptive process variable and should not be interpreted as a treatment-effect estimate.

In the primary logistic model, P2 and P3 remained associated with in-hospital mortality after adjustment. Compared with P1, adjusted odds ratios were 7.59 (95% CI 5.07-11.36) for P2 and 21.21 (95% CI 12.08-37.26) for P3. Early anemia was more frequent in P2 and P3. In the model adjusted for the primary hemoglobin-containing phenotypes, the adjusted odds ratio for anemia was 0.99 (95% CI 0.68-1.44; p = 0.955). When phenotypes were re-derived without hemoglobin and the adjusted anemia-mortality model was repeated, the adjusted odds ratio was 1.54 (95% CI 1.06-2.22; p = 0.022), indicating sensitivity to phenotype specification. The process-of-care model attenuated phenotype associations but did not remove them. These process-adjusted estimates are exploratory because several variables occurred during the feature window.

### Exploratory external transport assessment

The eICU transport cohort included 843 patients. Fixed transport assigned 540 patients to P1, 221 to P2, and 82 to P3. Hospital mortality increased from 5.4% in P1 to 25.8% in P2 and 42.7% in P3. ICU mortality, early anemia, and red blood cell transfusion also increased across transported phenotypes.

Transported phenotype order aligned with eICU-provided severity variables that were not used for assignment. Median APACHE scores were 36, 57, and 79 across P1, P2, and P3, with Spearman rho 0.480. Acute Physiology Score and predicted hospital mortality showed similar ordering. These variables were not used for phenotype assignment.

Independent de novo K-means clustering in eICU recovered ordered mortality differences, but patient-level agreement with transported labels was negligible (adjusted Rand index 0.0005). This result supports transportability of the observed mortality ordering, not exact replication of cluster boundaries across databases.

### Robustness

Sensitivity analyses preserved the ordered mortality pattern. Subject-grouped, full-pipeline bootstrap stability was high, with mean adjusted Rand index 0.8554 across 200 resamples. Hemoglobin-free clustering also preserved phenotype-mortality separation, but the anemia-mortality estimate changed from 0.99 with the primary hemoglobin-containing phenotypes to 1.54 with hemoglobin-free phenotypes; the anemia result was therefore not robust to phenotype specification.

## Discussion

Eight routine ICU measurements separated stays into three early-course NSAH phenotypes, and fixed transport preserved the mortality ordering in an external multicenter database. P2 and P3 both had severe neurological impairment, whereas P3 also had widespread systemic abnormalities and substantially higher mortality.

Hunt-Hess, WFNS, and GCS emphasize neurological status [@hunt1968surgicalrisk; @teasdale1988wfns; @teasdale1974gcs], while APACHE and SOFA summarize general critical illness severity and organ dysfunction [@knaus1985apacheii; @vincent1996sofa]. The present phenotypes combine these neurological and systemic domains. They separated groups with different observed outcomes in this cohort, but their use for cohort enrichment or trial stratification requires prospective evaluation.

Early anemia was common in the high-risk phenotypes, but its adjusted association with mortality depended on phenotype specification. Adjustment for the primary phenotypes, which were constructed partly from minimum hemoglobin, yielded an adjusted odds ratio of 0.99 (95% CI 0.68-1.44). Because the same-window hemoglobin measurement informed both phenotype assignment and anemia status, this estimate may be affected by overadjustment. After phenotypes were re-derived without hemoglobin, early anemia was associated with mortality (adjusted odds ratio 1.54, 95% CI 1.06-2.22). These results do not establish whether anemia is solely a marker of broader physiological derangement or provides independent prognostic information, and neither model supports a causal interpretation. In the SAHARA trial, a liberal transfusion strategy did not significantly reduce unfavorable neurological outcome at 12 months compared with a restrictive strategy [@english2025sahara]. Our study does not estimate transfusion effects and should not guide transfusion thresholds. That question requires a causal analysis with an explicit treatment estimand or a randomized trial.

The mortality and severity ordering persisted after fixed transport to eICU, but de novo eICU clustering did not reproduce the transported labels at the patient level. Differences in measurement, missingness, or documentation could explain this discordance, although we did not test those mechanisms. The fixed assignment rule warrants prospective evaluation; these data do not show replication of cluster structure or superiority over de novo clustering.

The analysis used eight routinely available variables, documented preprocessing steps, fixed transport to eICU, and multiple sensitivity analyses. Restricting phenotype derivation to these measurements kept the resulting patterns clinically interpretable.

This study has limitations. Residual confounding and misclassification remain possible in both retrospective databases, and the NSAH identification algorithm was not validated against manual chart review. The analysis lacked detailed neuroimaging and neurosurgical variables, including Fisher grade, hemorrhage volume, aneurysm location, hydrocephalus, and procedure timing. The 0-48 h window may contain measurements altered by treatment, gives shorter stays less measurement opportunity, and can overlap with the mortality outcome; the reported associations are therefore not 48 h landmark predictions. The use of minimum hemoglobin in both primary phenotype derivation and anemia definition created potential overadjustment in the primary anemia model; the hemoglobin-free sensitivity analysis reduced this coupling but did not eliminate residual confounding. Thirteen admission rows came from patients represented more than once, and resampling was therefore grouped by `subject_id`. The post-entry exclusion of patients receiving at least 5 red-cell units within 24 h may also introduce selection bias. INR was frequently missing in eICU, although the INR-free sensitivity analysis retained the mortality ordering. MIMIC-IV is a US single-center resource, and eICU is a US multicenter resource [@johnson2023mimiciv; @pollard2018eicu]. Prospective validation is needed in contemporary cohorts from other health systems.

## Conclusion

Eight routine physiological variables measured during the first 48 h of ICU admission defined three early-course NSAH phenotypes with ordered same-hospital mortality. Fixed MIMIC-derived assignment preserved this ordering in eICU and aligned with eICU-provided severity variables that were not used for assignment, but de novo clustering did not reproduce the same cluster boundaries. The adjusted anemia-mortality association was sensitive to whether hemoglobin was included in phenotype derivation. These descriptive findings require prospective, time-anchored validation and do not establish bedside predictive utility or treatment effects.

## Declarations

**Funding:** To be completed by authors before submission.

**Conflicts of interest:** To be completed by authors before submission.

**Ethics approval:** MIMIC-IV and eICU-CRD are de-identified, credentialed-access research databases [@johnson2024mimiciv31; @pollard2019eicu20]. Database access was obtained after required training and data-use agreements. Local ethics documentation should be completed according to the submitting institution and target journal requirements.

**Consent to participate:** To be confirmed against source database governance and local ethics requirements before submission.

**Data availability:** MIMIC-IV and eICU-CRD are available through PhysioNet to credentialed users who complete required training and data-use agreements [@johnson2024mimiciv31; @pollard2019eicu20]. Derived aggregate outputs are included in the manuscript and Electronic Supplementary Material.

**Code availability:** Analysis code and reproducible preprocessing parameters should be provided in a public repository or submitted as supplementary material before journal submission.

**Author contributions:** To be completed by authors before submission.

**Use of AI-assisted tools:** Gemini was used during initial manuscript drafting, and Codex was used for editorial revision, citation checking, and formatting review. The authors must verify and take responsibility for all scientific content, analyses, interpretation, and final wording before submission.

**Reporting guideline:** Completed STROBE and RECORD checklist mappings [@vonelm2007strobe; @benchimol2015record] will be submitted as Electronic Supplementary Material.

## Electronic supplementary material

The Electronic Supplementary Material is prepared as `electronic_supplementary_material.md` and includes the cohort algorithm, ICD/code-list, variable mapping, missingness audit, extended baseline/phenotype/regression/eICU/sensitivity tables, the time-to-event analysis boundary, supplementary figures, BigQuery provenance, and reproducibility parameters. STROBE and RECORD mappings are prepared separately as `strobe_checklist.md` and `record_checklist.md`.
