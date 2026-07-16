# Random Seed Registry

| Stage | Location | Seed policy | Status |
| :--- | :--- | :--- | :--- |
| MIMIC PCA/K-means | `11_bigquery_notebook_non_traumatic_sah_analysis.py` | Base `RANDOM_SEED = 42`; K-means uses fixed seed and explicit `n_init` | Recorded |
| MIMIC bootstrap | Same analysis script | NumPy generator seeded with 42; iteration K-means uses `42 + iteration` | Recorded; patient-grouped/full-pipeline resampling remains unresolved |
| Prediction cross-validation | Same analysis script | Stratified K-fold seed 42 | Analysis removed from submission manuscript; grouping/leakage unresolved |
| eICU transport/sensitivity | `scripts/15_run_eicu_external_validation.py` | `RANDOM_SEED = 42` | Recorded |
| Figure illustration | `scripts/generate_manuscript_figures.py` | Seed 42 for the displayed bootstrap-distribution illustration | Recorded |

No claim of bitwise reproducibility is made. Library, BLAS, CPU, and BigQuery execution differences may affect floating-point results or row ordering unless explicitly controlled.
