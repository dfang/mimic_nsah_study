# Random Seed Registry

| Stage | Location | Seed policy | Status |
| :--- | :--- | :--- | :--- |
| MIMIC PCA/K-means | `11_bigquery_notebook_non_traumatic_sah_analysis.py` | Base `RANDOM_SEED = 42`; K-means uses fixed seed and explicit `n_init` | Recorded |
| MIMIC bootstrap | `scripts/phenotype_stability.py` called by the analysis script | Subject-grouped NumPy sampling seeded with 42; each iteration refits imputer/scaler/PCA/K-means and uses `42 + iteration` for model randomness | Executed for frozen release; 200 iterations |
| Prediction cross-validation | `scripts/phenotype_stability.py` called by the analysis script | `StratifiedGroupKFold` seed 42; preprocessing is fitted inside each fold | Executed as exploratory output; not a validated prediction claim |
| eICU transport/sensitivity | `scripts/15_run_eicu_external_validation.py` | `RANDOM_SEED = 42` | Recorded |
| Figure illustration | `scripts/generate_manuscript_figures.py` | Seed 42 for the displayed bootstrap-distribution illustration | Recorded |

No claim of bitwise reproducibility is made. Library, BLAS, CPU, and BigQuery execution differences may affect floating-point results or row ordering unless explicitly controlled.
