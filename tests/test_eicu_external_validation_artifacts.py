from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_eicu_validation_sql_defines_current_primary_feature_set() -> None:
    sql = read_text("14_create_eicu_external_validation_cohort.sql")

    assert "pt - inr" in sql.lower()
    assert "gcs_motor_min_48h" in sql
    assert "eligible_external_validation" in sql
    assert "eligible_external_strict_sah_sensitivity" in sql
    assert "eicu_apache_severity" in sql
    assert "shock_index_pair_count_48h" in sql
    assert "eicu_inr_missingness_audit" in sql
    assert "eicu_analysis_features_48h" in sql


def test_eicu_transport_script_uses_frozen_mimic_pipeline_as_primary() -> None:
    script = read_text("scripts/15_run_eicu_external_validation.py")

    assert "frozen_mimic_transport" in script
    assert "eicu_external_phenotype_assignments" in script
    assert "eicu_de_novo_k3_metrics" in script
    assert "AdjustedRandIndex" not in script
    assert "adjusted_rand_score" in script
    assert "phenotype_hb_free_anemia_regression" in script
    assert "INR_FREE_FEATURES" in script
    assert "eicu_external_sensitivity_summary" in script
    assert "eicu_external_severity_validation" in script


def test_eicu_validation_report_records_rationale_and_results() -> None:
    report = read_text("docs/eicu_external_validation.md")

    assert "Frozen Transport" in report
    assert "De Novo" in report
    assert "Why This Validation Strategy" in report
    assert "Current External Validation Results" in report
    assert "Sensitivity Robustness" in report
    assert "APACHE" in report
