# Deviation Log

The protocol and SAP were reconstructed after outcome access. These entries record differences between the implemented exploratory analysis and the preferred frozen design.

| ID | Deviation | Impact | Current handling | Required closure |
| :--- | :--- | :--- | :--- | :--- |
| DEV-001 | Protocol/SAP were not frozen before analysis and outcome access | Confirmatory interpretation is not supported | Manuscript labels the work retrospective/exploratory | Authors approve retrospective status and freeze a versioned deviation record |
| DEV-002 | The 0-48 h feature window may overlap in-hospital death | Not a 48 h landmark prognostic design | Manuscript uses descriptive same-hospital association wording | Authors accept this target or authorize a landmark rerun |
| DEV-003 | Bootstrap and cross-validation are row-based rather than grouped by `subject_id` | Dependence may overstate stability/performance | Prediction results removed; bootstrap limitation disclosed | Count repeated subjects and rerun retained resampling if necessary |
| DEV-004 | Preprocessing/PCA are not fully refit within every bootstrap iteration | Stability may be optimistic | Disclosed in review artifacts | Authorized rerun of the full pipeline within grouped resamples |
| DEV-005 | Patients receiving at least 5 RBC units in 24 h are excluded after cohort entry | Potential treatment/severity selection bias | Threshold described as study-specific; limitation disclosed | Include-all sensitivity analysis or author-approved post hoc rationale |
| DEV-006 | NSAH ICD/text identification lacks manual-chart validation | Possible cohort misclassification | Explicitly disclosed in Methods, Discussion, and RECORD checklist | Add external validation evidence or conduct validation if feasible |
| DEV-007 | Prediction model used globally imputed data and ungrouped cross-validation | Leakage and dependence risk | Prediction result and figure removed from submission package | Retain as excluded exploratory artifact or rebuild in a separate prediction protocol |
