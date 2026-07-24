from pathlib import Path
import importlib.util
import inspect
import json
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def load_validation_module():
    script_path = ROOT / "scripts" / "15_run_eicu_external_validation.py"
    spec = importlib.util.spec_from_file_location("eicu_external_validation", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


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


def test_eicu_evaluation_entrypoint_only_loads_prebuilt_mimic_transforms() -> None:
    module = load_validation_module()

    main_source = inspect.getsource(module.main)
    script = read_text("scripts/15_run_eicu_external_validation.py")

    assert "--frozen-transform-bundle" in script
    assert "load_frozen_transform_bundle" in main_source
    assert "fit_frozen_mimic_pipeline" not in main_source
    assert "mimic_table" not in main_source


def test_prebuilt_transform_bundle_assigns_without_sklearn_fitting(
    tmp_path: Path,
) -> None:
    module = load_validation_module()

    def transform_payload(features: list[str]) -> dict:
        n_features = len(features)
        return {
            "features": features,
            "imputation_medians": [0.0] * n_features,
            "scaler_mean": [0.0] * n_features,
            "scaler_scale": [1.0] * n_features,
            "pca_mean": [0.0] * n_features,
            "pca_components": [
                [1.0 if column == row else 0.0 for column in range(n_features)]
                for row in range(3)
            ],
            "centroids_pc": [
                {"phenotype": 1, "pc1": -10.0, "pc2": 0.0, "pc3": 0.0},
                {"phenotype": 2, "pc1": 0.0, "pc2": 0.0, "pc3": 0.0},
                {"phenotype": 3, "pc1": 10.0, "pc2": 0.0, "pc3": 0.0},
            ],
            "centers_z": [
                {"phenotype": phenotype, **{feature: 0.0 for feature in features}}
                for phenotype in (1, 2, 3)
            ],
        }

    artifact = tmp_path / "frozen.json"
    artifact.write_text(
        json.dumps(
            {
                "artifact_version": "1.0",
                "artifact_class": "DERIVED_SENSITIVE",
                "transforms": {
                    "primary": transform_payload(module.FEATURES),
                    "hb_free": transform_payload(module.HB_FREE_FEATURES),
                    "inr_free": transform_payload(module.INR_FREE_FEATURES),
                },
            }
        ),
        encoding="utf-8",
    )

    pipeline = module.load_frozen_transform_bundle(artifact)["primary"]
    assignments, pc_scores = module.apply_frozen_transport(
        pd.DataFrame([{feature: 0.0 for feature in module.FEATURES}]),
        pipeline,
    )

    assert pc_scores.shape == (1, 3)
    assert assignments.loc[0, "phenotype"] == 2


def test_authorized_transform_exporter_writes_private_artifact_contract() -> None:
    exporter = read_text("scripts/export_mimic_frozen_transform_bundle.py")

    assert "fit_frozen_mimic_pipeline" in exporter
    assert "frozen_pipeline_to_dict" in exporter
    assert "DERIVED_SENSITIVE" in exporter
    assert "chmod(0o600)" in exporter


def test_eicu_validation_report_records_rationale_and_results() -> None:
    report = read_text("docs/eicu_external_validation.md")

    assert "Frozen Transport" in report
    assert "De Novo" in report
    assert "Why This Validation Strategy" in report
    assert "Current External Validation Results" in report
    assert "Sensitivity Robustness" in report
    assert "APACHE" in report


def test_hospital_cluster_bootstrap_is_deterministic_and_aggregate_only() -> None:
    module = load_validation_module()
    assignments = pd.DataFrame(
        [
            {"hospitalid": hospital, "phenotype": phenotype, "hospital_mortality": death}
            for hospital, outcomes in {
                101: {1: [0, 0], 2: [0, 1], 3: [1, 1]},
                102: {1: [0, 0], 2: [1, 1], 3: [0, 1]},
                103: {1: [0, 0], 2: [0, 1], 3: [1, 1]},
                104: {1: [0, 1], 2: [0, 1], 3: [1, 1]},
            }.items()
            for phenotype, phenotype_outcomes in outcomes.items()
            for death in phenotype_outcomes
        ]
    )

    first = module.build_hospital_cluster_bootstrap(
        assignments,
        iterations=200,
        random_seed=123,
    )
    second = module.build_hospital_cluster_bootstrap(
        assignments,
        iterations=200,
        random_seed=123,
    )

    pd.testing.assert_frame_equal(first, second)
    assert set(first["metric"]) == {
        "p1_hospital_mortality",
        "p2_hospital_mortality",
        "p3_hospital_mortality",
        "p2_minus_p1_risk_difference",
        "p3_minus_p1_risk_difference",
    }
    assert first["n_hospitals"].eq(4).all()
    assert first["bootstrap_iterations"].eq(200).all()
    assert first["random_seed"].eq(123).all()
    assert "hospitalid" not in first.columns


def test_leave_one_hospital_out_reports_influence_without_identifiers() -> None:
    module = load_validation_module()
    assignments = pd.DataFrame(
        [
            {"hospitalid": hospital, "phenotype": phenotype, "hospital_mortality": death}
            for hospital, outcomes in {
                101: {1: [0, 0], 2: [0, 1], 3: [1, 1]},
                102: {1: [0, 0], 2: [1, 1], 3: [0, 1]},
                103: {1: [0, 0], 2: [0, 1], 3: [1, 1]},
                104: {1: [0, 1], 2: [0, 1], 3: [1, 1]},
            }.items()
            for phenotype, phenotype_outcomes in outcomes.items()
            for death in phenotype_outcomes
        ]
    )

    summary = module.build_leave_one_hospital_out(assignments)

    assert len(summary) == 1
    assert summary.loc[0, "n_hospitals"] == 4
    assert summary.loc[0, "iterations"] == 4
    assert summary.loc[0, "monotonic_order_retained_n"] == 4
    assert summary.loc[0, "monotonic_order_retained_rate"] == 1.0
    assert summary.loc[0, "p2_minus_p1_min"] > 0
    assert summary.loc[0, "p3_minus_p1_min"] > 0
    assert "hospitalid" not in summary.columns
