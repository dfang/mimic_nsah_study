# Deviation Log

The protocol and SAP were reconstructed after outcome access. These entries record differences between the implemented exploratory analysis and the preferred frozen design.

| ID | Deviation | Impact | Current handling | Required closure |
| :--- | :--- | :--- | :--- | :--- |
| DEV-001 | Protocol/SAP were not frozen before analysis and outcome access | Confirmatory interpretation is not supported | Protocol/SAP v1.0.0 and manuscript label the work retrospective/exploratory | Closed for exploratory freeze; cannot be removed retrospectively |
| DEV-002 | The 0-48 h feature window may overlap in-hospital death | Not a 48 h landmark prognostic design | Descriptive same-hospital association retained; LOS ≥48 h sensitivity completed | Closed with permanent non-predictive interpretation boundary |
| DEV-003 | Original bootstrap and cross-validation were row-based rather than grouped by `subject_id` | Dependence may have overstated stability/performance | Superseded by subject-grouped rerun; 13 repeat-admission rows in primary cohort | Closed; only regenerated grouped results are frozen |
| DEV-004 | Original preprocessing/PCA were not fully refit within every bootstrap iteration | Original stability may have been optimistic | Superseded by 200-iteration full-pipeline grouped bootstrap | Closed; mean ARI 0.8554 and mean OOB ARI 0.8578 |
| DEV-005 | Patients receiving at least 5 RBC units in 24 h are excluded after cohort entry | Potential treatment/severity selection bias | Include-all sensitivity completed; no additional eligible cases, ARI 1.0000 | Closed for this release; retain design limitation |
| DEV-006 | NSAH ICD/text identification lacks manual-chart validation | Possible cohort misclassification | Explicitly disclosed in Methods, Discussion, and RECORD checklist | Add external validation evidence or conduct validation if feasible |
| DEV-007 | Original prediction model used globally imputed data and ungrouped cross-validation | Leakage and dependence risk | Superseded exploratory output uses fold-local preprocessing and grouped CV; not a validated prediction model | Closed for exploratory freeze; keep excluded from primary claims |
| DEV-008 | Sensitivity cohort clustering initially used a preprocessing space inconsistent with the primary log-PCA model | Sensitivity ARIs and sizes were not comparable to the primary pipeline | LOS, no-RBC and include-massive cohorts were refit with the primary log1p + PCA + K-means method | Closed by authorized rerun and manuscript/ESM reconciliation |
