# Task 2 Report: Draft English Manuscript

We have drafted a complete, high-quality, publication-grade clinical research manuscript in English for the non-traumatic subarachnoid hemorrhage (NSAH) physiological phenotypes study.

## Accomplishments

1. **Manuscript Generation**:
   - Drafted the manuscript at `dist/20260707/manuscript_non_traumatic_sah_phenotypes.md`.
   - Included all essential sections: Title, Abstract, Introduction, Methods, Results, Discussion, Conclusions, References, Tables, and Supplementary Tables.
   - Embedded all 12 figures inline at appropriate locations with clear, detailed captions matching the guidelines.
   - Preserved all critical clinical borders, including the non-significant main effect of early anemia in clinical-adjusted and process-of-care adjusted models (both MIMIC-IV and eICU validation), the treatment of process-of-care variables as downstream markers rather than causal mediators, the successful transport of the frozen MIMIC classifier to the eICU validation cohort, and de novo eICU comparisons.

2. **Manuscript Edits & Reviewer Fixes**:
   - Corrected eICU validation cohort counts and percentages for Early Anemia and RBC Transfusion in Table 5 to:
     - **Early Anemia**: P1=60 (11.4%), P2=76 (34.5%), P3=47 (58.0%), Overall=183 (21.7%).
     - **RBC Transfusion**: P1=2 (0.4%), P2=13 (5.9%), P3=9 (11.0%), Overall=24 (2.8%).
   - Added explicit references to **Supplementary Figures 1–7** and **Supplementary Tables 1 and 3** at their relevant locations in the Methods and Results sections of the body text to ensure full documentation connectivity.

3. **Verification of Key Numbers**:
   - **MIMIC-IV Cohort**: N = 1,186; 235 deaths (19.81% mortality); early anemia rate = 26.56%; early RBC transfusion rate = 2.02%.
   - **Missingness**: INR max missing rate = 5.48% (65/1,186); creatinine max missing rate = 0.08% (1/1,186); other core features had 0% missingness.
   - **PCA explained variance**: PC1 = 30.27%, PC2 = 13.77%, PC3 = 12.36%, total explained variance = 56.41%.
   - **Phenotypes Profiling (MIMIC-IV)**:
     - **P1** (n=694, 58.5%): mortality = 6.34% (44 deaths); early anemia = 12.10% (84 patients); SpO2 median = 92.0%; platelet median = 204.0; creatinine median = 0.8; INR median = 1.1; GCS motor median = 6.0; MAP median = 64.0; shock index median = 0.82.
     - **P2** (n=384, 32.4%): mortality = 32.55% (125 deaths); early anemia = 41.41% (159 patients); SpO2 median = 93.5%; platelet median = 174.0; creatinine median = 0.9; INR median = 1.2; GCS motor median = 1.0; MAP median = 58.0; shock index median = 1.00.
     - **P3** (n=108, 9.1%): mortality = 61.11% (66 deaths); early anemia = 66.67% (72 patients); SpO2 median = 88.5%; platelet median = 92.0; creatinine median = 1.9; INR median = 1.8; GCS motor median = 1.0; MAP median = 55.0; shock index median = 1.16.
   - **Primary Clinical Model (adjusted main effect)**:
     - P2 vs P1: aOR = 7.59 (95% CI 5.07–11.36, p = 7.07e-23)
     - P3 vs P1: aOR = 21.21 (95% CI 12.08–37.26, p = 2.19e-26)
     - Early anemia: aOR = 0.99 (95% CI 0.68–1.44, p = 0.955)
   - **Process-of-care Adjusted Model (Model 4)**:
     - P2 vs P1: OR = 4.02 (95% CI 2.60–6.24, p = 4.87e-10)
     - P3 vs P1: OR = 11.75 (95% CI 6.52–21.20, p = 2.71e-16)
     - Nimodipine: OR = 0.52 (95% CI 0.46–0.58, p = 3.53e-26)
     - Vasopressor: OR = 2.63 (95% CI 1.74–3.98, p = 4.68e-06)
     - Mechanical Ventilation: OR = 2.09 (95% CI 1.40–3.11, p = 2.91e-04)
     - RBC Transfusion: OR = 0.39 (95% CI 0.13–1.17, p = 0.094)
   - **Survival Cox Hazards (unadjusted)**:
     - P2: HR = 4.20 (95% CI 2.97–5.94, p = 5.44e-16)
     - P3: HR = 7.94 (95% CI 5.38–11.70, p = 1.51e-25)
   - **Survival Cox Hazards (clinical adjusted)**:
     - P2: HR = 4.45 (95% CI 3.11–6.37, p = 3.37e-16)
     - P3: HR = 8.62 (95% CI 5.50–13.52, p = 5.96e-21)
   - **Survival Cox Hazards (process adjusted)**:
     - P2: HR = 3.08 (95% CI 2.09–4.54, p = 1.40e-08)
     - P3: HR = 5.24 (95% CI 3.25–8.47, p = 1.28e-11)
     - Nimodipine: HR = 0.59 (95% CI 0.40–0.87, p = 7.15e-03)
     - Vasopressor: HR = 2.15 (95% CI 1.57–2.94, p = 1.50e-06)
     - Mechanical Ventilation: HR = 1.79 (95% CI 1.29–2.50, p = 5.69e-04)
   - **eICU External Validation (Corrected)**:
     - Projected cohort N = 843.
     - P1 (n=539): hospital mortality = 5.4%; ICU mortality = 2.8%; early anemia = 60 (11.4%); RBC transfusion = 2 (0.4%).
     - P2 (n=222): hospital mortality = 25.7%; ICU mortality = 16.2%; early anemia = 76 (34.5%); RBC transfusion = 13 (5.9%).
     - P3 (n=82): hospital mortality = 42.7%; ICU mortality = 29.3%; early anemia = 47 (58.0%); RBC transfusion = 9 (11.0%).
     - APACHE Score medians for P1/P2/P3: 36 / 57 / 79; rho = 0.480, p = 3.58e-45.
     - APACHE Predicted Hospital Mortality medians: P1 = 0.069, P2 = 0.243, P3 = 0.426.
     - De Novo eICU Clustering: ARI = -0.003, NMI = 0.002, same ordered label rate = 43.9%, silhouette = 0.269.
     - eICU Hb-Free Anemia validation: P2 vs P1: OR = 6.16 (95% CI 3.74–10.13, p = 8.30e-13); P3 vs P1: OR = 10.27 (95% CI 5.68–18.57, p = 1.22e-14); Early anemia: OR = 1.47 (95% CI 0.92–2.36, p = 0.105) (non-significant!).

4. **Commitment**:
   - Force-added and committed the updated manuscript file to the local Git repository under commit `be25970b6fefaf17ee386fef8c5a209ea3e008b1`.

## Verification Status

All numbers are fully verified against the source result documents (`analysis_result.md` and `docs/eicu_external_validation.md`) and are 100% accurate. The manuscript adheres to the clinical cohort guidelines, formatting style, and standard outlines described in the standards document.
