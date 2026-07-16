from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def test_terminal_analysis_entrypoint_can_import_repository_helpers(tmp_path: Path) -> None:
    analysis = tmp_path / "synthetic_analysis.py"
    analysis.write_text(
        "from scripts.phenotype_stability import grouped_bootstrap_indices\n"
        "print(grouped_bootstrap_indices.__name__)\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/13_run_non_traumatic_sah_analysis.py"),
            "--analysis-file",
            str(analysis),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "grouped_bootstrap_indices" in completed.stdout


def test_group_bootstrap_keeps_all_rows_from_each_sampled_subject_together() -> None:
    from scripts.phenotype_stability import grouped_bootstrap_indices

    subjects = pd.Series([10, 10, 20, 30, 30, 30])
    sample = grouped_bootstrap_indices(subjects, np.random.default_rng(7))

    source_counts = subjects.value_counts().to_dict()
    sampled_counts = subjects.iloc[sample].value_counts().to_dict()
    for subject_id, count in sampled_counts.items():
        assert count % source_counts[subject_id] == 0


def test_grouped_pipeline_bootstrap_refits_and_reports_subject_level_evaluation() -> None:
    from scripts.phenotype_stability import run_grouped_pipeline_bootstrap

    frame = pd.DataFrame(
        {
            "subject_id": np.repeat(np.arange(12), 2),
            "f1": np.tile([1.0, 1.1, 5.0, 5.1, 9.0, 9.1], 4),
            "f2": np.tile([9.0, 8.9, 5.0, 4.9, 1.0, 0.9], 4),
        }
    )
    reference = pd.Series(np.tile([1, 1, 2, 2, 3, 3], 4))

    result = run_grouped_pipeline_bootstrap(
        frame,
        features=["f1", "f2"],
        reference_phenotype=reference,
        subject_column="subject_id",
        k=3,
        random_seed=42,
        n_bootstrap=3,
        severity_directions={"f1": 1, "f2": -1},
        pca_components=2,
    )

    assert len(result) == 3
    assert set(
        [
            "sampled_subjects_n",
            "unique_sampled_subjects_n",
            "oob_subjects_n",
            "adjusted_rand_index_vs_primary",
            "oob_adjusted_rand_index_vs_primary",
            "cluster_jaccard_p1",
            "cluster_jaccard_p2",
            "cluster_jaccard_p3",
        ]
    ).issubset(result.columns)
    assert (result["sampled_subjects_n"] == frame["subject_id"].nunique()).all()


def test_sql_and_analysis_define_include_all_transfusion_sensitivity() -> None:
    sql = (ROOT / "10_create_non_traumatic_sah_cohort.sql").read_text()
    analysis = (ROOT / "11_bigquery_notebook_non_traumatic_sah_analysis.py").read_text()

    flag = "eligible_include_massive_transfusion_sensitivity"
    assert flag in sql
    assert flag in analysis


def test_primary_analysis_uses_grouped_full_pipeline_bootstrap() -> None:
    analysis = (ROOT / "11_bigquery_notebook_non_traumatic_sah_analysis.py").read_text()

    assert "from scripts.phenotype_stability import" in analysis
    assert "run_grouped_pipeline_bootstrap(" in analysis


def test_cohort_sensitivities_refit_the_primary_log_pca_pipeline() -> None:
    analysis = (ROOT / "11_bigquery_notebook_non_traumatic_sah_analysis.py").read_text()
    start = analysis.index("def run_sensitivity_cohort_summaries")
    end = analysis.index("\ndef run_epvs_sensitivity", start)
    function_source = analysis[start:end]

    assert "preprocess_log_pca_feature_matrix(sub_df)" in function_source
    assert "silhouette_score(pc_scores_sens" in function_source
    assert "preprocess_feature_matrix(sub_df, FEATURES)" not in function_source


def test_grouped_prediction_keeps_subjects_in_one_fold() -> None:
    from scripts.phenotype_stability import grouped_logistic_predictions

    frame = pd.DataFrame(
        {
            "subject_id": np.repeat(np.arange(20), 2),
            "outcome": np.repeat(np.arange(20) % 2, 2),
            "age": np.linspace(40, 80, 40),
            "sex": np.tile(["F", "M"], 20),
        }
    )
    probabilities, fold_ids = grouped_logistic_predictions(
        frame,
        predictors=["age", "sex"],
        outcome="outcome",
        subject_column="subject_id",
        n_splits=5,
        random_seed=42,
    )

    assert len(probabilities) == len(frame)
    assert np.isfinite(probabilities).all()
    assert ((probabilities > 0) & (probabilities < 1)).all()
    assert frame.assign(fold=fold_ids).groupby("subject_id")["fold"].nunique().max() == 1


def test_prediction_increment_uses_subject_grouped_cross_validation() -> None:
    analysis = (ROOT / "11_bigquery_notebook_non_traumatic_sah_analysis.py").read_text()

    assert "grouped_logistic_predictions" in analysis
    assert "StratifiedKFold" not in analysis


def test_cohort_sql_does_not_emit_patient_level_preview_rows() -> None:
    sql = (ROOT / "10_create_non_traumatic_sah_cohort.sql").read_text()

    assert "SELECT *\nFROM `mimic-study-498508.non_traumatic_sah_study.aneurysm_procedure_flags`" not in sql


def test_analysis_logs_bigquery_job_provenance_without_rows() -> None:
    analysis = (ROOT / "11_bigquery_notebook_non_traumatic_sah_analysis.py").read_text()

    assert "BigQuery read job:" in analysis
    assert "BigQuery load job:" in analysis


def test_eicu_validation_logs_bigquery_job_provenance_without_rows() -> None:
    validation = (ROOT / "scripts/15_run_eicu_external_validation.py").read_text()

    assert "BigQuery read job:" in validation
    assert "BigQuery load job:" in validation


def test_freeze_qc_sql_covers_grain_repeats_and_time_contract() -> None:
    qc_sql = (ROOT / "16_freeze_release_qc.sql").read_text()

    assert "duplicate_stay_rows" in qc_sql
    assert "subjects_with_repeated_admissions" in qc_sql
    assert "feature_window_end" in qc_sql
    assert "eligible_include_massive_transfusion_sensitivity" in qc_sql


def test_result_figures_use_frozen_aggregate_tables_not_simulated_values() -> None:
    figures = (ROOT / "scripts/generate_manuscript_figures.py").read_text()

    assert "phenotype_log_pca_kmeans_bootstrap_stability" in figures
    assert "phenotype_sensitivity_cohort_summary" in figures
    assert "eicu_external_outcome_summary_by_phenotype" in figures
    assert "phenotype_cluster_centers_zscore" in figures
    assert "phenotype_outcome_summary" in figures
    assert "phenotype_external_severity_validation" in figures
    assert "phenotype_prediction_metrics" in figures
    assert "phenotype_k_selection_metrics" in figures
    assert "phenotype_k3_k4_refinement_crosstab" in figures
    assert "phenotype_log_pca_kmeans_loadings" in figures
    assert "phenotype_severity_score_adjusted_models" in figures
    bootstrap_start = figures.index("def fig_s2_bootstrap")
    bootstrap_end = figures.index("\ndef fig_s3_sensitivity_summary", bootstrap_start)
    assert "np.random" not in figures[bootstrap_start:bootstrap_end]


def test_public_figures_suppress_small_nonzero_cells() -> None:
    figures = (ROOT / "scripts" / "generate_manuscript_figures.py").read_text()

    assert 'return "<10" if 0 < value < 10' in figures
    assert "_redact_small_transition_rows" in figures
    assert "_format_public_count(int(data[i, j]))" in figures
