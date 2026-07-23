---
bibliography: references.bib
csl: journal.csl
link-citations: true
reference-section-title: References
---

# Early physiological phenotypes and outcomes in critically ill adults with non-traumatic subarachnoid hemorrhage

## Take-home message

Among eligible ICU stays for adults with non-traumatic subarachnoid hemorrhage, a three-cluster solution based on eight routine physiological measures separated early clinical courses with graded observed mortality. Applying the fixed MIMIC assignment rule to eICU produced the same crude mortality order, although de novo clusters did not agree. The anemia estimate changed when hemoglobin was removed from phenotype derivation.

## Structured abstract

### Purpose

To derive 0-48 h physiological phenotypes in critically ill adults with non-traumatic subarachnoid hemorrhage (NSAH), describe observed in-hospital mortality, assess whether anemia estimates depend on phenotype specification, and examine fixed eICU assignment.

### Methods

This post-outcome exploratory analysis included 1,186 ICU stays from 1,173 MIMIC-IV 3.1 patients and 843 eICU-CRD 2.0 patients. Eight 0-48 h variables underwent PCA and K-means clustering after preprocessing. K=3 was frozen after outcome access and compared with K=2-5 internal metrics; mortality was not used for clustering or label ordering. Stay-level logistic regression estimated mortality associations; P values were unadjusted for multiplicity. This was not landmark prediction because deaths could occur during ascertainment. A post hoc hemoglobin-free analysis examined anemia. Fixed MIMIC parameters and centroids assigned eICU patients.

### Results

P1 (n=694) had relatively preserved physiology, P2 (n=384) had severe neurological impairment, and P3 (n=108) had neurological and multisystem dysfunction. In-hospital mortality was 6.34%, 32.55%, and 61.11%, respectively. Adjusted odds ratios versus P1 were 7.59 (95% CI 5.07-11.36) and 21.21 (12.08-37.26). Mean subject-grouped bootstrap adjusted Rand index was 0.8554. Anemia odds ratios were 0.99 (0.68-1.44) with hemoglobin-containing phenotypes and 1.54 (1.06-2.22) with hemoglobin-free phenotypes. Fixed eICU transport assigned 540, 221, and 82 patients to P1, P2, and P3; mortality was 5.4%, 25.8%, and 42.7%.

### Conclusion

Eligible ICU stays formed three groups with graded in-hospital mortality. Fixed eICU assignment yielded the same crude mortality order but not the cluster boundaries. The anemia estimate depended on phenotype specification. Prospective, time-anchored studies are needed before clinical use; these data do not estimate treatment effects.

**Keywords:** subarachnoid hemorrhage; critical care; phenotyping; unsupervised learning; transportability.

## Introduction

Non-traumatic subarachnoid hemorrhage (NSAH) is a high-acuity neurological emergency with substantial mortality and long-term disability [@macdonald2017sah]. Clinical grading includes Hunt-Hess, WFNS, and the Glasgow Coma Scale (GCS) [@hunt1968surgicalrisk; @teasdale1988wfns; @teasdale1974gcs]. These scales capture neurological severity but do not incorporate the range of systemic measurements routinely collected in the ICU.

Studies of aneurysmal SAH describe systemic inflammation that may contribute to intracranial and extracranial injury [@chai2023inflammation] and frequent anemia during acute care [@rosenberg2013anemia]. We therefore examined neurological measurements together with renal, hematologic, circulatory, respiratory, and coagulation variables in NSAH. APACHE and SOFA summarize general illness severity and organ dysfunction, respectively, but were not developed to identify NSAH-specific physiological patterns [@knaus1985apacheii; @vincent1996sofa].

Unsupervised analyses have identified clinically distinct subgroups in sepsis and acute respiratory distress syndrome [@seymour2019sepsisphenotypes; @calfee2014ardssubphenotypes]. We applied this approach to early multimodal physiology in neurocritical care. We examined whether the resulting NSAH groups differed in observed mortality and whether a fixed MIMIC-IV assignment rule produced the same mortality order in another ICU database. We also examined whether the anemia estimate changed with phenotype specification.

## Methods

### Study design and data sources

We performed a retrospective cohort study using two de-identified, credentialed-access ICU databases: MIMIC-IV version 3.1, covering admissions during 2008-2022 [@johnson2023mimiciv; @johnson2024mimiciv31], and eICU-CRD version 2.0, covering 2014-2015 [@pollard2018eicu; @pollard2019eicu20]. Both resources are distributed through PhysioNet [@goldberger2000physionet]. MIMIC-IV was the derivation cohort; eICU-CRD was used for exploratory fixed assignment. Database access followed the required training and data-use agreements. The protocol and statistical analysis plan were reconstructed after outcome access, so all analyses are exploratory. The final consent-waiver language remains subject to source-database governance and local ethics review. Reporting follows STROBE and RECORD guidance [@vonelm2007strobe; @benchimol2015record], with separate checklist mappings.

### Cohort

Adults admitted to an ICU with NSAH were eligible if ICU length of stay was at least 24 h and no more than two of eight core physiological variables were missing. In MIMIC, the analysis unit was one ICU stay per hospital admission; a patient could contribute more than one admission, and resampling was grouped by `subject_id`. MIMIC patients were identified using ICD-9 code 430 or ICD-10 I60.x codes. Admissions with traumatic subarachnoid hemorrhage evidence, multiple ICU stays, or at least 5 units of red blood cells recorded within 24 h of ICU admission were excluded. The transfusion threshold was study specific rather than a validated definition; an include-all MIMIC sensitivity analysis added no otherwise eligible cases. In eICU, ICD-9 code 430, admission diagnosis text, or diagnosis table entries identified candidate NSAH, and only the first ICU stay per unique patient was retained. Traumatic cases were excluded, but no red-cell threshold was applied because eICU transfusion units were heterogeneous. Neither database-specific identification algorithm was formally validated against manual chart review.

### Variables and preprocessing

The final feature set comprised minimum GCS motor score, minimum mean arterial pressure, maximum shock index, minimum oxygen saturation, maximum creatinine, maximum international normalized ratio, minimum hemoglobin, and minimum platelet count. These variables were chosen for clinical relevance and routine availability, then frozen after outcome access. Mortality was not a clustering input or used to order phenotype labels. Measurements were summarized over the first 48 h after ICU admission; treatment during this period could alter them. Values outside study-defined clinical ranges were removed. Missing values were imputed with derivation-cohort medians, creatinine and international normalized ratio were log1p transformed, and all variables were standardized with derivation-cohort means and standard deviations.

### Phenotype derivation and transport assessment

Principal component analysis reduced the standardized feature space before K-means clustering. Three retained components explained 56.41% of total variance. K-means used `random_state = 42` and `n_init = 100` in this three-component space. The frozen rerun compared K=2 to K=5 using silhouette, Calinski-Harabasz, and Davies-Bouldin indices, minimum cluster size, subject-grouped bootstrap stability, and clinical interpretation. K=3 was retained as the exploratory main specification, not as a prespecified choice. After clustering, a direction-weighted physiological severity score calculated from standardized cluster centers ordered the labels P1 to P3. Mortality was not used to fit the clusters or order the labels. Original variables were used to describe the groups.

The exploratory eICU assessment used fixed transport. eICU data were imputed, transformed, and standardized with MIMIC parameters, projected with MIMIC principal component loadings, and assigned to the nearest MIMIC phenotype centroid. Because unsupervised clusters are data-dependent, the assessment focused on preservation of mortality and severity ordering rather than exact replication of patient-level cluster membership. Transported phenotypes were evaluated against mortality and eICU-provided severity variables that were not used for phenotype assignment. De novo eICU clustering was used only as a structural sensitivity analysis.

### Outcomes and statistical analysis

The primary outcome was in-hospital mortality. Secondary outcomes included ICU mortality and length of stay. Early anemia, defined as a hemoglobin nadir <10 g/dL during 0-48 h, and red blood cell transfusion were exploratory variables. Because death or discharge could occur during the feature window, mortality analyses are descriptive associations rather than prognosis from a 48 h landmark.

The implemented exploratory logistic model included phenotype, age, sex, admission type, NSAH evidence level, aneurysm diagnosis, and early anemia. This formula was frozen after outcome access. A separate process-of-care model added same-window treatment variables and two etiology indicators that encoded the same information; it was retained for audit and not interpreted. Because minimum hemoglobin informed both phenotype assignment and anemia status, a post hoc exploratory sensitivity analysis re-derived phenotypes without hemoglobin and repeated the anemia model. Tests were two-sided and P values were unadjusted for multiplicity; interpretation emphasized estimates and confidence intervals. Regression confidence intervals used stay-level model covariance and were not clustered by `subject_id`. Other sensitivity analyses included complete-case, strict aneurysm, ICU stay >=48 h, 0-24 h, INR-free, K=4, and 200 subject-grouped bootstrap analyses.

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

In the implemented exploratory logistic model, the adjusted odds ratios versus P1 were 7.59 (95% CI 5.07-11.36) for P2 and 21.21 (95% CI 12.08-37.26) for P3. Early anemia was more frequent in P2 and P3. The anemia odds ratio was 0.99 (95% CI 0.68-1.44; unadjusted P = 0.955) when the model included the hemoglobin-containing phenotypes. After phenotypes were re-derived without hemoglobin, the anemia odds ratio was 1.54 (95% CI 1.06-2.22; unadjusted P = 0.022). The process-of-care model was rank deficient and was not interpreted.

### Exploratory external transport assessment

The eICU transport cohort included 843 patients. Fixed assignment placed 540 patients in P1, 221 in P2, and 82 in P3. Observed hospital mortality was 5.4%, 25.8%, and 42.7%, respectively. Before feature-completeness eligibility, INR was missing in 446 of 903 patients (49.4%); 390 of 843 transported patients (46.3%) required frozen MIMIC median imputation. ICU mortality, early anemia, and red blood cell transfusion followed the same crude order.

The assigned groups also had ordered eICU severity measures that were not used for assignment. Median APACHE scores were 36, 57.5, and 79 across P1, P2, and P3; Spearman rho was 0.480. Acute Physiology Score and predicted hospital mortality showed the same direction.

Independent de novo K-means clustering in eICU recovered ordered mortality differences, but patient-level agreement with transported labels was negligible (adjusted Rand index 0.0005). The external results show a crude mortality ordering under fixed assignment, not replication of cluster boundaries across databases.

### Robustness

Sensitivity analyses retained the crude mortality order. The mean adjusted Rand index from 200 subject-grouped, full-pipeline bootstrap resamples was 0.8554. INR-free eICU assignment yielded mortality of 4.6%, 24.4%, and 38.7% across P1 to P3. Hemoglobin-free clustering retained phenotype-mortality separation, but the anemia estimate changed from 0.99 to 1.54; the anemia result was not robust to phenotype specification.

## Discussion

Eight routine ICU measurements separated eligible stays into three early-course NSAH groups. Observed mortality increased from P1 to P3 in MIMIC, and the fixed assignment rule produced the same crude order in eICU. P2 and P3 both had severe neurological impairment, while P3 also had systemic abnormalities.

Hunt-Hess, WFNS, and GCS emphasize neurological status [@hunt1968surgicalrisk; @teasdale1988wfns; @teasdale1974gcs], whereas APACHE and SOFA summarize general illness severity and organ dysfunction [@knaus1985apacheii; @vincent1996sofa]. The present groups combine neurological and systemic measurements. Whether they are useful for cohort enrichment or trial stratification remains unknown.

Early anemia was common in P2 and P3, but its adjusted estimate depended on phenotype specification. The odds ratio was 0.99 when the model included phenotypes constructed partly from minimum hemoglobin and 1.54 after hemoglobin was removed from phenotype derivation. The first estimate may be overadjusted because the same-window hemoglobin value informed both variables. The second was post hoc and does not remove residual confounding. Neither model establishes independent prognostic information or a causal effect. In the SAHARA trial, a liberal transfusion strategy did not significantly reduce unfavorable neurological outcome at 12 months compared with a restrictive strategy [@english2025sahara]. Our study does not estimate transfusion effects and should not guide transfusion thresholds.

The fixed eICU assignment produced ordered mortality and severity measures, but de novo eICU clusters showed negligible patient-level agreement with the assigned labels. Differences in measurement, missingness, and documentation are possible explanations, but we did not test them. This is an exploratory transport check, not evidence that the cluster structure replicated.

The assignment rule uses eight routinely recorded variables and fixed preprocessing parameters. This makes the rule reproducible, but the small feature set omits imaging and several neurosurgical factors that may define clinically important SAH subgroups.

This study has limitations. The protocol and SAP were reconstructed after outcome access, so the feature set, K=3 choice, and regression models are exploratory rather than prespecified. Residual confounding and cohort misclassification remain possible, and the NSAH identification algorithm was not validated against manual chart review. The analysis lacked Fisher grade, hemorrhage volume, aneurysm location, hydrocephalus, and procedure timing. The 0-48 h window may include measurements altered by treatment, gives shorter stays less measurement opportunity, and overlaps some deaths; these are not 48 h landmark predictions. The anemia analysis couples the same-window hemoglobin measure to phenotype assignment, and the hemoglobin-free analysis was post hoc. P values were not adjusted for multiplicity. Thirteen rows came from patients represented more than once; resampling was grouped by `subject_id`, but regression confidence intervals used stay-level covariance. The post-entry transfusion exclusion did not remove any otherwise eligible case in the include-all sensitivity analysis. Before feature-completeness eligibility, INR was missing in 49.4% of eICU patients; external analyses also did not account for hospital-level clustering. MIMIC-IV is a US single-center resource and eICU is a US multicenter resource [@johnson2023mimiciv; @pollard2018eicu]. Other health systems may yield different assignments and outcome patterns.

## Conclusion

Among ICU stays lasting at least 24 h with adequate feature availability, the three-cluster solution separated early NSAH courses with graded observed in-hospital mortality. Fixed eICU assignment produced the same crude mortality order, but de novo clusters did not reproduce the boundaries. The anemia estimate changed when hemoglobin was removed from phenotype derivation. Prospective, time-anchored studies are needed before clinical use; these data do not estimate treatment effects.

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
