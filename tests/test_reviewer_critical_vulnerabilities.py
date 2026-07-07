from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_aneurysmal_sah_evidence_uses_i60_or_procedure_not_unruptured_dx_only() -> None:
    sql = read_text("10_create_non_traumatic_sah_cohort.sql")

    assert "has_ruptured_aneurysmal_sah_evidence" in sql
    assert "has_unruptured_aneurysm_dx" in sql
    assert "COALESCE(dx.has_sah_dx, 0) = 1" in sql
    assert "COALESCE(proc.has_aneurysm_procedure, 0) = 1" in sql


def test_hb_free_anemia_regression_sensitivity_is_written() -> None:
    analysis = read_text("11_bigquery_notebook_non_traumatic_sah_analysis.py")

    assert '"hb_free_anemia_regression"' in analysis
    assert "phenotype_hb_free_anemia_regression" in analysis
    assert "run_hb_free_anemia_regression" in analysis
    assert "hb_free_sensitivity[\"assignments\"]" in analysis


def test_process_of_care_cox_is_exploratory_not_fixed_baseline_adjustment() -> None:
    analysis = read_text("11_bigquery_notebook_non_traumatic_sah_analysis.py")
    prompt = read_text("scripts/prompt_for_regenerating_manuscript.md")

    assert "cox_phenotype_process_of_care_exploratory" in analysis
    assert "immortal time bias" in analysis.lower()
    assert "time-varying covariates" in analysis.lower()
    assert "immortal time bias" in prompt.lower()
