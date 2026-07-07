# BigQuery Notebook 可直接运行的 non-traumatic SAH 早期生理表型分析脚本
#
# 使用方式：
# 1. 在 BigQuery Notebook / Colab Enterprise 新建 Python notebook。
# 2. 确认已经运行过 10_create_non_traumatic_sah_cohort.sql。
# 3. 把本脚本整段复制到一个 Python cell 中运行，或上传后执行：
#       %run 11_bigquery_notebook_non_traumatic_sah_analysis.py
#
# 脚本会直接读取：
#   mimic-study-498508.non_traumatic_sah_study.physiology_features_48h
#
# 并写回以下 BigQuery 表：
#   phenotype_k_selection_metrics
#   phenotype_cluster_assignments                  (primary log1p + PCA K=3)
#   phenotype_cluster_centers_zscore              (primary log1p + PCA K=3)
#   phenotype_feature_summary_raw                 (primary log1p + PCA K=3)
#   phenotype_outcome_summary                     (primary log1p + PCA K=3)
#   phenotype_anemia_feasibility                  (primary log1p + PCA K=3)
#   phenotype_lightweight_tests                   (primary log1p + PCA K=3)
#   phenotype_cluster_stability                   (primary log1p + PCA K=3)
#   phenotype_bootstrap_stability                 (primary log1p + PCA K=3)
#   phenotype_gcs_sensitivity_summary             (primary K=3 sensitivity)
#   phenotype_prediction_metrics                  (mortality prediction increment)
#   phenotype_regression_models                   (adjusted outcome models)
#   phenotype_severity_score_adjusted_models      (phenotype adjusted for SOFA/SAPSII/OASIS/LODS)
#   phenotype_process_of_care_audit               (process-of-care and fluid balance audit)
#   phenotype_process_of_care_adjusted_models     (process-of-care adjusted sensitivity models)
#   phenotype_survival_km_curve                   (Kaplan-Meier hospital survival curve by phenotype)
#   phenotype_survival_logrank                    (pairwise log-rank tests by phenotype)
#   phenotype_survival_cox_models                 (phenotype Cox models for in-hospital death timing)
#   phenotype_feature_heatmap                     (reviewer-facing phenotype feature heatmap data)
#   phenotype_shap_feature_importance             (linear logistic SHAP-style feature importance)
#   phenotype_shap_phenotype_contributions        (SHAP-style contributions summarized by phenotype)
#   phenotype_anemia_stratified_models            (anemia OR within each K=3 phenotype)
#   phenotype_candidate_feature_audit             (ePVS/troponin/blood gas audit)
#   phenotype_baseline_characteristics            (Table 1 baseline by phenotype)
#   phenotype_sensitivity_cohort_summary          (no RBC and ICU LOS >=48h sensitivity)
#   phenotype_epvs_sensitivity_summary            (candidate ePVS clustering sensitivity)
#   phenotype_hb_free_sensitivity                 (Hb-free clustering sensitivity)
#   phenotype_hb_free_centers_zscore              (Hb-free standardized centers)
#   phenotype_hb_free_anemia_regression           (anemia model adjusted by Hb-free phenotype)
#   phenotype_inr_free_sensitivity                (INR-free clustering sensitivity)
#   phenotype_inr_free_centers_zscore             (INR-free standardized centers)
#   phenotype_complete_case_sensitivity           (complete-case clustering sensitivity)
#   phenotype_complete_case_centers_zscore        (complete-case standardized centers)
#   phenotype_log_pca_complete_case_sensitivity   (log-PCA complete-case sensitivity)
#   phenotype_24h_window_sensitivity              (0-24h log-PCA sensitivity)
#   phenotype_external_severity_validation        (SOFA/SAPSII/OASIS/LODS validation)
#   phenotype_strict_aneurysm_*                   (high-specificity aneurysm evidence subgroup)
#   phenotype_lpa_*_sensitivity                   (model-based LPA/GMM sensitivity in log-PCA space)
#   phenotype_raw_kmeans_*_sensitivity            (raw standardized 8-variable K-means sensitivity)
#   phenotype_log_pca_kmeans_sensitivity          (primary log1p + PCA K-means audit copy)
#   phenotype_log_pca_kmeans_centers_zscore       (log1p + PCA standardized centers)
#   phenotype_log_pca_kmeans_loadings             (PCA component loadings)
#   phenotype_log_pca_kmeans_bootstrap_stability  (log1p + PCA bootstrap stability)
#   phenotype_*_k4_exploratory                    (K=4 high-resolution sensitivity)
#   phenotype_k3_k4_refinement_crosstab

from __future__ import annotations

import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from google.cloud import bigquery
from scipy import stats
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.mixture import GaussianMixture
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    adjusted_rand_score,
    brier_score_loss,
    calinski_harabasz_score,
    davies_bouldin_score,
    roc_auc_score,
    silhouette_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


warnings.filterwarnings("ignore", category=FutureWarning)


def show_or_close_current_figure() -> None:
    """Show figures in notebooks and close them in non-interactive terminal runs."""
    backend = plt.get_backend().lower()
    if "agg" in backend:
        plt.close()
        return
    plt.show()


def prepare_logit_dataframe(
    df: pd.DataFrame,
    numeric_columns: list[str],
    categorical_columns: list[str],
    required_columns: list[str],
) -> pd.DataFrame:
    """Convert pandas nullable dtypes to statsmodels-friendly numeric/object dtypes."""
    model_df = df.copy()
    for col in numeric_columns:
        model_df[col] = pd.to_numeric(model_df[col], errors="coerce").astype(float)
    for col in categorical_columns:
        model_df[col] = model_df[col].astype("object").where(model_df[col].notna(), "Unknown")
    return model_df.dropna(subset=required_columns)


def collapse_admission_type(value: object) -> str:
    """Collapse sparse MIMIC admission types for stable adjusted regression."""
    text = str(value).upper()
    if "OBSERVATION" in text:
        return "observation"
    if "ELECTIVE" in text or "SURGICAL SAME DAY" in text:
        return "elective_or_surgical"
    if "URGENT" in text:
        return "urgent"
    if "EMER" in text or text.startswith("EW"):
        return "emergency"
    return "other"


def collapse_race(value: object) -> str:
    """Collapse sparse MIMIC race labels for stable descriptive Table 1 reporting."""
    text = str(value).upper()
    if not text or text in {"NAN", "NONE"}:
        return "Unknown"
    if "WHITE" in text:
        return "White"
    if "BLACK" in text or "AFRICAN" in text:
        return "Black"
    if "UNKNOWN" in text or "UNABLE" in text or "DECLINED" in text or "PATIENT DECLINED" in text:
        return "Unknown"
    return "Other"


def fit_logit_quiet(smf, formula: str, data: pd.DataFrame):
    """Fit a logit model without noisy optimizer warnings in terminal logs."""
    from statsmodels.tools.sm_exceptions import ConvergenceWarning

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=ConvergenceWarning)
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        return smf.logit(formula, data=data).fit(disp=False, maxiter=200)


def build_adjusted_regression_formulas(model_df: pd.DataFrame) -> dict[str, str]:
    """Build adjusted formulas while skipping constant or duplicated covariates."""
    adjustment_terms = ["age", "C(gender)", "C(admission_type_group)"]
    note_parts = ["collapsed sparse admission_type categories for model stability"]

    if model_df["nsah_evidence_level"].nunique(dropna=True) > 1:
        adjustment_terms.append("C(nsah_evidence_level)")
    else:
        note_parts.append("skipped constant nsah_evidence_level")

    if model_df["has_aneurysm_dx"].nunique(dropna=True) > 1:
        adjustment_terms.append("has_aneurysm_dx")
    else:
        note_parts.append("skipped constant has_aneurysm_dx")

    procedure_duplicates_evidence = (
        model_df["has_aneurysm_procedure"].nunique(dropna=True) > 1
        and model_df["nsah_evidence_level"].nunique(dropna=True) > 1
        and model_df["has_aneurysm_procedure"].astype(int).equals(
            (model_df["nsah_evidence_level"].astype(int) == 3).astype(int)
        )
    )
    if procedure_duplicates_evidence:
        note_parts.append("skipped has_aneurysm_procedure because it duplicates nsah_evidence_level=3")
    elif model_df["has_aneurysm_procedure"].nunique(dropna=True) > 1:
        adjustment_terms.append("has_aneurysm_procedure")
    else:
        note_parts.append("skipped constant has_aneurysm_procedure")

    adjustment = " + ".join(adjustment_terms)
    note = "; ".join(note_parts)
    return {
        "adjusted_main_effect": f"hospital_mortality ~ C(phenotype) + early_anemia_all + {adjustment}",
        "adjusted_anemia_interaction": f"hospital_mortality ~ C(phenotype) * early_anemia_all + {adjustment}",
        "_note": note,
    }

# =============================================================================
# 0. 配置区
# =============================================================================

PROJECT_ID = "mimic-study-498508"
DATASET_ID = "non_traumatic_sah_study"
INPUT_TABLE = f"{PROJECT_ID}.{DATASET_ID}.physiology_features_48h"

# 主分析使用 K=3；K=4 作为高分辨率敏感性分析，用于观察重症组内是否可进一步
# 分离出小型极高危表型。
PRIMARY_K = 3
EXPLORATORY_K = 4
K_MIN = 2
K_MAX = 5
MIN_CLUSTER_FRAC = 0.05
RANDOM_SEED = 42
BOOTSTRAP_N = 200
CV_FOLDS = 5
PCA_COMPONENTS = 3
LOG_TRANSFORM_FEATURES = ["creatinine_max_48h", "inr_max_48h"]
LOG_TRANSFORM_FEATURES_24H = ["creatinine_max_24h", "inr_max_24h"]

# cohort 选择：
#   eligible_primary_analysis: 主分析
#   eligible_no_transfusion_sensitivity: 排除所有 0-48h RBC 输血患者
#   eligible_sensitivity_48h_los: ICU LOS >=48h 敏感性分析
COHORT_FLAG = "eligible_primary_analysis"

FEATURES = [
    "hb_min_48h_all",
    "gcs_motor_min_48h",
    "map_min_48h",
    "shock_index_max_48h",
    "spo2_min_48h",
    "creatinine_max_48h",
    "inr_max_48h",
    "platelet_min_48h",
]
FEATURES_24H = [
    "hb_min_24h_all",
    "gcs_motor_min_24h",
    "map_min_24h",
    "shock_index_max_24h",
    "spo2_min_24h",
    "creatinine_max_24h",
    "inr_max_24h",
    "platelet_min_24h",
]
HB_FREE_FEATURES = [feature for feature in FEATURES if feature != "hb_min_48h_all"]
INR_FREE_FEATURES = [feature for feature in FEATURES if feature != "inr_max_48h"]

FEATURE_LABELS = {
    "hb_min_48h_all": "Hb min",
    "gcs_min_48h": "GCS min",
    "gcs_motor_min_48h": "GCS motor min",
    "map_min_48h": "MAP min",
    "shock_index_max_48h": "Shock index max",
    "spo2_min_48h": "SpO2 min",
    "creatinine_max_48h": "Creatinine max",
    "inr_max_48h": "INR max",
    "sodium_max_48h": "Sodium max",
    "platelet_min_48h": "Platelet min",
    "hb_min_24h_all": "Hb min 24h",
    "gcs_motor_min_24h": "GCS motor min 24h",
    "map_min_24h": "MAP min 24h",
    "shock_index_max_24h": "Shock index max 24h",
    "spo2_min_24h": "SpO2 min 24h",
    "creatinine_max_24h": "Creatinine max 24h",
    "inr_max_24h": "INR max 24h",
    "platelet_min_24h": "Platelet min 24h",
}

# 标准化后，正方向代表生理状态更差。
SEVERITY_DIRECTIONS = {
    "hb_min_48h_all": -1,
    "gcs_min_48h": -1,
    "gcs_motor_min_48h": -1,
    "gcs_grade_min_48h": 1,
    "map_min_48h": -1,
    "shock_index_max_48h": 1,
    "spo2_min_48h": -1,
    "creatinine_max_48h": 1,
    "inr_max_48h": 1,
    "sodium_max_48h": 1,
    "platelet_min_48h": -1,
    "epvs_mean_48h": 1,
    "hb_min_24h_all": -1,
    "gcs_motor_min_24h": -1,
    "map_min_24h": -1,
    "shock_index_max_24h": 1,
    "spo2_min_24h": -1,
    "creatinine_max_24h": 1,
    "inr_max_24h": 1,
    "platelet_min_24h": -1,
}

GCS_SENSITIVITY_FEATURE_SETS = {
    "raw_8_gcs_motor_reference": FEATURES,
    "add_total_gcs": [
        "hb_min_48h_all",
        "gcs_min_48h",
        "gcs_motor_min_48h",
        "map_min_48h",
        "shock_index_max_48h",
        "spo2_min_48h",
        "creatinine_max_48h",
        "inr_max_48h",
        "platelet_min_48h",
    ],
    "gcs_total_only": [
        "hb_min_48h_all",
        "gcs_min_48h",
        "map_min_48h",
        "shock_index_max_48h",
        "spo2_min_48h",
        "creatinine_max_48h",
        "inr_max_48h",
        "platelet_min_48h",
    ],
    "gcs_grade_alternative": [
        "hb_min_48h_all",
        "gcs_grade_min_48h",
        "map_min_48h",
        "shock_index_max_48h",
        "spo2_min_48h",
        "creatinine_max_48h",
        "inr_max_48h",
        "platelet_min_48h",
    ],
}

CANDIDATE_AUDIT_FEATURES = [
    "epvs_mean_48h",
    "epvs_first_48h",
    "epvs_max_48h",
    "troponin_peak_48h",
    "troponin_peak_m6_48h",
    "sodium_max_48h",
    "lactate_max_48h",
    "lactate_max_m6_48h",
    "pao2_fio2_min_48h",
    "spo2_fio2_min_48h",
    "oxygenation_min_48h",
    "sofa_24h",
    "sapsii_24h",
    "apsiii_24h",
    "oasis_24h",
    "lods_24h",
]

SENSITIVITY_COHORT_FLAGS = {
    "no_rbc_48h": "eligible_no_transfusion_sensitivity",
    "icu_los_ge_48h": "eligible_sensitivity_48h_los",
}

EPVS_SENSITIVITY_FEATURE_SETS = {
    "main_8": FEATURES,
    "add_epvs_mean": [*FEATURES, "epvs_mean_48h"],
}

PROCESS_OF_CARE_BINARY_FEATURES = [
    "aneurysm_securing_hosp",
    "nimodipine_48h",
    "evd_or_icp_48h",
    "vasopressor_48h",
    "mech_vent_48h",
    "noninvasive_vent_48h",
    "any_rbc_transfusion_48h",
    "crrt_48h",
    "fluid_balance_complete_48h",
]

PROCESS_OF_CARE_CONTINUOUS_FEATURES = [
    "fluid_input_ml_48h",
    "fluid_output_ml_48h",
    "fluid_balance_ml_48h",
    "fluid_balance_l_48h",
]

PROCESS_OF_CARE_MODEL_FEATURES = [
    "aneurysm_securing_hosp",
    "nimodipine_48h",
    "evd_or_icp_48h",
    "vasopressor_48h",
    "mech_vent_48h",
    "any_rbc_transfusion_48h",
    "crrt_48h",
    "fluid_balance_l_48h",
]

BASELINE_CONTINUOUS_FEATURES = [
    "age",
    "icu_los_days",
    "hospital_los_days",
    "hb_min_48h_all",
    "hb_min_48h_pre_transfusion",
    "gcs_min_48h",
    "gcs_grade_min_48h",
    "wfns_gcs_grade_min_48h",
    "epvs_mean_48h",
    "troponin_peak_48h",
    "troponin_peak_m6_48h",
    "lactate_max_48h",
    "lactate_max_m6_48h",
    "pao2_fio2_min_48h",
    "spo2_fio2_min_48h",
    "oxygenation_min_48h",
    "sofa_24h",
    "sofa_respiration_24h",
    "sofa_coagulation_24h",
    "sofa_liver_24h",
    "sofa_cardiovascular_24h",
    "sofa_cns_24h",
    "sofa_renal_24h",
    "sapsii_24h",
    "sapsii_prob_24h",
    "apsiii_24h",
    "apsiii_prob_24h",
    "oasis_24h",
    "oasis_prob_24h",
    "lods_24h",
    *PROCESS_OF_CARE_CONTINUOUS_FEATURES,
    *FEATURES,
]
BASELINE_CONTINUOUS_FEATURES = list(dict.fromkeys(BASELINE_CONTINUOUS_FEATURES))

BASELINE_CATEGORICAL_FEATURES = [
    "gender",
    "race_group",
    "admission_type",
    "insurance",
    "nsah_evidence_level",
    "has_aneurysm_dx",
    "has_unruptured_aneurysm_dx",
    "has_ruptured_aneurysmal_sah_dx",
    "has_ruptured_aneurysmal_sah_evidence",
    "has_aneurysm_procedure",
    "early_anemia_all",
    "early_anemia_pre_transfusion",
    "any_rbc_transfusion_48h",
    "massive_transfusion_24h",
    *PROCESS_OF_CARE_BINARY_FEATURES,
]

OUTPUT_TABLES = {
    "k_metrics": f"{PROJECT_ID}.{DATASET_ID}.phenotype_k_selection_metrics",
    "assignments": f"{PROJECT_ID}.{DATASET_ID}.phenotype_cluster_assignments",
    "centers": f"{PROJECT_ID}.{DATASET_ID}.phenotype_cluster_centers_zscore",
    "feature_summary": f"{PROJECT_ID}.{DATASET_ID}.phenotype_feature_summary_raw",
    "outcome_summary": f"{PROJECT_ID}.{DATASET_ID}.phenotype_outcome_summary",
    "anemia_feasibility": f"{PROJECT_ID}.{DATASET_ID}.phenotype_anemia_feasibility",
    "gcs_motor_distribution": f"{PROJECT_ID}.{DATASET_ID}.phenotype_gcs_motor_distribution",
    "tests": f"{PROJECT_ID}.{DATASET_ID}.phenotype_lightweight_tests",
    "stability": f"{PROJECT_ID}.{DATASET_ID}.phenotype_cluster_stability",
    "bootstrap_stability": f"{PROJECT_ID}.{DATASET_ID}.phenotype_bootstrap_stability",
    "gcs_sensitivity": f"{PROJECT_ID}.{DATASET_ID}.phenotype_gcs_sensitivity_summary",
    "prediction_metrics": f"{PROJECT_ID}.{DATASET_ID}.phenotype_prediction_metrics",
    "regression_models": f"{PROJECT_ID}.{DATASET_ID}.phenotype_regression_models",
    "severity_score_adjusted_models": f"{PROJECT_ID}.{DATASET_ID}.phenotype_severity_score_adjusted_models",
    "process_of_care_audit": f"{PROJECT_ID}.{DATASET_ID}.phenotype_process_of_care_audit",
    "process_of_care_adjusted_models": f"{PROJECT_ID}.{DATASET_ID}.phenotype_process_of_care_adjusted_models",
    "survival_km_curve": f"{PROJECT_ID}.{DATASET_ID}.phenotype_survival_km_curve",
    "survival_logrank": f"{PROJECT_ID}.{DATASET_ID}.phenotype_survival_logrank",
    "survival_cox_models": f"{PROJECT_ID}.{DATASET_ID}.phenotype_survival_cox_models",
    "feature_heatmap": f"{PROJECT_ID}.{DATASET_ID}.phenotype_feature_heatmap",
    "shap_feature_importance": f"{PROJECT_ID}.{DATASET_ID}.phenotype_shap_feature_importance",
    "shap_phenotype_contributions": f"{PROJECT_ID}.{DATASET_ID}.phenotype_shap_phenotype_contributions",
    "anemia_stratified_models": f"{PROJECT_ID}.{DATASET_ID}.phenotype_anemia_stratified_models",
    "candidate_feature_audit": f"{PROJECT_ID}.{DATASET_ID}.phenotype_candidate_feature_audit",
    "baseline_characteristics": f"{PROJECT_ID}.{DATASET_ID}.phenotype_baseline_characteristics",
    "sensitivity_cohort_summary": f"{PROJECT_ID}.{DATASET_ID}.phenotype_sensitivity_cohort_summary",
    "epvs_sensitivity": f"{PROJECT_ID}.{DATASET_ID}.phenotype_epvs_sensitivity_summary",
    "hb_free_sensitivity": f"{PROJECT_ID}.{DATASET_ID}.phenotype_hb_free_sensitivity",
    "hb_free_centers": f"{PROJECT_ID}.{DATASET_ID}.phenotype_hb_free_centers_zscore",
    "hb_free_anemia_regression": f"{PROJECT_ID}.{DATASET_ID}.phenotype_hb_free_anemia_regression",
    "inr_free_sensitivity": f"{PROJECT_ID}.{DATASET_ID}.phenotype_inr_free_sensitivity",
    "inr_free_centers": f"{PROJECT_ID}.{DATASET_ID}.phenotype_inr_free_centers_zscore",
    "complete_case_sensitivity": f"{PROJECT_ID}.{DATASET_ID}.phenotype_complete_case_sensitivity",
    "complete_case_centers": f"{PROJECT_ID}.{DATASET_ID}.phenotype_complete_case_centers_zscore",
    "log_pca_complete_case_sensitivity": f"{PROJECT_ID}.{DATASET_ID}.phenotype_log_pca_complete_case_sensitivity",
    "log_pca_complete_case_centers": f"{PROJECT_ID}.{DATASET_ID}.phenotype_log_pca_complete_case_centers_zscore",
    "window_24h_sensitivity": f"{PROJECT_ID}.{DATASET_ID}.phenotype_24h_window_sensitivity",
    "window_24h_centers": f"{PROJECT_ID}.{DATASET_ID}.phenotype_24h_window_centers_zscore",
    "external_severity_validation": f"{PROJECT_ID}.{DATASET_ID}.phenotype_external_severity_validation",
    "strict_aneurysm_assignments": f"{PROJECT_ID}.{DATASET_ID}.phenotype_strict_aneurysm_subgroup_assignments",
    "strict_aneurysm_summary": f"{PROJECT_ID}.{DATASET_ID}.phenotype_strict_aneurysm_subgroup_summary",
    "strict_aneurysm_centers": f"{PROJECT_ID}.{DATASET_ID}.phenotype_strict_aneurysm_subgroup_centers_zscore",
    "strict_aneurysm_outcomes": f"{PROJECT_ID}.{DATASET_ID}.phenotype_strict_aneurysm_subgroup_outcomes",
    "strict_aneurysm_severity_validation": f"{PROJECT_ID}.{DATASET_ID}.phenotype_strict_aneurysm_subgroup_severity_validation",
    "strict_aneurysm_regression": f"{PROJECT_ID}.{DATASET_ID}.phenotype_strict_aneurysm_subgroup_regression",
    "strict_aneurysm_severity_score_adjusted_models": f"{PROJECT_ID}.{DATASET_ID}.phenotype_strict_aneurysm_subgroup_severity_score_adjusted_models",
    "lpa_fit_indices": f"{PROJECT_ID}.{DATASET_ID}.phenotype_lpa_fit_indices",
    "lpa_assignments": f"{PROJECT_ID}.{DATASET_ID}.phenotype_lpa_assignments_sensitivity",
    "lpa_outcome_summary": f"{PROJECT_ID}.{DATASET_ID}.phenotype_lpa_outcome_summary_sensitivity",
    "lpa_centers": f"{PROJECT_ID}.{DATASET_ID}.phenotype_lpa_centers_zscore_sensitivity",
    "lpa_severity_validation": f"{PROJECT_ID}.{DATASET_ID}.phenotype_lpa_severity_validation_sensitivity",
    "log_pca_kmeans_sensitivity": f"{PROJECT_ID}.{DATASET_ID}.phenotype_log_pca_kmeans_sensitivity",
    "log_pca_kmeans_centers": f"{PROJECT_ID}.{DATASET_ID}.phenotype_log_pca_kmeans_centers_zscore",
    "log_pca_kmeans_loadings": f"{PROJECT_ID}.{DATASET_ID}.phenotype_log_pca_kmeans_loadings",
    "log_pca_kmeans_bootstrap_stability": f"{PROJECT_ID}.{DATASET_ID}.phenotype_log_pca_kmeans_bootstrap_stability",
    "raw_kmeans_assignments": f"{PROJECT_ID}.{DATASET_ID}.phenotype_raw_kmeans_assignments_sensitivity",
    "raw_kmeans_centers": f"{PROJECT_ID}.{DATASET_ID}.phenotype_raw_kmeans_centers_zscore_sensitivity",
    "raw_kmeans_outcome_summary": f"{PROJECT_ID}.{DATASET_ID}.phenotype_raw_kmeans_outcome_summary_sensitivity",
    "raw_kmeans_bootstrap_stability": f"{PROJECT_ID}.{DATASET_ID}.phenotype_raw_kmeans_bootstrap_stability_sensitivity",
    "assignments_k4": f"{PROJECT_ID}.{DATASET_ID}.phenotype_cluster_assignments_k4_exploratory",
    "centers_k4": f"{PROJECT_ID}.{DATASET_ID}.phenotype_cluster_centers_zscore_k4_exploratory",
    "feature_summary_k4": f"{PROJECT_ID}.{DATASET_ID}.phenotype_feature_summary_raw_k4_exploratory",
    "outcome_summary_k4": f"{PROJECT_ID}.{DATASET_ID}.phenotype_outcome_summary_k4_exploratory",
    "anemia_feasibility_k4": f"{PROJECT_ID}.{DATASET_ID}.phenotype_anemia_feasibility_k4_exploratory",
    "tests_k4": f"{PROJECT_ID}.{DATASET_ID}.phenotype_lightweight_tests_k4_exploratory",
    "stability_k4": f"{PROJECT_ID}.{DATASET_ID}.phenotype_cluster_stability_k4_exploratory",
    "k3_k4_crosstab": f"{PROJECT_ID}.{DATASET_ID}.phenotype_k3_k4_refinement_crosstab",
}


# =============================================================================
# 1. BigQuery 工具函数
# =============================================================================

client = bigquery.Client(project=PROJECT_ID)


def read_table_from_bigquery() -> pd.DataFrame:
    """从 BigQuery 读取最终宽表，并只保留当前 cohort flag 对应样本。"""
    selected_columns = [
        "subject_id",
        "hadm_id",
        "stay_id",
        "age",
        "gender",
        "race",
        "admission_type",
        "insurance",
        "nsah_evidence_level",
        "has_aneurysm_dx",
        "has_unruptured_aneurysm_dx",
        "has_ruptured_aneurysmal_sah_dx",
        "has_ruptured_aneurysmal_sah_evidence",
        "has_aneurysm_procedure",
        "icu_los_days",
        "hospital_los_days",
        "hospital_mortality",
        "icu_mortality",
        "early_anemia_all",
        "early_anemia_pre_transfusion",
        "any_rbc_transfusion_48h",
        "massive_transfusion_24h",
        "vasopressor_48h",
        "first_vasopressor_time_48h",
        "vasopressor_events_48h",
        "vasopressor_labels_48h",
        "mech_vent_48h",
        "noninvasive_vent_48h",
        "first_mech_vent_time_48h",
        "invasive_vent_events_48h",
        "noninvasive_vent_events_48h",
        "ventilation_labels_48h",
        "evd_or_icp_48h",
        "first_evd_or_icp_time_48h",
        "evd_icp_proc_events_48h",
        "evd_icp_chart_events_48h",
        "evd_icp_proc_labels_48h",
        "evd_icp_chart_labels_48h",
        "crrt_48h",
        "first_crrt_time_48h",
        "crrt_events_48h",
        "crrt_modes_48h",
        "nimodipine_48h",
        "first_nimodipine_time_48h",
        "nimodipine_orders_48h",
        "nimodipine_drugs_48h",
        "nimodipine_routes_48h",
        "aneurysm_securing_hosp",
        "aneurysm_securing_codes_hosp",
        "fluid_input_ml_48h",
        "fluid_output_ml_48h",
        "fluid_input_events_48h",
        "fluid_output_events_48h",
        "fluid_balance_ml_48h",
        "fluid_balance_l_48h",
        "fluid_balance_complete_48h",
        "hb_min_48h_all",
        "hb_min_48h_pre_transfusion",
        "hb_min_24h_all",
        "hb_min_24h_pre_transfusion",
        "core_feature_missing_count",
        "core_feature_missing_count_24h",
        "eligible_primary_analysis",
        "eligible_no_transfusion_sensitivity",
        "eligible_sensitivity_48h_los",
        "gcs_min_48h",
        "gcs_grade_min_48h",
        "gcs_grade_min_24h",
        "gcs_motor_min_24h",
        "wfns_gcs_grade_min_48h",
        "epvs_mean_48h",
        "epvs_first_48h",
        "epvs_max_48h",
        "troponin_peak_48h",
        "troponin_peak_m6_48h",
        "troponin_labels_48h",
        "troponin_units_48h",
        "troponin_labels_m6_48h",
        "troponin_units_m6_48h",
        "sodium_max_48h",
        "lactate_max_48h",
        "lactate_max_m6_48h",
        "oxygenation_min_48h",
        "pao2_fio2_min_48h",
        "spo2_fio2_min_48h",
        "sofa_24h",
        "sofa_respiration_24h",
        "sofa_coagulation_24h",
        "sofa_liver_24h",
        "sofa_cardiovascular_24h",
        "sofa_cns_24h",
        "sofa_renal_24h",
        "sapsii_24h",
        "sapsii_prob_24h",
        "apsiii_24h",
        "apsiii_prob_24h",
        "oasis_24h",
        "oasis_prob_24h",
        "lods_24h",
        *FEATURES,
        *FEATURES_24H,
    ]
    selected_columns = list(dict.fromkeys(selected_columns))
    sql = f"""
    SELECT {", ".join(selected_columns)}
    FROM `{INPUT_TABLE}`
    WHERE {COHORT_FLAG} = 1
    """
    print(f"读取 BigQuery 表：{INPUT_TABLE}")
    print(f"当前 cohort flag：{COHORT_FLAG} = 1")
    df = client.query(sql).to_dataframe(create_bqstorage_client=False)
    df["race_group"] = df["race"].map(collapse_race)
    print(f"读取完成：{len(df):,} 行，{df.shape[1]} 列")
    return df


def write_dataframe(df: pd.DataFrame, table_id: str) -> None:
    """将 DataFrame 写回 BigQuery，覆盖同名结果表。"""
    df = df.copy()
    df.columns = [str(col) for col in df.columns]
    duplicate_columns = df.columns[df.columns.duplicated()].tolist()
    if duplicate_columns:
        raise ValueError(f"写入 {table_id} 前发现重复列名：{duplicate_columns}")
    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()
    print(f"写回 BigQuery：{table_id} ({len(df):,} 行)")


# =============================================================================
# 2. 数据预处理与聚类
# =============================================================================


def validate_input(df: pd.DataFrame) -> None:
    """检查输入宽表是否包含分析所需字段。"""
    required = [
        "subject_id",
        "hadm_id",
        "stay_id",
        "hospital_mortality",
        "early_anemia_all",
        "age",
        "gender",
        *FEATURES,
    ]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"输入表缺少字段：{missing}")
    if df.empty:
        raise ValueError("当前 cohort 为空，请检查 COHORT_FLAG 或 SQL 中间表。")


def preprocess_feature_matrix(df: pd.DataFrame, features: list[str]):
    """对指定连续/有序变量做中位数填补和 Z-score 标准化。"""
    x_raw = df[features].apply(pd.to_numeric, errors="coerce")
    missing_summary = pd.DataFrame(
        {
            "feature": features,
            "missing_n": [int(x_raw[col].isna().sum()) for col in features],
            "total_n": len(x_raw),
            "missing_rate": [float(x_raw[col].isna().mean()) for col in features],
        }
    ).sort_values("missing_rate", ascending=False)

    imputer = SimpleImputer(strategy="median")
    scaler = StandardScaler()
    x_imputed = imputer.fit_transform(x_raw)
    x_scaled = scaler.fit_transform(x_imputed)
    return x_raw, x_imputed, x_scaled, imputer, scaler, missing_summary


def preprocess_log_pca_feature_matrix(
    df: pd.DataFrame,
    features: list[str] | None = None,
    log_transform_features: list[str] | None = None,
    use_complete_cases: bool = False,
):
    """对偏态变量 log1p 变换后标准化，并提取 PCA 得分。"""
    features = features or FEATURES
    log_transform_features = log_transform_features or LOG_TRANSFORM_FEATURES
    x_raw = df[features].apply(pd.to_numeric, errors="coerce")
    if use_complete_cases:
        x_raw = x_raw.loc[x_raw.notna().all(axis=1)].copy()
    x_transformed = x_raw.copy()
    for feature in log_transform_features:
        if feature not in x_transformed.columns:
            continue
        values = x_transformed[feature].clip(lower=0)
        x_transformed[feature] = np.log1p(values)

    missing_summary = pd.DataFrame(
        {
            "feature": features,
            "missing_n": [int(df[col].isna().sum()) for col in features],
            "total_n": len(df),
            "missing_rate": [float(df[col].isna().mean()) for col in features],
            "transform": ["log1p" if col in log_transform_features else "none" for col in features],
        }
    ).sort_values("missing_rate", ascending=False)

    scaler = StandardScaler()
    if use_complete_cases:
        imputer = None
        x_imputed = x_transformed.to_numpy()
    else:
        imputer = SimpleImputer(strategy="median")
        x_imputed = imputer.fit_transform(x_transformed)
    x_scaled = scaler.fit_transform(x_imputed)

    n_components = min(PCA_COMPONENTS, x_scaled.shape[1], x_scaled.shape[0])
    pca = PCA(n_components=n_components, random_state=RANDOM_SEED)
    pc_scores = pca.fit_transform(x_scaled)
    pc_columns = [f"PC{i + 1}" for i in range(n_components)]
    return x_raw, x_transformed, x_scaled, pc_scores, pc_columns, pca, imputer, scaler, missing_summary


def build_feature_matrix(df: pd.DataFrame):
    """对 8 个核心聚类变量做中位数填补和 Z-score 标准化。"""
    x_raw, x_imputed, x_scaled, imputer, scaler, missing_summary = preprocess_feature_matrix(df, FEATURES)
    display(missing_summary)
    return x_raw, x_imputed, x_scaled, imputer, scaler, missing_summary


def run_k_selection(x_scaled: np.ndarray, analysis: str) -> pd.DataFrame:
    """计算不同 K 的聚类评估指标。"""
    rows = []
    n = x_scaled.shape[0]
    for k in range(K_MIN, K_MAX + 1):
        if k >= n:
            continue
        model = KMeans(n_clusters=k, random_state=RANDOM_SEED, n_init=50)
        labels = model.fit_predict(x_scaled)
        counts = np.bincount(labels)
        rows.append(
            {
                "cohort_flag": COHORT_FLAG,
                "analysis": analysis,
                "k": k,
                "inertia": float(model.inertia_),
                "silhouette": float(silhouette_score(x_scaled, labels)),
                "calinski_harabasz": float(calinski_harabasz_score(x_scaled, labels)),
                "davies_bouldin": float(davies_bouldin_score(x_scaled, labels)),
                "min_cluster_n": int(counts.min()),
                "min_cluster_frac": float(counts.min() / n),
                "max_cluster_n": int(counts.max()),
            }
        )
    metrics = pd.DataFrame(rows)
    display(metrics)
    return metrics


def fit_final_kmeans(x_scaled: np.ndarray, k: int):
    """拟合最终 K-means 模型。"""
    model = KMeans(n_clusters=k, random_state=RANDOM_SEED, n_init=100)
    raw_labels = model.fit_predict(x_scaled)
    return model, raw_labels


def build_ordered_phenotype_labels(
    x_scaled: np.ndarray,
    raw_labels: np.ndarray,
    features: list[str] | None = None,
    severity_directions: dict[str, int] | None = None,
) -> tuple[pd.DataFrame, dict[int, int]]:
    """根据生理严重程度给原始 cluster 排序，生成 phenotype 1..K。"""
    features = features or FEATURES
    severity_directions = severity_directions or SEVERITY_DIRECTIONS
    raw_clusters = sorted(np.unique(raw_labels))
    centers = pd.DataFrame(
        [x_scaled[raw_labels == label].mean(axis=0) for label in raw_clusters],
        columns=features,
    )
    centers.insert(0, "raw_cluster", raw_clusters)

    severity_score = np.zeros(len(centers))
    for feature, direction in severity_directions.items():
        if feature in centers:
            severity_score += direction * centers[feature].to_numpy()
    centers["severity_score"] = severity_score

    ordered_raw = centers.sort_values("severity_score")["raw_cluster"].tolist()
    label_map = {int(raw): int(rank + 1) for rank, raw in enumerate(ordered_raw)}
    centers["phenotype"] = centers["raw_cluster"].map(label_map)
    centers = centers.sort_values("phenotype")
    centers.insert(0, "cohort_flag", COHORT_FLAG)
    return centers, label_map


# =============================================================================
# 3. 汇总、检验和图表
# =============================================================================


def build_assignments(df: pd.DataFrame, raw_labels: np.ndarray, label_map: dict[int, int]) -> pd.DataFrame:
    """生成每个 stay 的 phenotype assignment。"""
    out = df.copy()
    out["raw_cluster"] = raw_labels
    out["phenotype"] = out["raw_cluster"].map(label_map)
    out["phenotype_label"] = out["phenotype"].map(lambda x: f"Phenotype {int(x)}")
    out.insert(0, "cohort_flag", COHORT_FLAG)
    return out


def build_feature_summary(assignments: pd.DataFrame) -> pd.DataFrame:
    """按 phenotype 汇总原始特征分布。"""
    rows = []
    for phenotype, group in assignments.groupby("phenotype"):
        row = {
            "cohort_flag": COHORT_FLAG,
            "phenotype": int(phenotype),
            "n": int(len(group)),
        }
        for feature in FEATURES:
            row[f"{feature}_median"] = float(group[feature].median())
            row[f"{feature}_q1"] = float(group[feature].quantile(0.25))
            row[f"{feature}_q3"] = float(group[feature].quantile(0.75))
            row[f"{feature}_mean"] = float(group[feature].mean())
        rows.append(row)
    return pd.DataFrame(rows).sort_values("phenotype")


def build_outcome_summary(assignments: pd.DataFrame) -> pd.DataFrame:
    """按 phenotype 汇总结局和贫血比例。"""
    rows = []
    for phenotype, group in assignments.groupby("phenotype"):
        rows.append(
            {
                "cohort_flag": COHORT_FLAG,
                "phenotype": int(phenotype),
                "n": int(len(group)),
                "hospital_deaths": int((group["hospital_mortality"] == 1).sum()),
                "hospital_mortality_rate": float(group["hospital_mortality"].mean()),
                "icu_deaths": int((group["icu_mortality"] == 1).sum()) if "icu_mortality" in group else None,
                "icu_mortality_rate": float(group["icu_mortality"].mean()) if "icu_mortality" in group else None,
                "early_anemia_n": int((group["early_anemia_all"] == 1).sum()),
                "early_anemia_rate": float(group["early_anemia_all"].mean()),
                "age_median": float(group["age"].median()),
                "icu_los_days_median": float(group["icu_los_days"].median()),
                "hospital_los_days_median": float(group["hospital_los_days"].median()),
                "any_rbc_transfusion_48h_rate": float(group["any_rbc_transfusion_48h"].mean()),
            }
        )
    return pd.DataFrame(rows).sort_values("phenotype")


def build_anemia_feasibility(assignments: pd.DataFrame) -> pd.DataFrame:
    """生成 phenotype x anemia 的事件数，用于判断分层回归是否稳定。"""
    rows = []
    for phenotype, group in assignments.groupby("phenotype"):
        for anemia_value in [0, 1]:
            sub = group[group["early_anemia_all"] == anemia_value]
            rows.append(
                {
                    "cohort_flag": COHORT_FLAG,
                    "phenotype": int(phenotype),
                    "early_anemia_all": int(anemia_value),
                    "n": int(len(sub)),
                    "deaths": int((sub["hospital_mortality"] == 1).sum()),
                    "mortality_rate": float(sub["hospital_mortality"].mean()) if len(sub) else np.nan,
                }
            )
    return pd.DataFrame(rows).sort_values(["phenotype", "early_anemia_all"])


def build_gcs_motor_distribution(assignments: pd.DataFrame) -> pd.DataFrame:
    """Summarize GCS motor distributions beyond medians for reviewer-facing diagnostics."""
    rows = []
    solution_label = (
        str(assignments["phenotype_solution"].dropna().iloc[0])
        if "phenotype_solution" in assignments.columns and assignments["phenotype_solution"].notna().any()
        else "primary_log_pca_kmeans_k3"
    )
    with_values = assignments.copy()
    with_values["gcs_motor_value"] = pd.to_numeric(with_values["gcs_motor_min_48h"], errors="coerce")
    for phenotype, group in with_values.groupby("phenotype"):
        total = int(len(group))
        group_values = pd.to_numeric(group["gcs_motor_value"], errors="coerce")
        nonmissing = group_values.dropna()
        for motor_score in range(1, 7):
            count = int((group_values == motor_score).sum())
            rows.append(
                {
                    "cohort_flag": COHORT_FLAG,
                    "phenotype_solution": solution_label,
                    "phenotype": int(phenotype),
                    "phenotype_n": total,
                    "gcs_motor_min_48h": int(motor_score),
                    "n": count,
                    "pct_within_phenotype": float(count / total) if total else np.nan,
                    "n_nonmissing": int(nonmissing.shape[0]),
                    "missing_n": int(group_values.isna().sum()),
                    "median": float(nonmissing.median()) if len(nonmissing) else np.nan,
                    "q1": float(nonmissing.quantile(0.25)) if len(nonmissing) else np.nan,
                    "q3": float(nonmissing.quantile(0.75)) if len(nonmissing) else np.nan,
                    "note": (
                        "Use this table to interpret GCS motor beyond median/IQR; P2 and P3 can share "
                        "a median of 1 while differing in full distribution and non-neurologic physiology."
                    ),
                }
            )
    return pd.DataFrame(rows).sort_values(["phenotype", "gcs_motor_min_48h"])


def run_lightweight_tests(assignments: pd.DataFrame) -> pd.DataFrame:
    """运行不依赖 statsmodels 的基础统计检验。"""
    rows = []

    contingency = pd.crosstab(assignments["phenotype"], assignments["hospital_mortality"])
    if contingency.shape[0] > 1 and contingency.shape[1] > 1:
        chi2, p_value, _, _ = stats.chi2_contingency(contingency)
        rows.append(
            {
                "cohort_flag": COHORT_FLAG,
                "test": "chi_square_phenotype_vs_hospital_mortality",
                "statistic": float(chi2),
                "p_value": float(p_value),
            }
        )

    anemia_contingency = pd.crosstab(
        [assignments["phenotype"], assignments["early_anemia_all"]],
        assignments["hospital_mortality"],
    )
    if anemia_contingency.shape[0] > 1 and anemia_contingency.shape[1] > 1:
        chi2, p_value, _, _ = stats.chi2_contingency(anemia_contingency)
        rows.append(
            {
                "cohort_flag": COHORT_FLAG,
                "test": "chi_square_phenotype_anemia_cells_vs_hospital_mortality",
                "statistic": float(chi2),
                "p_value": float(p_value),
            }
        )

    for feature in FEATURES:
        groups = [
            group[feature].dropna()
            for _, group in assignments.groupby("phenotype")
        ]
        if len(groups) > 1 and all(len(group) > 0 for group in groups):
            stat, p_value = stats.kruskal(*groups)
            rows.append(
                {
                    "cohort_flag": COHORT_FLAG,
                    "test": f"kruskal_{feature}_by_phenotype",
                    "statistic": float(stat),
                    "p_value": float(p_value),
                }
            )

    return pd.DataFrame(rows)


def run_stability_check(x_scaled: np.ndarray, raw_labels: np.ndarray, k: int) -> pd.DataFrame:
    """用层次聚类与 K-means 对比 adjusted Rand index。"""
    hierarchical = AgglomerativeClustering(n_clusters=k)
    h_labels = hierarchical.fit_predict(x_scaled)
    ari = adjusted_rand_score(raw_labels, h_labels)
    return pd.DataFrame(
        [
            {
                "cohort_flag": COHORT_FLAG,
                "k": int(k),
                "comparison": "kmeans_vs_hierarchical",
                "adjusted_rand_index": float(ari),
            }
        ]
    )


def run_bootstrap_stability(x_scaled: np.ndarray, reference_phenotype: pd.Series, k: int) -> pd.DataFrame:
    """Bootstrap 重采样评估 K-means phenotype assignment 稳定性。"""
    rng = np.random.default_rng(RANDOM_SEED)
    reference = reference_phenotype.astype(int).to_numpy()
    rows = []
    n = x_scaled.shape[0]

    for iteration in range(1, BOOTSTRAP_N + 1):
        sample_idx = rng.integers(0, n, size=n)
        model = KMeans(n_clusters=k, random_state=RANDOM_SEED + iteration, n_init=50)
        model.fit(x_scaled[sample_idx])
        raw_labels = model.predict(x_scaled)
        _, label_map = build_ordered_phenotype_labels(x_scaled, raw_labels)
        ordered_labels = np.array([label_map[int(label)] for label in raw_labels])
        rows.append(
            {
                "cohort_flag": COHORT_FLAG,
                "k": int(k),
                "iteration": int(iteration),
                "adjusted_rand_index_vs_primary": float(adjusted_rand_score(reference, ordered_labels)),
                "same_ordered_label_rate": float(np.mean(reference == ordered_labels)),
                "min_cluster_n": int(pd.Series(ordered_labels).value_counts().min()),
            }
        )

    return pd.DataFrame(rows)


def run_log_pca_bootstrap_stability(
    pc_scores: np.ndarray,
    x_scaled: np.ndarray,
    reference_phenotype: pd.Series,
    k: int,
) -> pd.DataFrame:
    """Bootstrap 评估 log1p + PCA K-means phenotype assignment 稳定性。"""
    rng = np.random.default_rng(RANDOM_SEED)
    reference = reference_phenotype.astype(int).to_numpy()
    rows = []
    n = pc_scores.shape[0]

    for iteration in range(1, BOOTSTRAP_N + 1):
        sample_idx = rng.integers(0, n, size=n)
        model = KMeans(n_clusters=k, random_state=RANDOM_SEED + iteration, n_init=50)
        model.fit(pc_scores[sample_idx])
        raw_labels = model.predict(pc_scores)
        _, label_map = build_ordered_phenotype_labels(x_scaled, raw_labels, features=FEATURES)
        ordered_labels = np.array([label_map[int(label)] for label in raw_labels])
        rows.append(
            {
                "cohort_flag": COHORT_FLAG,
                "analysis": "log1p_creatinine_inr_pca_kmeans_k3",
                "k": int(k),
                "iteration": int(iteration),
                "adjusted_rand_index_vs_primary": float(adjusted_rand_score(reference, ordered_labels)),
                "adjusted_rand_index_vs_log_pca": float(adjusted_rand_score(reference, ordered_labels)),
                "same_ordered_label_rate": float(np.mean(reference == ordered_labels)),
                "min_cluster_n": int(pd.Series(ordered_labels).value_counts().min()),
            }
        )

    return pd.DataFrame(rows)


def run_hb_free_sensitivity(df: pd.DataFrame, primary_assignments: pd.DataFrame):
    """去除 Hb 后重新聚类，检验贫血结局解释是否完全由 Hb 输入驱动。"""
    _x_raw, _x_imputed, x_scaled_hb_free, _imputer, _scaler, missing_summary = preprocess_feature_matrix(
        df,
        HB_FREE_FEATURES,
    )
    model = KMeans(n_clusters=PRIMARY_K, random_state=RANDOM_SEED, n_init=100)
    raw_labels = model.fit_predict(x_scaled_hb_free)
    centers, label_map = build_ordered_phenotype_labels(x_scaled_hb_free, raw_labels, features=HB_FREE_FEATURES)
    assignments = build_assignments(df, raw_labels, label_map)
    assignments["phenotype_solution"] = "hb_free_kmeans_k3"
    centers["phenotype_solution"] = "hb_free_kmeans_k3"

    phenotype = assignments["phenotype"].astype(int).to_numpy()
    reference = primary_assignments["phenotype"].astype(int).to_numpy()
    counts = assignments["phenotype"].value_counts()
    global_metrics = {
        "cohort_flag": COHORT_FLAG,
        "analysis": "hb_free_kmeans_k3",
        "features": ",".join(HB_FREE_FEATURES),
        "k": int(PRIMARY_K),
        "n": int(len(assignments)),
        "silhouette": float(silhouette_score(x_scaled_hb_free, phenotype)),
        "ari_vs_primary_log_pca": float(adjusted_rand_score(reference, phenotype)),
        "min_cluster_n": int(counts.min()),
        "min_cluster_frac": float(counts.min() / len(assignments)),
        "max_feature_missing_rate": float(missing_summary["missing_rate"].max()),
    }

    rows = []
    for phenotype_id, group in assignments.groupby("phenotype"):
        row = {
            **global_metrics,
            "phenotype": int(phenotype_id),
            "phenotype_n": int(len(group)),
            "hospital_deaths": int((group["hospital_mortality"] == 1).sum()),
            "hospital_mortality_rate": float(group["hospital_mortality"].mean()),
            "early_anemia_rate": float(group["early_anemia_all"].mean()),
            "hb_min_48h_all_median": float(group["hb_min_48h_all"].median()),
            "hb_min_48h_all_q1": float(group["hb_min_48h_all"].quantile(0.25)),
            "hb_min_48h_all_q3": float(group["hb_min_48h_all"].quantile(0.75)),
            "note": "Hb excluded from clustering input; anemia/Hb are reported only as downstream phenotype descriptors.",
        }
        for feature in HB_FREE_FEATURES:
            row[f"{feature}_median"] = float(group[feature].median())
            row[f"{feature}_q1"] = float(group[feature].quantile(0.25))
            row[f"{feature}_q3"] = float(group[feature].quantile(0.75))
        rows.append(row)

    summary = pd.DataFrame(rows).sort_values("phenotype")
    return {"summary": summary, "centers": centers, "assignments": assignments}


def run_hb_free_anemia_regression(assignments: pd.DataFrame) -> pd.DataFrame:
    """Re-test anemia after replacing primary phenotype with an Hb-free phenotype."""
    try:
        import statsmodels.formula.api as smf
    except ImportError:
        return pd.DataFrame(
            [
                {
                    "cohort_flag": COHORT_FLAG,
                    "model": "hb_free_phenotype_anemia_adjusted",
                    "term": "statsmodels_unavailable",
                    "formula": "",
                    "odds_ratio": np.nan,
                    "ci_lower": np.nan,
                    "ci_upper": np.nan,
                    "p_value": np.nan,
                    "n": int(len(assignments)),
                    "events": int((assignments["hospital_mortality"] == 1).sum()),
                    "aic": np.nan,
                    "bic": np.nan,
                    "pseudo_r2": np.nan,
                    "note": "statsmodels is required for Hb-free phenotype anemia regression output.",
                }
            ]
        )

    required_columns = [
        "hospital_mortality",
        "phenotype",
        "early_anemia_all",
        "age",
        "gender",
        "admission_type",
        "nsah_evidence_level",
        "has_aneurysm_dx",
        "has_aneurysm_procedure",
    ]
    available_columns = [col for col in required_columns if col in assignments.columns]
    model_df = prepare_logit_dataframe(
        assignments[available_columns],
        numeric_columns=[
            col
            for col in [
                "hospital_mortality",
                "phenotype",
                "early_anemia_all",
                "age",
                "nsah_evidence_level",
                "has_aneurysm_dx",
                "has_aneurysm_procedure",
            ]
            if col in available_columns
        ],
        categorical_columns=[col for col in ["gender", "admission_type"] if col in available_columns],
        required_columns=[
            col
            for col in ["hospital_mortality", "phenotype", "early_anemia_all", "age", "gender", "admission_type"]
            if col in available_columns
        ],
    )
    model_df["admission_type_group"] = model_df["admission_type"].map(collapse_admission_type)

    formulas = build_adjusted_regression_formulas(model_df)
    formula_note = formulas.pop("_note")
    rows = []
    for model_name, formula in formulas.items():
        sensitivity_model_name = f"hb_free_phenotype_{model_name}"
        try:
            fitted = fit_logit_quiet(smf, formula, model_df)
            conf = fitted.conf_int()
            for term, coef in fitted.params.items():
                rows.append(
                    {
                        "cohort_flag": COHORT_FLAG,
                        "model": sensitivity_model_name,
                        "term": term,
                        "formula": formula,
                        "odds_ratio": float(np.exp(coef)),
                        "ci_lower": float(np.exp(conf.loc[term, 0])),
                        "ci_upper": float(np.exp(conf.loc[term, 1])),
                        "p_value": float(fitted.pvalues[term]),
                        "n": int(fitted.nobs),
                        "events": int(model_df["hospital_mortality"].sum()),
                        "aic": float(fitted.aic),
                        "bic": float(fitted.bic),
                        "pseudo_r2": float(fitted.prsquared),
                        "note": (
                            "Sensitivity model adjusts anemia for Hb-free phenotype to avoid overadjusting "
                            "for a phenotype that already contains Hb; "
                            + formula_note
                        ),
                    }
                )
        except Exception as exc:
            rows.append(
                {
                    "cohort_flag": COHORT_FLAG,
                    "model": sensitivity_model_name,
                    "term": "model_failed",
                    "formula": formula,
                    "odds_ratio": np.nan,
                    "ci_lower": np.nan,
                    "ci_upper": np.nan,
                    "p_value": np.nan,
                    "n": int(len(model_df)),
                    "events": int(model_df["hospital_mortality"].sum()),
                    "aic": np.nan,
                    "bic": np.nan,
                    "pseudo_r2": np.nan,
                    "note": str(exc),
                }
            )

    return pd.DataFrame(rows)


def run_inr_free_sensitivity(df: pd.DataFrame, primary_assignments: pd.DataFrame):
    """去除 INR 后重新聚类，检验凝血维度是否改善或削弱表型。"""
    _x_raw, _x_imputed, x_scaled_inr_free, _imputer, _scaler, missing_summary = preprocess_feature_matrix(
        df,
        INR_FREE_FEATURES,
    )
    model = KMeans(n_clusters=PRIMARY_K, random_state=RANDOM_SEED, n_init=100)
    raw_labels = model.fit_predict(x_scaled_inr_free)
    centers, label_map = build_ordered_phenotype_labels(x_scaled_inr_free, raw_labels, features=INR_FREE_FEATURES)
    assignments = build_assignments(df, raw_labels, label_map)
    assignments["phenotype_solution"] = "inr_free_kmeans_k3"
    centers["phenotype_solution"] = "inr_free_kmeans_k3"

    phenotype = assignments["phenotype"].astype(int).to_numpy()
    reference = primary_assignments["phenotype"].astype(int).to_numpy()
    counts = assignments["phenotype"].value_counts()
    global_metrics = {
        "cohort_flag": COHORT_FLAG,
        "analysis": "inr_free_kmeans_k3",
        "features": ",".join(INR_FREE_FEATURES),
        "k": int(PRIMARY_K),
        "n": int(len(assignments)),
        "silhouette": float(silhouette_score(x_scaled_inr_free, phenotype)),
        "ari_vs_primary_log_pca": float(adjusted_rand_score(reference, phenotype)),
        "min_cluster_n": int(counts.min()),
        "min_cluster_frac": float(counts.min() / len(assignments)),
        "max_feature_missing_rate": float(missing_summary["missing_rate"].max()),
    }

    rows = []
    for phenotype_id, group in assignments.groupby("phenotype"):
        row = {
            **global_metrics,
            "phenotype": int(phenotype_id),
            "phenotype_n": int(len(group)),
            "hospital_deaths": int((group["hospital_mortality"] == 1).sum()),
            "hospital_mortality_rate": float(group["hospital_mortality"].mean()),
            "early_anemia_rate": float(group["early_anemia_all"].mean()),
            "inr_max_48h_median": float(group["inr_max_48h"].median()),
            "inr_max_48h_q1": float(group["inr_max_48h"].quantile(0.25)),
            "inr_max_48h_q3": float(group["inr_max_48h"].quantile(0.75)),
            "note": "INR excluded from clustering input; INR is reported only as a downstream phenotype descriptor.",
        }
        for feature in INR_FREE_FEATURES:
            row[f"{feature}_median"] = float(group[feature].median())
            row[f"{feature}_q1"] = float(group[feature].quantile(0.25))
            row[f"{feature}_q3"] = float(group[feature].quantile(0.75))
        rows.append(row)

    summary = pd.DataFrame(rows).sort_values("phenotype")
    return {"summary": summary, "centers": centers, "assignments": assignments}


def run_complete_case_sensitivity(df: pd.DataFrame, primary_assignments: pd.DataFrame):
    """仅保留 8 个核心变量均非缺失的样本，检验中位数填补是否驱动聚类。"""
    x_raw = df[FEATURES].apply(pd.to_numeric, errors="coerce")
    complete_mask = x_raw.notna().all(axis=1)
    df_complete = df.loc[complete_mask].copy()
    if df_complete.empty:
        raise ValueError("Complete-case sensitivity cohort is empty.")

    x_complete = df_complete[FEATURES].apply(pd.to_numeric, errors="coerce")
    scaler = StandardScaler()
    x_scaled_complete = scaler.fit_transform(x_complete)
    model = KMeans(n_clusters=PRIMARY_K, random_state=RANDOM_SEED, n_init=100)
    raw_labels = model.fit_predict(x_scaled_complete)
    centers, label_map = build_ordered_phenotype_labels(x_scaled_complete, raw_labels, features=FEATURES)
    assignments = build_assignments(df_complete, raw_labels, label_map)
    assignments["phenotype_solution"] = "complete_case_kmeans_k3"
    centers["phenotype_solution"] = "complete_case_kmeans_k3"

    reference = (
        primary_assignments.set_index("stay_id")
        .loc[assignments["stay_id"], "phenotype"]
        .astype(int)
        .to_numpy()
    )
    phenotype = assignments["phenotype"].astype(int).to_numpy()
    counts = assignments["phenotype"].value_counts()
    global_metrics = {
        "cohort_flag": COHORT_FLAG,
        "analysis": "complete_case_kmeans_k3",
        "features": ",".join(FEATURES),
        "k": int(PRIMARY_K),
        "n": int(len(assignments)),
        "excluded_missing_n": int((~complete_mask).sum()),
        "excluded_missing_frac": float((~complete_mask).mean()),
        "silhouette": float(silhouette_score(x_scaled_complete, phenotype)),
        "ari_vs_primary_subset": float(adjusted_rand_score(reference, phenotype)),
        "same_ordered_label_rate_vs_primary_subset": float(np.mean(reference == phenotype)),
        "min_cluster_n": int(counts.min()),
        "min_cluster_frac": float(counts.min() / len(assignments)),
    }

    rows = []
    for phenotype_id, group in assignments.groupby("phenotype"):
        row = {
            **global_metrics,
            "phenotype": int(phenotype_id),
            "phenotype_n": int(len(group)),
            "hospital_deaths": int((group["hospital_mortality"] == 1).sum()),
            "hospital_mortality_rate": float(group["hospital_mortality"].mean()),
            "early_anemia_rate": float(group["early_anemia_all"].mean()),
            "note": "Complete-case sensitivity excludes stays with any missing core clustering feature; no median imputation is used.",
        }
        for feature in FEATURES:
            row[f"{feature}_median"] = float(group[feature].median())
            row[f"{feature}_q1"] = float(group[feature].quantile(0.25))
            row[f"{feature}_q3"] = float(group[feature].quantile(0.75))
        rows.append(row)

    summary = pd.DataFrame(rows).sort_values("phenotype")
    return {"summary": summary, "centers": centers, "assignments": assignments}


def run_log_pca_complete_case_sensitivity(df: pd.DataFrame, primary_assignments: pd.DataFrame):
    """仅保留核心 48h 变量 complete cases，并复用主 log-PCA K-means 流程。"""
    x_raw = df[FEATURES].apply(pd.to_numeric, errors="coerce")
    complete_mask = x_raw.notna().all(axis=1)
    df_complete = df.loc[complete_mask].copy()
    if df_complete.empty:
        raise ValueError("Log-PCA complete-case sensitivity cohort is empty.")

    (
        _x_raw,
        _x_transformed,
        x_scaled,
        pc_scores,
        pc_columns,
        pca,
        _imputer,
        _scaler,
        missing_summary,
    ) = preprocess_log_pca_feature_matrix(df_complete)

    model = KMeans(n_clusters=PRIMARY_K, random_state=RANDOM_SEED, n_init=100)
    raw_labels = model.fit_predict(pc_scores)
    centers, label_map = build_ordered_phenotype_labels(x_scaled, raw_labels, features=FEATURES)
    assignments = build_assignments(df_complete, raw_labels, label_map)
    assignments["phenotype_solution"] = "log_pca_complete_case_kmeans_k3"
    centers["phenotype_solution"] = "log_pca_complete_case_kmeans_k3"

    reference = (
        primary_assignments.set_index("stay_id")
        .loc[assignments["stay_id"], "phenotype"]
        .astype(int)
        .to_numpy()
    )
    phenotype = assignments["phenotype"].astype(int).to_numpy()
    counts = assignments["phenotype"].value_counts()
    explained = pca.explained_variance_ratio_
    global_metrics = {
        "cohort_flag": COHORT_FLAG,
        "analysis": "log_pca_complete_case_kmeans_k3",
        "features": ",".join(FEATURES),
        "k": int(PRIMARY_K),
        "n": int(len(assignments)),
        "excluded_missing_n": int((~complete_mask).sum()),
        "excluded_missing_frac": float((~complete_mask).mean()),
        "silhouette_pc_space": float(silhouette_score(pc_scores, phenotype)),
        "ari_vs_primary_log_pca_subset": float(adjusted_rand_score(reference, phenotype)),
        "same_ordered_label_rate_vs_primary_subset": float(np.mean(reference == phenotype)),
        "min_cluster_n": int(counts.min()),
        "min_cluster_frac": float(counts.min() / len(assignments)),
        "pca_n_components": int(len(pc_columns)),
        "pca_explained_variance_total": float(explained.sum()),
        "max_feature_missing_rate_before_exclusion": float(missing_summary["missing_rate"].max()),
        "note": "Complete-case sensitivity uses the same log1p(creatinine/INR), Z-score, PCA and K-means pipeline as the primary analysis, without median imputation.",
    }

    rows = []
    for phenotype_id, group in assignments.groupby("phenotype"):
        row = {
            **global_metrics,
            "phenotype": int(phenotype_id),
            "phenotype_n": int(len(group)),
            "hospital_deaths": int((group["hospital_mortality"] == 1).sum()),
            "hospital_mortality_rate": float(group["hospital_mortality"].mean()),
            "early_anemia_rate": float(group["early_anemia_all"].mean()),
        }
        for i, ratio in enumerate(explained, start=1):
            row[f"pc{i}_explained_variance"] = float(ratio)
        for feature in FEATURES:
            row[f"{feature}_median"] = float(group[feature].median())
            row[f"{feature}_q1"] = float(group[feature].quantile(0.25))
            row[f"{feature}_q3"] = float(group[feature].quantile(0.75))
        rows.append(row)

    summary = pd.DataFrame(rows).sort_values("phenotype")
    return {"summary": summary, "centers": centers, "assignments": assignments}


def run_24h_window_sensitivity(df: pd.DataFrame, primary_assignments: pd.DataFrame):
    """使用 0-24h 同源核心变量复用主 log-PCA K-means 流程。"""
    missing_columns = [feature for feature in FEATURES_24H if feature not in df.columns]
    if missing_columns:
        raise ValueError(f"24h window sensitivity missing fields: {missing_columns}")

    (
        _x_raw,
        _x_transformed,
        x_scaled,
        pc_scores,
        pc_columns,
        pca,
        _imputer,
        _scaler,
        missing_summary,
    ) = preprocess_log_pca_feature_matrix(
        df,
        features=FEATURES_24H,
        log_transform_features=LOG_TRANSFORM_FEATURES_24H,
    )

    model = KMeans(n_clusters=PRIMARY_K, random_state=RANDOM_SEED, n_init=100)
    raw_labels = model.fit_predict(pc_scores)
    centers, label_map = build_ordered_phenotype_labels(x_scaled, raw_labels, features=FEATURES_24H)
    assignments = build_assignments(df, raw_labels, label_map)
    assignments["phenotype_solution"] = "log_pca_24h_window_kmeans_k3"
    centers["phenotype_solution"] = "log_pca_24h_window_kmeans_k3"

    reference = primary_assignments["phenotype"].astype(int).to_numpy()
    phenotype = assignments["phenotype"].astype(int).to_numpy()
    counts = assignments["phenotype"].value_counts()
    explained = pca.explained_variance_ratio_
    global_metrics = {
        "cohort_flag": COHORT_FLAG,
        "analysis": "log_pca_24h_window_kmeans_k3",
        "features": ",".join(FEATURES_24H),
        "k": int(PRIMARY_K),
        "n": int(len(assignments)),
        "silhouette_pc_space": float(silhouette_score(pc_scores, phenotype)),
        "ari_vs_primary_log_pca": float(adjusted_rand_score(reference, phenotype)),
        "same_ordered_label_rate_vs_primary": float(np.mean(reference == phenotype)),
        "min_cluster_n": int(counts.min()),
        "min_cluster_frac": float(counts.min() / len(assignments)),
        "pca_n_components": int(len(pc_columns)),
        "pca_explained_variance_total": float(explained.sum()),
        "max_feature_missing_rate": float(missing_summary["missing_rate"].max()),
        "note": "0-24h window sensitivity uses the same core physiology domains and primary log-PCA K-means pipeline, with median imputation as in the primary analysis.",
    }

    rows = []
    for phenotype_id, group in assignments.groupby("phenotype"):
        row = {
            **global_metrics,
            "phenotype": int(phenotype_id),
            "phenotype_n": int(len(group)),
            "hospital_deaths": int((group["hospital_mortality"] == 1).sum()),
            "hospital_mortality_rate": float(group["hospital_mortality"].mean()),
            "early_anemia_rate": float(group["early_anemia_all"].mean()),
            "core_feature_missing_count_24h_median": float(group["core_feature_missing_count_24h"].median())
            if "core_feature_missing_count_24h" in group
            else np.nan,
        }
        for i, ratio in enumerate(explained, start=1):
            row[f"pc{i}_explained_variance"] = float(ratio)
        for feature in FEATURES_24H:
            row[f"{feature}_median"] = float(group[feature].median())
            row[f"{feature}_q1"] = float(group[feature].quantile(0.25))
            row[f"{feature}_q3"] = float(group[feature].quantile(0.75))
        rows.append(row)

    summary = pd.DataFrame(rows).sort_values("phenotype")
    return {"summary": summary, "centers": centers, "assignments": assignments, "missing_summary": missing_summary}


def run_gcs_sensitivity(df: pd.DataFrame, reference_assignments: pd.DataFrame) -> pd.DataFrame:
    """比较 GCS motor 主方案、加入 total GCS、total only 和 grade 替代方案。"""
    reference = reference_assignments["phenotype"].astype(int).to_numpy()
    rows = []

    for feature_set_name, features in GCS_SENSITIVITY_FEATURE_SETS.items():
        _, _, x_scaled_sens, _, _, missing_summary = preprocess_feature_matrix(df, features)
        model = KMeans(n_clusters=PRIMARY_K, random_state=RANDOM_SEED, n_init=100)
        raw_labels = model.fit_predict(x_scaled_sens)
        _, label_map = build_ordered_phenotype_labels(x_scaled_sens, raw_labels, features=features)
        phenotype = np.array([label_map[int(label)] for label in raw_labels])
        counts = pd.Series(phenotype).value_counts()

        global_metrics = {
            "cohort_flag": COHORT_FLAG,
            "feature_set": feature_set_name,
            "features": ",".join(features),
            "k": int(PRIMARY_K),
            "n": int(len(df)),
            "silhouette": float(silhouette_score(x_scaled_sens, phenotype)),
            "ari_vs_primary_log_pca": float(adjusted_rand_score(reference, phenotype)),
            "min_cluster_n": int(counts.min()),
            "min_cluster_frac": float(counts.min() / len(df)),
            "max_feature_missing_rate": float(missing_summary["missing_rate"].max()),
        }

        for pheno in sorted(np.unique(phenotype)):
            mask = phenotype == pheno
            rows.append(
                {
                    **global_metrics,
                    "phenotype": int(pheno),
                    "phenotype_n": int(mask.sum()),
                    "hospital_deaths": int((df.loc[mask, "hospital_mortality"] == 1).sum()),
                    "hospital_mortality_rate": float(df.loc[mask, "hospital_mortality"].mean()),
                    "early_anemia_rate": float(df.loc[mask, "early_anemia_all"].mean()),
                }
            )

    return pd.DataFrame(rows).sort_values(["feature_set", "phenotype"])


def build_candidate_feature_audit(df: pd.DataFrame) -> pd.DataFrame:
    """审计 ePVS、troponin 和血气候选变量的覆盖率与分布。"""
    rows = []
    available_features = [feature for feature in CANDIDATE_AUDIT_FEATURES if feature in df.columns]
    for feature in available_features:
        values = pd.to_numeric(df[feature], errors="coerce")
        non_missing = values.dropna()
        rows.append(
            {
                "cohort_flag": COHORT_FLAG,
                "feature": feature,
                "total_n": int(len(df)),
                "missing_n": int(values.isna().sum()),
                "non_missing_n": int(non_missing.shape[0]),
                "missing_rate": float(values.isna().mean()),
                "mean": float(non_missing.mean()) if len(non_missing) else np.nan,
                "median": float(non_missing.median()) if len(non_missing) else np.nan,
                "q1": float(non_missing.quantile(0.25)) if len(non_missing) else np.nan,
                "q3": float(non_missing.quantile(0.75)) if len(non_missing) else np.nan,
                "min": float(non_missing.min()) if len(non_missing) else np.nan,
                "max": float(non_missing.max()) if len(non_missing) else np.nan,
            }
        )
    return pd.DataFrame(rows).sort_values("missing_rate", ascending=False)


def build_external_severity_validation(assignments: pd.DataFrame) -> pd.DataFrame:
    """用既有 ICU 严重程度评分验证 phenotype 梯度，不把评分纳入聚类输入。"""
    severity_scores = [
        ("sofa_24h", "SOFA"),
        ("sapsii_24h", "SAPS II"),
        ("oasis_24h", "OASIS"),
        ("lods_24h", "LODS"),
    ]
    rows = []
    solution_label = (
        str(assignments["phenotype_solution"].dropna().iloc[0])
        if "phenotype_solution" in assignments.columns and assignments["phenotype_solution"].notna().any()
        else "primary_log_pca_kmeans_k3"
    )
    for feature, label in severity_scores:
        if feature not in assignments.columns:
            continue
        values = pd.to_numeric(assignments[feature], errors="coerce")
        groups = [
            pd.to_numeric(group[feature], errors="coerce").dropna()
            for _, group in assignments.groupby("phenotype")
        ]
        valid_groups = [group for group in groups if len(group) > 0]
        if len(valid_groups) > 1:
            kruskal_stat, kruskal_p = stats.kruskal(*valid_groups)
        else:
            kruskal_stat, kruskal_p = np.nan, np.nan
        valid = assignments[["phenotype"]].copy()
        valid[feature] = values
        valid = valid.dropna()
        if valid["phenotype"].nunique() > 1 and valid[feature].nunique() > 1:
            rho, spearman_p = stats.spearmanr(valid["phenotype"], valid[feature])
        else:
            rho, spearman_p = np.nan, np.nan

        for phenotype_id, group in assignments.groupby("phenotype"):
            group_values = pd.to_numeric(group[feature], errors="coerce")
            non_missing = group_values.dropna()
            rows.append(
                {
                    "cohort_flag": COHORT_FLAG,
                    "phenotype_solution": solution_label,
                    "validation_score": label,
                    "variable": feature,
                    "phenotype": int(phenotype_id),
                    "phenotype_n": int(len(group)),
                    "n_nonmissing": int(non_missing.shape[0]),
                    "missing_n": int(group_values.isna().sum()),
                    "missing_rate": float(group_values.isna().mean()),
                    "median": float(non_missing.median()) if len(non_missing) else np.nan,
                    "q1": float(non_missing.quantile(0.25)) if len(non_missing) else np.nan,
                    "q3": float(non_missing.quantile(0.75)) if len(non_missing) else np.nan,
                    "mean": float(non_missing.mean()) if len(non_missing) else np.nan,
                    "kruskal_statistic": float(kruskal_stat) if pd.notna(kruskal_stat) else np.nan,
                    "kruskal_p_value": float(kruskal_p) if pd.notna(kruskal_p) else np.nan,
                    "spearman_rho_vs_ordered_phenotype": float(rho) if pd.notna(rho) else np.nan,
                    "spearman_p_value": float(spearman_p) if pd.notna(spearman_p) else np.nan,
                    "note": "External severity validation only; score was not used as a clustering input.",
                }
            )

    return pd.DataFrame(rows).sort_values(["variable", "phenotype"])


def format_p_value(p_value: float | None) -> str:
    """格式化 Table 1 p 值。"""
    if p_value is None or pd.isna(p_value):
        return ""
    if p_value < 0.001:
        return "<0.001"
    return f"{p_value:.3f}"


def continuous_p_value_by_phenotype(assignments: pd.DataFrame, feature: str) -> float:
    """连续变量 phenotype 间 Kruskal-Wallis p 值。"""
    groups = [
        pd.to_numeric(group[feature], errors="coerce").dropna()
        for _, group in assignments.groupby("phenotype")
        if feature in group
    ]
    groups = [group for group in groups if len(group) > 0]
    if len(groups) < 2:
        return np.nan
    try:
        _, p_value = stats.kruskal(*groups)
        return float(p_value)
    except Exception:
        return np.nan


def categorical_p_value_by_phenotype(assignments: pd.DataFrame, feature: str) -> float:
    """分类变量 phenotype 间卡方检验 p 值。"""
    if feature not in assignments:
        return np.nan
    table = pd.crosstab(assignments["phenotype"], assignments[feature].astype("object").fillna("Missing"))
    if table.shape[0] < 2 or table.shape[1] < 2:
        return np.nan
    try:
        _, p_value, _, _ = stats.chi2_contingency(table)
        return float(p_value)
    except Exception:
        return np.nan


def summarize_continuous(group: pd.DataFrame, feature: str) -> dict:
    """连续变量描述性统计。"""
    values = pd.to_numeric(group[feature], errors="coerce") if feature in group else pd.Series(dtype=float)
    non_missing = values.dropna()
    return {
        "n_nonmissing": int(non_missing.shape[0]),
        "missing_n": int(values.isna().sum()),
        "mean": float(non_missing.mean()) if len(non_missing) else np.nan,
        "sd": float(non_missing.std()) if len(non_missing) > 1 else np.nan,
        "median": float(non_missing.median()) if len(non_missing) else np.nan,
        "q1": float(non_missing.quantile(0.25)) if len(non_missing) else np.nan,
        "q3": float(non_missing.quantile(0.75)) if len(non_missing) else np.nan,
        "min": float(non_missing.min()) if len(non_missing) else np.nan,
        "max": float(non_missing.max()) if len(non_missing) else np.nan,
    }


def build_baseline_characteristics(assignments: pd.DataFrame) -> pd.DataFrame:
    """生成 Overall 和 K=3 phenotype 分层的基线特征表。"""
    rows = []
    solution_label = (
        str(assignments["phenotype_solution"].dropna().iloc[0])
        if "phenotype_solution" in assignments.columns and assignments["phenotype_solution"].notna().any()
        else "primary_log_pca_kmeans_k3"
    )
    groups = [("Overall", None, assignments)]
    groups.extend(
        [
            (f"Phenotype {int(phenotype)}", int(phenotype), group)
            for phenotype, group in assignments.groupby("phenotype")
        ]
    )

    for feature in [feature for feature in BASELINE_CONTINUOUS_FEATURES if feature in assignments.columns]:
        p_value = continuous_p_value_by_phenotype(assignments, feature)
        for group_label, phenotype, group in groups:
            summary = summarize_continuous(group, feature)
            rows.append(
                {
                    "cohort_flag": COHORT_FLAG,
                    "phenotype_solution": solution_label,
                    "group": group_label,
                    "phenotype": phenotype,
                    "variable": feature,
                    "variable_type": "continuous",
                    "level": "",
                    "n": int(len(group)),
                    "n_nonmissing": summary["n_nonmissing"],
                    "missing_n": summary["missing_n"],
                    "level_n": np.nan,
                    "level_pct": np.nan,
                    "mean": summary["mean"],
                    "sd": summary["sd"],
                    "median": summary["median"],
                    "q1": summary["q1"],
                    "q3": summary["q3"],
                    "min": summary["min"],
                    "max": summary["max"],
                    "summary": (
                        f"{summary['median']:.2f} [{summary['q1']:.2f}, {summary['q3']:.2f}]"
                        if summary["n_nonmissing"] else ""
                    ),
                    "p_value": p_value,
                    "p_value_formatted": format_p_value(p_value),
                }
            )

    for feature in [feature for feature in BASELINE_CATEGORICAL_FEATURES if feature in assignments.columns]:
        p_value = categorical_p_value_by_phenotype(assignments, feature)
        levels = (
            assignments[feature]
            .astype("object")
            .where(assignments[feature].notna(), "Missing")
            .value_counts(dropna=False)
            .index
            .tolist()
        )
        for group_label, phenotype, group in groups:
            values = group[feature].astype("object").where(group[feature].notna(), "Missing")
            denominator = int(len(group))
            missing_n = int((values == "Missing").sum())
            for level in levels:
                level_n = int((values == level).sum())
                level_pct = float(level_n / denominator) if denominator else np.nan
                rows.append(
                    {
                        "cohort_flag": COHORT_FLAG,
                        "phenotype_solution": solution_label,
                        "group": group_label,
                        "phenotype": phenotype,
                        "variable": feature,
                        "variable_type": "categorical",
                        "level": str(level),
                        "n": denominator,
                        "n_nonmissing": int(denominator - missing_n),
                        "missing_n": missing_n,
                        "level_n": level_n,
                        "level_pct": level_pct,
                        "mean": np.nan,
                        "sd": np.nan,
                        "median": np.nan,
                        "q1": np.nan,
                        "q3": np.nan,
                        "min": np.nan,
                        "max": np.nan,
                        "summary": f"{level_n} ({level_pct * 100:.1f}%)" if denominator else "",
                        "p_value": p_value,
                        "p_value_formatted": format_p_value(p_value),
                    }
                )

    return pd.DataFrame(rows)


def build_prediction_design(assignments: pd.DataFrame, predictors: list[str]) -> pd.DataFrame:
    """构造 logistic prediction 的设计矩阵。"""
    data = assignments[predictors].copy()
    for col in data.columns:
        if pd.api.types.is_numeric_dtype(data[col]):
            data[col] = pd.to_numeric(data[col], errors="coerce")
            data[col] = data[col].fillna(data[col].median())
        else:
            data[col] = data[col].astype("object").where(data[col].notna(), "Unknown")
    design = pd.get_dummies(data, columns=[col for col in data.columns if not pd.api.types.is_numeric_dtype(data[col])], drop_first=True)
    return design.astype(float)


def evaluate_prediction_model(assignments: pd.DataFrame, model_name: str, predictors: list[str]) -> dict:
    """用交叉验证评估死亡预测增量。"""
    y = assignments["hospital_mortality"].astype(int).to_numpy()
    x = build_prediction_design(assignments, predictors)
    min_class_n = int(pd.Series(y).value_counts().min())
    n_splits = max(2, min(CV_FOLDS, min_class_n))
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_SEED)
    model = LogisticRegression(max_iter=2000, solver="liblinear")
    pred = cross_val_predict(model, x, y, cv=cv, method="predict_proba")[:, 1]
    pred_clip = np.clip(pred, 1e-6, 1 - 1e-6)
    logit_pred = np.log(pred_clip / (1 - pred_clip)).reshape(-1, 1)
    calibration_model = LogisticRegression(max_iter=2000, solver="liblinear")
    calibration_model.fit(logit_pred, y)

    return {
        "cohort_flag": COHORT_FLAG,
        "model": model_name,
        "predictors": ",".join(predictors),
        "n": int(len(assignments)),
        "events": int(y.sum()),
        "cv_folds": int(n_splits),
        "auroc": float(roc_auc_score(y, pred)),
        "brier_score": float(brier_score_loss(y, pred)),
        "observed_event_rate": float(y.mean()),
        "mean_predicted_risk": float(pred.mean()),
        "calibration_in_the_large": float(y.mean() - pred.mean()),
        "approx_calibration_slope": float(calibration_model.coef_[0][0]),
    }


def run_prediction_increment(assignments: pd.DataFrame) -> pd.DataFrame:
    """比较 GCS-only、8 变量、phenotype、phenotype+贫血+协变量的预测性能。"""
    assignments = assignments.copy()
    assignments["phenotype_factor"] = assignments["phenotype"].map(lambda x: f"P{int(x)}")
    model_specs = {
        "gcs_only": ["gcs_min_48h"],
        "features_8": FEATURES,
        "phenotype_only": ["phenotype_factor"],
        "phenotype_anemia_covariates": [
            "phenotype_factor",
            "early_anemia_all",
            "age",
            "gender",
            "admission_type",
            "nsah_evidence_level",
            "has_aneurysm_dx",
            "has_aneurysm_procedure",
        ],
    }
    rows = [evaluate_prediction_model(assignments, name, predictors) for name, predictors in model_specs.items()]
    return pd.DataFrame(rows)


def build_survival_dataset(assignments: pd.DataFrame) -> pd.DataFrame:
    """Prepare in-hospital time-to-event data.

    Alive discharges are censored at hospital discharge. This is a hospital-course
    analysis, not post-discharge long-term survival.
    """
    survival_columns = [
        "phenotype",
        "hospital_los_days",
        "hospital_mortality",
        "age",
        "gender",
        "admission_type",
        "early_anemia_all",
        "nsah_evidence_level",
        "has_aneurysm_dx",
        "has_aneurysm_procedure",
        *PROCESS_OF_CARE_MODEL_FEATURES,
    ]
    survival = assignments[[col for col in survival_columns if col in assignments.columns]].copy()
    survival["time_days"] = pd.to_numeric(survival["hospital_los_days"], errors="coerce")
    survival["event"] = pd.to_numeric(survival["hospital_mortality"], errors="coerce")
    survival = survival.dropna(subset=["phenotype", "time_days", "event"])
    survival = survival[survival["time_days"] > 0].copy()
    survival["phenotype"] = survival["phenotype"].astype(int)
    survival["event"] = survival["event"].astype(int)
    survival["admission_type_group"] = survival["admission_type"].map(collapse_admission_type)
    if "fluid_balance_l_48h" in survival:
        median_fluid = survival["fluid_balance_l_48h"].median()
        survival["fluid_balance_l_48h_imputed"] = survival["fluid_balance_l_48h"].fillna(median_fluid)
        survival["fluid_balance_l_48h_missing"] = survival["fluid_balance_l_48h"].isna().astype(int)
    return survival


def build_km_curve(assignments: pd.DataFrame) -> pd.DataFrame:
    """Build Kaplan-Meier survival curve points by phenotype."""
    survival = build_survival_dataset(assignments)
    rows = []
    for phenotype, group in survival.groupby("phenotype"):
        group = group.sort_values("time_days")
        at_risk_initial = int(len(group))
        survival_prob = 1.0
        cumulative_events = 0
        rows.append(
            {
                "cohort_flag": COHORT_FLAG,
                "phenotype": int(phenotype),
                "time_days": 0.0,
                "n_at_risk": at_risk_initial,
                "events_at_time": 0,
                "censored_at_time": 0,
                "cumulative_events": 0,
                "survival_probability": 1.0,
                "failure_probability": 0.0,
                "note": "Alive discharges are censored at hospital discharge; hospital-course analysis only.",
            }
        )
        for time_value in np.sort(group["time_days"].unique()):
            at_risk = int((group["time_days"] >= time_value).sum())
            at_time = group[group["time_days"] == time_value]
            events = int(at_time["event"].sum())
            censored = int((at_time["event"] == 0).sum())
            if at_risk > 0 and events > 0:
                survival_prob *= max(0.0, 1.0 - events / at_risk)
            cumulative_events += events
            rows.append(
                {
                    "cohort_flag": COHORT_FLAG,
                    "phenotype": int(phenotype),
                    "time_days": float(time_value),
                    "n_at_risk": at_risk,
                    "events_at_time": events,
                    "censored_at_time": censored,
                    "cumulative_events": cumulative_events,
                    "survival_probability": float(survival_prob),
                    "failure_probability": float(1.0 - survival_prob),
                    "note": "Alive discharges are censored at hospital discharge; hospital-course analysis only.",
                }
            )
    return pd.DataFrame(rows).sort_values(["phenotype", "time_days"])


def pairwise_logrank(group_a: pd.DataFrame, group_b: pd.DataFrame) -> dict[str, float]:
    """Two-sample log-rank test without optional dependencies."""
    combined = pd.concat([group_a.assign(_group=0), group_b.assign(_group=1)], ignore_index=True)
    event_times = np.sort(combined.loc[combined["event"] == 1, "time_days"].unique())
    observed_a = 0.0
    expected_a = 0.0
    variance_a = 0.0
    for time_value in event_times:
        risk_a = float(((group_a["time_days"] >= time_value)).sum())
        risk_b = float(((group_b["time_days"] >= time_value)).sum())
        events_a = float(((group_a["time_days"] == time_value) & (group_a["event"] == 1)).sum())
        events_b = float(((group_b["time_days"] == time_value) & (group_b["event"] == 1)).sum())
        risk_total = risk_a + risk_b
        events_total = events_a + events_b
        if risk_total <= 1 or events_total <= 0:
            continue
        observed_a += events_a
        expected_a += events_total * risk_a / risk_total
        variance_a += (
            risk_a
            * risk_b
            * events_total
            * (risk_total - events_total)
            / (risk_total**2 * (risk_total - 1))
        )
    statistic = ((observed_a - expected_a) ** 2 / variance_a) if variance_a > 0 else np.nan
    p_value = float(stats.chi2.sf(statistic, df=1)) if pd.notna(statistic) else np.nan
    return {
        "observed_events_a": float(observed_a),
        "expected_events_a": float(expected_a),
        "chi_square": float(statistic) if pd.notna(statistic) else np.nan,
        "p_value": p_value,
    }


def run_survival_logrank(assignments: pd.DataFrame) -> pd.DataFrame:
    """Pairwise log-rank tests for in-hospital death timing by phenotype."""
    survival = build_survival_dataset(assignments)
    phenotypes = sorted(survival["phenotype"].dropna().unique())
    rows = []
    for idx, phenotype_a in enumerate(phenotypes):
        for phenotype_b in phenotypes[idx + 1:]:
            group_a = survival[survival["phenotype"] == phenotype_a]
            group_b = survival[survival["phenotype"] == phenotype_b]
            test = pairwise_logrank(group_a, group_b)
            rows.append(
                {
                    "cohort_flag": COHORT_FLAG,
                    "comparison": f"P{int(phenotype_a)} vs P{int(phenotype_b)}",
                    "phenotype_a": int(phenotype_a),
                    "phenotype_b": int(phenotype_b),
                    "n_a": int(len(group_a)),
                    "n_b": int(len(group_b)),
                    "events_a": int(group_a["event"].sum()),
                    "events_b": int(group_b["event"].sum()),
                    **test,
                    "note": "Pairwise log-rank test; alive discharges censored at hospital discharge.",
                }
            )
    return pd.DataFrame(rows)


def run_survival_cox_models(assignments: pd.DataFrame) -> pd.DataFrame:
    """Fit unadjusted and clinically adjusted Cox models for in-hospital death timing."""
    survival = build_survival_dataset(assignments)
    rows = []
    try:
        from statsmodels.duration.hazard_regression import PHReg
    except ImportError:
        return pd.DataFrame(
            [
                {
                    "cohort_flag": COHORT_FLAG,
                    "model": "statsmodels_phreg_unavailable",
                    "term": "statsmodels_phreg_unavailable",
                    "hazard_ratio": np.nan,
                    "ci_lower": np.nan,
                    "ci_upper": np.nan,
                    "p_value": np.nan,
                    "n": int(len(survival)),
                    "events": int(survival["event"].sum()),
                    "note": "statsmodels PHReg is required for Cox model output.",
                }
            ]
        )

    model_specs = {
        "cox_phenotype_unadjusted": ["phenotype"],
        "cox_phenotype_clinical": [
            "phenotype",
            "age",
            "gender",
            "admission_type_group",
            "early_anemia_all",
            "nsah_evidence_level",
            "has_aneurysm_dx",
            "has_aneurysm_procedure",
        ],
        "cox_phenotype_process_of_care_exploratory": [
            "phenotype",
            "age",
            "gender",
            "admission_type_group",
            "early_anemia_all",
            "nsah_evidence_level",
            "has_aneurysm_dx",
            "aneurysm_securing_hosp",
            "nimodipine_48h",
            "evd_or_icp_48h",
            "vasopressor_48h",
            "mech_vent_48h",
            "any_rbc_transfusion_48h",
            "crrt_48h",
            "fluid_balance_l_48h_imputed",
            "fluid_balance_l_48h_missing",
        ],
    }
    for model_name, predictors in model_specs.items():
        predictors = [col for col in predictors if col in survival.columns]
        model_df = survival[["time_days", "event", *predictors]].copy()
        model_df = model_df.dropna(subset=["time_days", "event", "phenotype"])
        model_df["phenotype"] = model_df["phenotype"].map(lambda value: f"P{int(value)}")
        categorical = [col for col in ["phenotype", "gender", "admission_type_group"] if col in model_df.columns]
        design = pd.get_dummies(model_df[predictors], columns=categorical, drop_first=True)
        for col in design.columns:
            design[col] = pd.to_numeric(design[col], errors="coerce")
            if design[col].isna().any():
                design[col] = design[col].fillna(design[col].median())
        constant_cols = [col for col in design.columns if design[col].nunique(dropna=True) <= 1]
        design = design.drop(columns=constant_cols)
        if design.empty:
            continue
        try:
            fitted = PHReg(
                endog=model_df["time_days"].astype(float),
                exog=design.astype(float),
                status=model_df["event"].astype(int),
            ).fit(disp=False)
            conf = fitted.conf_int()
            for idx, term in enumerate(design.columns):
                rows.append(
                    {
                        "cohort_flag": COHORT_FLAG,
                        "model": model_name,
                        "term": term,
                        "hazard_ratio": float(np.exp(fitted.params[idx])),
                        "ci_lower": float(np.exp(conf[idx, 0])),
                        "ci_upper": float(np.exp(conf[idx, 1])),
                        "p_value": float(fitted.pvalues[idx]),
                        "n": int(len(model_df)),
                        "events": int(model_df["event"].sum()),
                        "note": (
                            "Cox model for in-hospital death timing; alive discharges censored at discharge. "
                            "Process-of-care variables measured over 0-48h are exploratory fixed covariates only; "
                            "they may introduce immortal time bias and should be handled as time-varying covariates "
                            "for formal survival adjustment."
                        ),
                    }
                )
        except Exception as exc:
            rows.append(
                {
                    "cohort_flag": COHORT_FLAG,
                    "model": model_name,
                    "term": "model_failed",
                    "hazard_ratio": np.nan,
                    "ci_lower": np.nan,
                    "ci_upper": np.nan,
                    "p_value": np.nan,
                    "n": int(len(model_df)),
                    "events": int(model_df["event"].sum()),
                    "note": str(exc),
                }
            )
    return pd.DataFrame(rows)


def build_feature_heatmap_table(assignments: pd.DataFrame, centers: pd.DataFrame) -> pd.DataFrame:
    """Build long-format heatmap data using raw medians and standardized centers."""
    rows = []
    center_lookup = centers.set_index("phenotype")
    for phenotype, group in assignments.groupby("phenotype"):
        for feature in FEATURES:
            raw_values = pd.to_numeric(group[feature], errors="coerce")
            z_center = (
                float(center_lookup.loc[phenotype, feature])
                if phenotype in center_lookup.index and feature in center_lookup.columns
                else np.nan
            )
            rows.append(
                {
                    "cohort_flag": COHORT_FLAG,
                    "phenotype": int(phenotype),
                    "feature": feature,
                    "feature_label": FEATURE_LABELS.get(feature, feature),
                    "severity_direction": int(SEVERITY_DIRECTIONS.get(feature, 1)),
                    "z_center": z_center,
                    "median": float(raw_values.median()),
                    "q1": float(raw_values.quantile(0.25)),
                    "q3": float(raw_values.quantile(0.75)),
                    "mean": float(raw_values.mean()),
                    "n_nonmissing": int(raw_values.notna().sum()),
                    "missing_rate": float(raw_values.isna().mean()),
                    "display_value": f"{raw_values.median():.2f} [{raw_values.quantile(0.25):.2f}, {raw_values.quantile(0.75):.2f}]",
                    "note": "Rows provide raw median [IQR] plus standardized phenotype center for heatmap display.",
                }
            )
    return pd.DataFrame(rows).sort_values(["phenotype", "feature"])


def run_linear_shap_analysis(assignments: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Approximate SHAP-style contributions for an interpretable logistic mortality model.

    For a standardized linear logistic model, feature contribution to log-odds is
    beta_j * (x_j - mean_j). Because standardized features have mean 0, this is
    beta_j * z_j. We label this explicitly as an approximation and use it only
    to explain the mortality prediction model, not the unsupervised clustering.
    """
    model_df = assignments[["phenotype", "hospital_mortality", *FEATURES]].copy()
    y = pd.to_numeric(model_df["hospital_mortality"], errors="coerce").astype(float)
    x_raw = model_df[FEATURES].apply(pd.to_numeric, errors="coerce")
    x_transformed = x_raw.copy()
    for feature in LOG_TRANSFORM_FEATURES:
        if feature in x_transformed:
            x_transformed[feature] = np.log1p(x_transformed[feature].clip(lower=0))

    valid = y.notna()
    y = y.loc[valid].astype(int)
    x_transformed = x_transformed.loc[valid]
    phenotypes = model_df.loc[valid, "phenotype"].astype(int)
    imputer = SimpleImputer(strategy="median")
    scaler = StandardScaler()
    x_imputed = imputer.fit_transform(x_transformed)
    x_scaled = scaler.fit_transform(x_imputed)
    model = LogisticRegression(max_iter=2000, solver="liblinear", random_state=RANDOM_SEED)
    model.fit(x_scaled, y)
    coefficients = model.coef_[0]
    contributions = x_scaled * coefficients
    predicted_risk = model.predict_proba(x_scaled)[:, 1]

    importance_rows = []
    for idx, feature in enumerate(FEATURES):
        values = contributions[:, idx]
        importance_rows.append(
            {
                "cohort_flag": COHORT_FLAG,
                "model": "features_8_log1p_standardized_logistic",
                "explanation_method": "linear_logistic_shap_approximation",
                "feature": feature,
                "feature_label": FEATURE_LABELS.get(feature, feature),
                "transform": "log1p" if feature in LOG_TRANSFORM_FEATURES else "none",
                "coefficient": float(coefficients[idx]),
                "mean_abs_shap_log_odds": float(np.mean(np.abs(values))),
                "mean_shap_log_odds": float(np.mean(values)),
                "median_abs_shap_log_odds": float(np.median(np.abs(values))),
                "rank_by_mean_abs": 0,
                "n": int(len(y)),
                "events": int(y.sum()),
                "auroc_apparent": float(roc_auc_score(y, predicted_risk)),
                "note": "Linear SHAP-style log-odds contribution from a standardized logistic model; explains mortality prediction, not cluster assignment.",
            }
        )
    importance = pd.DataFrame(importance_rows).sort_values("mean_abs_shap_log_odds", ascending=False)
    importance["rank_by_mean_abs"] = np.arange(1, len(importance) + 1)

    contribution_df = pd.DataFrame(contributions, columns=FEATURES)
    contribution_df["phenotype"] = phenotypes.to_numpy()
    phenotype_rows = []
    for phenotype, group in contribution_df.groupby("phenotype"):
        for feature in FEATURES:
            values = group[feature].to_numpy(dtype=float)
            phenotype_rows.append(
                {
                    "cohort_flag": COHORT_FLAG,
                    "model": "features_8_log1p_standardized_logistic",
                    "explanation_method": "linear_logistic_shap_approximation",
                    "phenotype": int(phenotype),
                    "feature": feature,
                    "feature_label": FEATURE_LABELS.get(feature, feature),
                    "mean_shap_log_odds": float(np.mean(values)),
                    "mean_abs_shap_log_odds": float(np.mean(np.abs(values))),
                    "median_shap_log_odds": float(np.median(values)),
                    "n": int(len(group)),
                    "note": "Positive values increase predicted hospital mortality log-odds in the fitted mortality model.",
                }
            )
    phenotype_contributions = pd.DataFrame(phenotype_rows).sort_values(["phenotype", "feature"])
    return {
        "importance": importance,
        "phenotype_contributions": phenotype_contributions,
    }


def run_adjusted_regression(assignments: pd.DataFrame) -> pd.DataFrame:
    """用 statsmodels 输出 phenotype 与贫血相关的调整后死亡模型。"""
    try:
        import statsmodels.formula.api as smf
    except ImportError:
        y = pd.to_numeric(assignments["hospital_mortality"], errors="coerce")
        return pd.DataFrame(
            [
                {
                    "cohort_flag": COHORT_FLAG,
                    "model": "statsmodels_unavailable",
                    "term": "statsmodels_unavailable",
                    "odds_ratio": np.nan,
                    "ci_lower": np.nan,
                    "ci_upper": np.nan,
                    "p_value": np.nan,
                    "n": int(y.notna().sum()),
                    "events": int((y == 1).sum()),
                    "note": "statsmodels is required for adjusted OR and 95% CI output.",
                }
            ]
        )

    model_df = prepare_logit_dataframe(
        assignments[
            [
                "hospital_mortality",
                "phenotype",
                "early_anemia_all",
                "age",
                "gender",
                "admission_type",
                "nsah_evidence_level",
                "has_aneurysm_dx",
                "has_aneurysm_procedure",
            ]
        ],
        numeric_columns=[
            "hospital_mortality",
            "phenotype",
            "early_anemia_all",
            "age",
            "nsah_evidence_level",
            "has_aneurysm_dx",
            "has_aneurysm_procedure",
        ],
        categorical_columns=["gender", "admission_type"],
        required_columns=["hospital_mortality", "phenotype", "early_anemia_all", "age"],
    )
    model_df["admission_type_group"] = model_df["admission_type"].map(collapse_admission_type)

    formulas = build_adjusted_regression_formulas(model_df)
    formula_note = formulas.pop("_note")

    rows = []
    for model_name, formula in formulas.items():
        try:
            fitted = fit_logit_quiet(smf, formula, model_df)
            conf = fitted.conf_int()
            converged = bool(fitted.mle_retvals.get("converged", True))
            for term, coef in fitted.params.items():
                rows.append(
                    {
                        "cohort_flag": COHORT_FLAG,
                        "model": model_name,
                        "term": term,
                        "odds_ratio": float(np.exp(coef)),
                        "ci_lower": float(np.exp(conf.loc[term, 0])),
                        "ci_upper": float(np.exp(conf.loc[term, 1])),
                        "p_value": float(fitted.pvalues[term]),
                        "n": int(fitted.nobs),
                        "events": int(model_df["hospital_mortality"].sum()),
                        "note": "; ".join(
                            part
                            for part in [
                                formula_note,
                                "" if converged else "Maximum likelihood optimizer did not report convergence; interpret adjusted OR cautiously.",
                            ]
                            if part
                        ),
                    }
                )
        except Exception as exc:
            rows.append(
                {
                    "cohort_flag": COHORT_FLAG,
                    "model": model_name,
                    "term": "model_failed",
                    "odds_ratio": np.nan,
                    "ci_lower": np.nan,
                    "ci_upper": np.nan,
                    "p_value": np.nan,
                    "n": int(len(model_df)),
                    "events": int(model_df["hospital_mortality"].sum()),
                    "note": str(exc),
                }
            )

    return pd.DataFrame(rows)


def run_severity_score_adjusted_models(assignments: pd.DataFrame) -> pd.DataFrame:
    """Test whether phenotype remains associated with mortality after severity-score adjustment."""
    try:
        import statsmodels.formula.api as smf
    except ImportError:
        return pd.DataFrame(
            [
                {
                    "cohort_flag": COHORT_FLAG,
                    "model": "statsmodels_unavailable",
                    "term": "statsmodels_unavailable",
                    "odds_ratio": np.nan,
                    "ci_lower": np.nan,
                    "ci_upper": np.nan,
                    "p_value": np.nan,
                    "n": int(len(assignments)),
                    "events": int((assignments["hospital_mortality"] == 1).sum()),
                    "aic": np.nan,
                    "bic": np.nan,
                    "pseudo_r2": np.nan,
                    "note": "statsmodels is required for severity-score-adjusted OR and 95% CI output.",
                }
            ]
        )

    required_columns = [
        "hospital_mortality",
        "phenotype",
        "sofa_24h",
        "sapsii_24h",
        "oasis_24h",
        "lods_24h",
        "age",
        "gender",
        "admission_type",
        "early_anemia_all",
        "nsah_evidence_level",
        "has_aneurysm_dx",
        "has_aneurysm_procedure",
    ]
    available_columns = [col for col in required_columns if col in assignments.columns]
    model_df = prepare_logit_dataframe(
        assignments[available_columns],
        numeric_columns=[
            col
            for col in [
                "hospital_mortality",
                "phenotype",
                "sofa_24h",
                "sapsii_24h",
                "oasis_24h",
                "lods_24h",
                "age",
                "early_anemia_all",
                "nsah_evidence_level",
                "has_aneurysm_dx",
                "has_aneurysm_procedure",
            ]
            if col in available_columns
        ],
        categorical_columns=[col for col in ["gender", "admission_type"] if col in available_columns],
        required_columns=[
            col
            for col in [
                "hospital_mortality",
                "phenotype",
                "sofa_24h",
                "sapsii_24h",
                "oasis_24h",
                "lods_24h",
                "age",
                "early_anemia_all",
            ]
            if col in available_columns
        ],
    )
    model_df["admission_type_group"] = model_df["admission_type"].map(collapse_admission_type)

    note_parts = ["severity scores were used only for adjustment/validation, not for clustering"]
    aneurysm_terms = []
    if "nsah_evidence_level" in model_df and model_df["nsah_evidence_level"].nunique(dropna=True) > 1:
        aneurysm_terms.append("C(nsah_evidence_level)")
    else:
        note_parts.append("skipped constant nsah_evidence_level")
    if "has_aneurysm_dx" in model_df and model_df["has_aneurysm_dx"].nunique(dropna=True) > 1:
        aneurysm_terms.append("has_aneurysm_dx")
    else:
        note_parts.append("skipped constant has_aneurysm_dx")
    procedure_duplicates_evidence = (
        "has_aneurysm_procedure" in model_df
        and "nsah_evidence_level" in model_df
        and model_df["has_aneurysm_procedure"].nunique(dropna=True) > 1
        and model_df["nsah_evidence_level"].nunique(dropna=True) > 1
        and model_df["has_aneurysm_procedure"].astype(int).equals(
            (model_df["nsah_evidence_level"].astype(int) == 3).astype(int)
        )
    )
    if procedure_duplicates_evidence:
        note_parts.append("skipped has_aneurysm_procedure because it duplicates nsah_evidence_level=3")
    elif "has_aneurysm_procedure" in model_df and model_df["has_aneurysm_procedure"].nunique(dropna=True) > 1:
        aneurysm_terms.append("has_aneurysm_procedure")
    else:
        note_parts.append("skipped constant has_aneurysm_procedure")

    model_specs = {
        "phenotype_plus_sofa": "hospital_mortality ~ C(phenotype) + sofa_24h",
        "phenotype_plus_sapsii": "hospital_mortality ~ C(phenotype) + sapsii_24h",
        "phenotype_plus_oasis": "hospital_mortality ~ C(phenotype) + oasis_24h",
        "phenotype_plus_lods": "hospital_mortality ~ C(phenotype) + lods_24h",
        "phenotype_plus_sofa_clinical": "hospital_mortality ~ C(phenotype) + sofa_24h + age + C(gender) + C(admission_type_group) + early_anemia_all",
    }
    if aneurysm_terms:
        model_specs["phenotype_plus_sofa_clinical"] += " + " + " + ".join(aneurysm_terms)

    rows = []
    formula_note = "; ".join(note_parts)
    for model_name, formula in model_specs.items():
        try:
            fitted = fit_logit_quiet(smf, formula, model_df)
            conf = fitted.conf_int()
            converged = bool(fitted.mle_retvals.get("converged", True))
            null_llf = getattr(fitted, "llnull", np.nan)
            pseudo_r2 = 1 - (float(fitted.llf) / float(null_llf)) if pd.notna(null_llf) and null_llf != 0 else np.nan
            for term, coef in fitted.params.items():
                rows.append(
                    {
                        "cohort_flag": COHORT_FLAG,
                        "model": model_name,
                        "formula": formula,
                        "term": term,
                        "odds_ratio": float(np.exp(coef)),
                        "ci_lower": float(np.exp(conf.loc[term, 0])),
                        "ci_upper": float(np.exp(conf.loc[term, 1])),
                        "p_value": float(fitted.pvalues[term]),
                        "n": int(fitted.nobs),
                        "events": int(model_df["hospital_mortality"].sum()),
                        "aic": float(fitted.aic),
                        "bic": float(fitted.bic),
                        "pseudo_r2": float(pseudo_r2) if pd.notna(pseudo_r2) else np.nan,
                        "note": "; ".join(
                            part
                            for part in [
                                formula_note,
                                "" if converged else "Maximum likelihood optimizer did not report convergence; interpret adjusted OR cautiously.",
                            ]
                            if part
                        ),
                    }
                )
        except Exception as exc:
            rows.append(
                {
                    "cohort_flag": COHORT_FLAG,
                    "model": model_name,
                    "formula": formula,
                    "term": "model_failed",
                    "odds_ratio": np.nan,
                    "ci_lower": np.nan,
                    "ci_upper": np.nan,
                    "p_value": np.nan,
                    "n": int(len(model_df)),
                    "events": int(model_df["hospital_mortality"].sum()),
                    "aic": np.nan,
                    "bic": np.nan,
                    "pseudo_r2": np.nan,
                    "note": str(exc),
                }
            )

    return pd.DataFrame(rows)


def build_process_of_care_audit(assignments: pd.DataFrame) -> pd.DataFrame:
    """Summarize process-of-care variables by phenotype and overall."""
    rows = []
    groups = [("Overall", None, assignments)]
    groups.extend((f"Phenotype {int(p)}", int(p), g) for p, g in assignments.groupby("phenotype"))

    for group_name, phenotype, group in groups:
        for feature in PROCESS_OF_CARE_BINARY_FEATURES:
            if feature not in group.columns:
                continue
            values = pd.to_numeric(group[feature], errors="coerce")
            non_missing = values.dropna()
            rows.append(
                {
                    "cohort_flag": COHORT_FLAG,
                    "group": group_name,
                    "phenotype": phenotype,
                    "variable": feature,
                    "variable_type": "binary_process_of_care",
                    "n": int(len(group)),
                    "n_nonmissing": int(non_missing.shape[0]),
                    "missing_n": int(values.isna().sum()),
                    "missing_rate": float(values.isna().mean()),
                    "event_n": int((non_missing == 1).sum()),
                    "event_rate": float((non_missing == 1).mean()) if len(non_missing) else np.nan,
                    "median": np.nan,
                    "q1": np.nan,
                    "q3": np.nan,
                    "mean": np.nan,
                    "note": "Process-of-care marker; use for Table 1 and sensitivity adjustment, not as a causal mediator-free covariate.",
                }
            )
        for feature in PROCESS_OF_CARE_CONTINUOUS_FEATURES:
            if feature not in group.columns:
                continue
            values = pd.to_numeric(group[feature], errors="coerce")
            non_missing = values.dropna()
            rows.append(
                {
                    "cohort_flag": COHORT_FLAG,
                    "group": group_name,
                    "phenotype": phenotype,
                    "variable": feature,
                    "variable_type": "continuous_process_of_care",
                    "n": int(len(group)),
                    "n_nonmissing": int(non_missing.shape[0]),
                    "missing_n": int(values.isna().sum()),
                    "missing_rate": float(values.isna().mean()),
                    "event_n": np.nan,
                    "event_rate": np.nan,
                    "median": float(non_missing.median()) if len(non_missing) else np.nan,
                    "q1": float(non_missing.quantile(0.25)) if len(non_missing) else np.nan,
                    "q3": float(non_missing.quantile(0.75)) if len(non_missing) else np.nan,
                    "mean": float(non_missing.mean()) if len(non_missing) else np.nan,
                    "note": "Fluid balance is derived from charted ICU inputs and outputs; interpret as a process-of-care marker with measurement-quality limits.",
                }
            )
    return pd.DataFrame(rows).sort_values(["variable_type", "variable", "group"])


def build_available_formula_terms(model_df: pd.DataFrame, candidate_terms: list[tuple[str, str]]) -> tuple[list[str], list[str]]:
    """Return formula terms whose underlying columns are available and nonconstant."""
    terms = []
    notes = []
    for column, term in candidate_terms:
        if column not in model_df.columns:
            notes.append(f"skipped missing {column}")
            continue
        values = model_df[column]
        if values.dropna().nunique() <= 1:
            notes.append(f"skipped constant {column}")
            continue
        terms.append(term)
    return terms, notes


def run_process_of_care_adjusted_models(assignments: pd.DataFrame) -> pd.DataFrame:
    """Progressive mortality models including process-of-care variables as sensitivity adjustment."""
    try:
        import statsmodels.formula.api as smf
    except ImportError:
        return pd.DataFrame(
            [
                {
                    "cohort_flag": COHORT_FLAG,
                    "model": "statsmodels_unavailable",
                    "term": "statsmodels_unavailable",
                    "odds_ratio": np.nan,
                    "ci_lower": np.nan,
                    "ci_upper": np.nan,
                    "p_value": np.nan,
                    "n": int(len(assignments)),
                    "events": int((assignments["hospital_mortality"] == 1).sum()),
                    "aic": np.nan,
                    "bic": np.nan,
                    "note": "statsmodels is required for process-of-care adjusted models.",
                }
            ]
        )

    required = [
        "hospital_mortality",
        "phenotype",
        "age",
        "gender",
        "admission_type",
        "nsah_evidence_level",
        "has_aneurysm_dx",
        "has_aneurysm_procedure",
        "early_anemia_all",
        *PROCESS_OF_CARE_MODEL_FEATURES,
    ]
    available = [col for col in required if col in assignments.columns]
    model_df = prepare_logit_dataframe(
        assignments[available],
        numeric_columns=[
            col
            for col in [
                "hospital_mortality",
                "phenotype",
                "age",
                "nsah_evidence_level",
                "has_aneurysm_dx",
                "has_aneurysm_procedure",
                "early_anemia_all",
                *PROCESS_OF_CARE_MODEL_FEATURES,
            ]
            if col in available
        ],
        categorical_columns=[col for col in ["gender", "admission_type"] if col in available],
        required_columns=["hospital_mortality", "phenotype", "age"],
    )
    model_df["admission_type_group"] = model_df["admission_type"].map(collapse_admission_type)
    if "fluid_balance_l_48h" in model_df:
        median_fluid = model_df["fluid_balance_l_48h"].median()
        model_df["fluid_balance_l_48h_imputed"] = model_df["fluid_balance_l_48h"].fillna(median_fluid)
        model_df["fluid_balance_l_48h_missing"] = model_df["fluid_balance_l_48h"].isna().astype(int)

    demographic_terms = [
        ("age", "age"),
        ("gender", "C(gender)"),
        ("admission_type_group", "C(admission_type_group)"),
        ("nsah_evidence_level", "C(nsah_evidence_level)"),
        ("has_aneurysm_dx", "has_aneurysm_dx"),
        ("early_anemia_all", "early_anemia_all"),
    ]
    specialty_terms = [
        ("aneurysm_securing_hosp", "aneurysm_securing_hosp"),
        ("nimodipine_48h", "nimodipine_48h"),
        ("evd_or_icp_48h", "evd_or_icp_48h"),
    ]
    organ_support_terms = [
        ("vasopressor_48h", "vasopressor_48h"),
        ("mech_vent_48h", "mech_vent_48h"),
        ("any_rbc_transfusion_48h", "any_rbc_transfusion_48h"),
        ("crrt_48h", "crrt_48h"),
        ("fluid_balance_l_48h_imputed", "fluid_balance_l_48h_imputed"),
        ("fluid_balance_l_48h_missing", "fluid_balance_l_48h_missing"),
    ]
    demo, demo_notes = build_available_formula_terms(model_df, demographic_terms)
    specialty, specialty_notes = build_available_formula_terms(model_df, specialty_terms)
    organ_support, organ_support_notes = build_available_formula_terms(model_df, organ_support_terms)

    model_terms = {
        "process_model_1_phenotype_only": ["C(phenotype)"],
        "process_model_2_demographic_etiology": ["C(phenotype)", *demo],
        "process_model_3_specialty_care": ["C(phenotype)", *demo, *specialty],
        "process_model_4_organ_support": ["C(phenotype)", *demo, *specialty, *organ_support],
    }
    formula_notes = "; ".join(
        [
            "process-of-care variables may be downstream markers or mediators; interpret as sensitivity adjustment, not causal control",
            *demo_notes,
            *specialty_notes,
            *organ_support_notes,
        ]
    )
    rows = []
    for model_name, terms in model_terms.items():
        formula = "hospital_mortality ~ " + " + ".join(dict.fromkeys(terms))
        try:
            fitted = fit_logit_quiet(smf, formula, model_df)
            conf = fitted.conf_int()
            converged = bool(fitted.mle_retvals.get("converged", True))
            for term, coef in fitted.params.items():
                rows.append(
                    {
                        "cohort_flag": COHORT_FLAG,
                        "model": model_name,
                        "formula": formula,
                        "term": term,
                        "odds_ratio": float(np.exp(coef)),
                        "ci_lower": float(np.exp(conf.loc[term, 0])),
                        "ci_upper": float(np.exp(conf.loc[term, 1])),
                        "p_value": float(fitted.pvalues[term]),
                        "n": int(fitted.nobs),
                        "events": int(model_df["hospital_mortality"].sum()),
                        "aic": float(fitted.aic),
                        "bic": float(fitted.bic),
                        "note": "; ".join(
                            part
                            for part in [
                                formula_notes,
                                "" if converged else "Maximum likelihood optimizer did not report convergence; interpret cautiously.",
                            ]
                            if part
                        ),
                    }
                )
        except Exception as exc:
            rows.append(
                {
                    "cohort_flag": COHORT_FLAG,
                    "model": model_name,
                    "formula": formula,
                    "term": "model_failed",
                    "odds_ratio": np.nan,
                    "ci_lower": np.nan,
                    "ci_upper": np.nan,
                    "p_value": np.nan,
                    "n": int(len(model_df)),
                    "events": int(model_df["hospital_mortality"].sum()),
                    "aic": np.nan,
                    "bic": np.nan,
                    "note": str(exc),
                }
            )
    return pd.DataFrame(rows)


def run_anemia_stratified_regression(assignments: pd.DataFrame) -> pd.DataFrame:
    """在每个 K=3 phenotype 内估计早期贫血与住院死亡的调整后关联。"""
    try:
        import statsmodels.formula.api as smf
    except ImportError:
        return pd.DataFrame(
            [
                {
                    "cohort_flag": COHORT_FLAG,
                    "phenotype": np.nan,
                    "model": "statsmodels_unavailable",
                    "term": "early_anemia_all",
                    "odds_ratio": np.nan,
                    "ci_lower": np.nan,
                    "ci_upper": np.nan,
                    "p_value": np.nan,
                    "n": int(len(assignments)),
                    "events": int((assignments["hospital_mortality"] == 1).sum()),
                    "anemia_n": int((assignments["early_anemia_all"] == 1).sum()),
                    "anemia_deaths": int(((assignments["early_anemia_all"] == 1) & (assignments["hospital_mortality"] == 1)).sum()),
                    "non_anemia_n": int((assignments["early_anemia_all"] == 0).sum()),
                    "non_anemia_deaths": int(((assignments["early_anemia_all"] == 0) & (assignments["hospital_mortality"] == 1)).sum()),
                    "note": "statsmodels is required for phenotype-stratified adjusted OR output.",
                }
            ]
        )

    rows = []
    base_cols = ["hospital_mortality", "early_anemia_all", "age", "gender", "admission_type"]
    for phenotype, group in assignments.groupby("phenotype"):
        model_df = prepare_logit_dataframe(
            group[base_cols],
            numeric_columns=["hospital_mortality", "early_anemia_all", "age"],
            categorical_columns=["gender", "admission_type"],
            required_columns=["hospital_mortality", "early_anemia_all", "age"],
        )
        model_df["admission_type_group"] = model_df["admission_type"].map(collapse_admission_type)

        anemia_mask = model_df["early_anemia_all"] == 1
        event_n = int((model_df["hospital_mortality"] == 1).sum())
        anemia_n = int(anemia_mask.sum())
        anemia_deaths = int(((model_df["early_anemia_all"] == 1) & (model_df["hospital_mortality"] == 1)).sum())
        non_anemia_n = int((~anemia_mask).sum())
        non_anemia_deaths = int(((model_df["early_anemia_all"] == 0) & (model_df["hospital_mortality"] == 1)).sum())

        row_base = {
            "cohort_flag": COHORT_FLAG,
            "phenotype": int(phenotype),
            "model": "phenotype_stratified_anemia",
            "term": "early_anemia_all",
            "n": int(len(model_df)),
            "events": event_n,
            "anemia_n": anemia_n,
            "anemia_deaths": anemia_deaths,
            "non_anemia_n": non_anemia_n,
            "non_anemia_deaths": non_anemia_deaths,
        }

        if (
            len(model_df) < 50
            or model_df["early_anemia_all"].nunique() < 2
            or model_df["hospital_mortality"].nunique() < 2
            or min(anemia_n, non_anemia_n, anemia_deaths, non_anemia_deaths) < 5
        ):
            rows.append(
                {
                    **row_base,
                    "odds_ratio": np.nan,
                    "ci_lower": np.nan,
                    "ci_upper": np.nan,
                    "p_value": np.nan,
                    "note": "Sparse phenotype x anemia x mortality cells; report crude rates and treat adjusted OR as unstable.",
                }
            )
            continue

        formula = "hospital_mortality ~ early_anemia_all + age + C(gender) + C(admission_type_group)"
        try:
            fitted = fit_logit_quiet(smf, formula, model_df)
            conf = fitted.conf_int()
            term = "early_anemia_all"
            converged = bool(fitted.mle_retvals.get("converged", True))
            rows.append(
                {
                    **row_base,
                    "odds_ratio": float(np.exp(fitted.params[term])),
                    "ci_lower": float(np.exp(conf.loc[term, 0])),
                    "ci_upper": float(np.exp(conf.loc[term, 1])),
                    "p_value": float(fitted.pvalues[term]),
                    "note": "" if converged else "Maximum likelihood optimizer did not report convergence; interpret adjusted OR cautiously.",
                }
            )
        except Exception as exc:
            rows.append(
                {
                    **row_base,
                    "odds_ratio": np.nan,
                    "ci_lower": np.nan,
                    "ci_upper": np.nan,
                    "p_value": np.nan,
                    "note": str(exc),
                }
            )

    return pd.DataFrame(rows).sort_values("phenotype")


def run_sensitivity_cohort_summaries(df: pd.DataFrame, primary_assignments: pd.DataFrame) -> pd.DataFrame:
    """在主分析宽表内对预先定义的敏感性子队列重新聚类并汇总结局。"""
    rows = []
    reference = primary_assignments[["stay_id", "phenotype"]].rename(columns={"phenotype": "primary_phenotype"})

    for analysis_name, flag_col in SENSITIVITY_COHORT_FLAGS.items():
        if flag_col not in df.columns:
            continue
        sub_df = df[df[flag_col] == 1].copy()
        if len(sub_df) < PRIMARY_K * 20:
            rows.append(
                {
                    "cohort_flag": COHORT_FLAG,
                    "analysis": analysis_name,
                    "flag_column": flag_col,
                    "phenotype": np.nan,
                    "n": int(len(sub_df)),
                    "hospital_deaths": int((sub_df["hospital_mortality"] == 1).sum()) if len(sub_df) else 0,
                    "hospital_mortality_rate": float(sub_df["hospital_mortality"].mean()) if len(sub_df) else np.nan,
                    "early_anemia_rate": float(sub_df["early_anemia_all"].mean()) if len(sub_df) else np.nan,
                    "silhouette": np.nan,
                    "min_cluster_n": np.nan,
                    "min_cluster_frac": np.nan,
                    "ari_vs_primary_subset": np.nan,
                    "note": "Sensitivity cohort too small for stable K=3 re-clustering.",
                }
            )
            continue

        _, _, x_scaled_sens, _, _, _ = preprocess_feature_matrix(sub_df, FEATURES)
        model = KMeans(n_clusters=PRIMARY_K, random_state=RANDOM_SEED, n_init=100)
        raw_labels = model.fit_predict(x_scaled_sens)
        _, label_map = build_ordered_phenotype_labels(x_scaled_sens, raw_labels)
        assignments = build_assignments(sub_df, raw_labels, label_map)
        assignments = assignments.merge(reference, on="stay_id", how="left")
        counts = assignments["phenotype"].value_counts()
        ari = adjusted_rand_score(
            assignments["primary_phenotype"].astype(int),
            assignments["phenotype"].astype(int),
        ) if assignments["primary_phenotype"].notna().all() else np.nan
        silhouette = float(silhouette_score(x_scaled_sens, assignments["phenotype"]))

        for phenotype, group in assignments.groupby("phenotype"):
            rows.append(
                {
                    "cohort_flag": COHORT_FLAG,
                    "analysis": analysis_name,
                    "flag_column": flag_col,
                    "phenotype": int(phenotype),
                    "n": int(len(group)),
                    "hospital_deaths": int((group["hospital_mortality"] == 1).sum()),
                    "hospital_mortality_rate": float(group["hospital_mortality"].mean()),
                    "early_anemia_rate": float(group["early_anemia_all"].mean()),
                    "silhouette": silhouette,
                    "min_cluster_n": int(counts.min()),
                    "min_cluster_frac": float(counts.min() / len(assignments)),
                    "ari_vs_primary_subset": float(ari) if not pd.isna(ari) else np.nan,
                    "note": "",
                }
            )

    return pd.DataFrame(rows).sort_values(["analysis", "phenotype"])


def run_epvs_sensitivity(df: pd.DataFrame, primary_assignments: pd.DataFrame) -> pd.DataFrame:
    """评估 ePVS 作为候选增强变量时 K=3 表型结构是否改变。"""
    rows = []
    reference = primary_assignments["phenotype"].astype(int).to_numpy()

    for feature_set_name, features in EPVS_SENSITIVITY_FEATURE_SETS.items():
        missing_features = [feature for feature in features if feature not in df.columns]
        if missing_features:
            rows.append(
                {
                    "cohort_flag": COHORT_FLAG,
                    "feature_set": feature_set_name,
                    "features": ",".join(features),
                    "phenotype": np.nan,
                    "phenotype_n": np.nan,
                    "hospital_deaths": np.nan,
                    "hospital_mortality_rate": np.nan,
                    "early_anemia_rate": np.nan,
                    "silhouette": np.nan,
                    "ari_vs_primary_log_pca": np.nan,
                    "min_cluster_n": np.nan,
                    "min_cluster_frac": np.nan,
                    "max_feature_missing_rate": np.nan,
                    "note": f"Missing features: {missing_features}",
                }
            )
            continue

        _, _, x_scaled_sens, _, _, missing_summary = preprocess_feature_matrix(df, features)
        model = KMeans(n_clusters=PRIMARY_K, random_state=RANDOM_SEED, n_init=100)
        raw_labels = model.fit_predict(x_scaled_sens)
        _, label_map = build_ordered_phenotype_labels(x_scaled_sens, raw_labels, features=features)
        phenotype = np.array([label_map[int(label)] for label in raw_labels])
        counts = pd.Series(phenotype).value_counts()
        silhouette = float(silhouette_score(x_scaled_sens, phenotype))
        ari = float(adjusted_rand_score(reference, phenotype))

        for pheno in sorted(np.unique(phenotype)):
            mask = phenotype == pheno
            rows.append(
                {
                    "cohort_flag": COHORT_FLAG,
                    "feature_set": feature_set_name,
                    "features": ",".join(features),
                    "phenotype": int(pheno),
                    "phenotype_n": int(mask.sum()),
                    "hospital_deaths": int((df.loc[mask, "hospital_mortality"] == 1).sum()),
                    "hospital_mortality_rate": float(df.loc[mask, "hospital_mortality"].mean()),
                    "early_anemia_rate": float(df.loc[mask, "early_anemia_all"].mean()),
                    "silhouette": silhouette,
                    "ari_vs_primary_log_pca": ari,
                    "min_cluster_n": int(counts.min()),
                    "min_cluster_frac": float(counts.min() / len(df)),
                    "max_feature_missing_rate": float(missing_summary["missing_rate"].max()),
                    "note": "Exploratory only; ePVS is highly related to hemoglobin/hematocrit and should not be added to the main 8-variable solution without clinical justification.",
                }
            )

    return pd.DataFrame(rows).sort_values(["feature_set", "phenotype"])


def run_log_pca_kmeans_sensitivity(df: pd.DataFrame, reference_assignments: pd.DataFrame):
    """Primary log1p(creatinine/INR) + PCA + K-means K=3 analysis."""
    (
        _x_raw,
        _x_transformed,
        x_scaled,
        pc_scores,
        pc_columns,
        pca,
        _imputer,
        _scaler,
        missing_summary,
    ) = preprocess_log_pca_feature_matrix(df)

    model = KMeans(n_clusters=PRIMARY_K, random_state=RANDOM_SEED, n_init=100)
    raw_labels = model.fit_predict(pc_scores)
    centers, label_map = build_ordered_phenotype_labels(x_scaled, raw_labels, features=FEATURES)
    assignments = build_assignments(df, raw_labels, label_map)
    assignments["phenotype_solution"] = "log_pca_kmeans_k3"

    phenotype = assignments["phenotype"].astype(int).to_numpy()
    reference = reference_assignments["phenotype"].astype(int).to_numpy()
    ari = float(adjusted_rand_score(reference, phenotype))
    silhouette = float(silhouette_score(pc_scores, phenotype))
    counts = assignments["phenotype"].value_counts()

    explained = pca.explained_variance_ratio_
    summary_rows = []
    for phenotype_id, group in assignments.groupby("phenotype"):
        row = {
            "cohort_flag": COHORT_FLAG,
            "analysis": "log1p_creatinine_inr_pca_kmeans_k3",
            "phenotype": int(phenotype_id),
            "n": int(len(group)),
            "hospital_deaths": int((group["hospital_mortality"] == 1).sum()),
            "hospital_mortality_rate": float(group["hospital_mortality"].mean()),
            "early_anemia_rate": float(group["early_anemia_all"].mean()),
            "silhouette_pc_space": silhouette,
            "ari_vs_raw_8d_kmeans_reference": ari,
            "min_cluster_n": int(counts.min()),
            "min_cluster_frac": float(counts.min() / len(assignments)),
            "pca_n_components": int(len(pc_columns)),
            "pca_explained_variance_total": float(explained.sum()),
            "max_feature_missing_rate": float(missing_summary["missing_rate"].max()),
        }
        for i, ratio in enumerate(explained, start=1):
            row[f"pc{i}_explained_variance"] = float(ratio)
        for feature in FEATURES:
            row[f"{feature}_median"] = float(group[feature].median())
            row[f"{feature}_q1"] = float(group[feature].quantile(0.25))
            row[f"{feature}_q3"] = float(group[feature].quantile(0.75))
        summary_rows.append(row)

    loadings_rows = []
    for pc_index, pc_name in enumerate(pc_columns):
        for feature_index, feature in enumerate(FEATURES):
            loadings_rows.append(
                {
                    "cohort_flag": COHORT_FLAG,
                    "analysis": "log1p_creatinine_inr_pca_kmeans_k3",
                    "principal_component": pc_name,
                    "feature": feature,
                    "loading": float(pca.components_[pc_index, feature_index]),
                    "explained_variance_ratio": float(explained[pc_index]),
                    "transform": "log1p" if feature in LOG_TRANSFORM_FEATURES else "none",
                }
            )

    centers["phenotype_solution"] = "log_pca_kmeans_k3"
    summary = pd.DataFrame(summary_rows).sort_values("phenotype")
    loadings = pd.DataFrame(loadings_rows).sort_values(["principal_component", "feature"])
    return {
        "assignments": assignments,
        "model": model,
        "raw_labels": raw_labels,
        "summary": summary,
        "centers": centers,
        "loadings": loadings,
        "pc_scores": pc_scores,
        "x_scaled": x_scaled,
        "pc_columns": pc_columns,
        "pca": pca,
        "missing_summary": missing_summary,
    }


def normalized_classification_entropy(probabilities: np.ndarray) -> float:
    """Return 0-1 normalized mixture-model classification entropy."""
    if probabilities.size == 0 or probabilities.shape[1] <= 1:
        return np.nan
    clipped = np.clip(probabilities, 1e-12, 1.0)
    uncertainty = -np.sum(clipped * np.log(clipped))
    max_uncertainty = probabilities.shape[0] * np.log(probabilities.shape[1])
    return float(1 - uncertainty / max_uncertainty) if max_uncertainty else np.nan


def run_lpa_gmm_sensitivity(df: pd.DataFrame, primary_assignments: pd.DataFrame):
    """Model-based LPA/GMM sensitivity in the same log-PCA score space as the primary solution."""
    (
        _x_raw,
        _x_transformed,
        x_scaled,
        pc_scores,
        pc_columns,
        pca,
        _imputer,
        _scaler,
        missing_summary,
    ) = preprocess_log_pca_feature_matrix(df)

    models: dict[tuple[str, int], GaussianMixture] = {}
    fit_rows = []
    previous_by_covariance: dict[str, dict[str, float]] = {}
    n = int(pc_scores.shape[0])
    n_dimensions = int(pc_scores.shape[1])

    for covariance_type in ["diag", "full"]:
        for k in range(K_MIN, K_MAX + 1):
            if k >= n:
                continue
            model = GaussianMixture(
                n_components=k,
                covariance_type=covariance_type,
                random_state=RANDOM_SEED,
                n_init=20,
                max_iter=500,
                reg_covar=1e-6,
            )
            raw_labels = model.fit_predict(pc_scores)
            probabilities = model.predict_proba(pc_scores)
            counts = np.bincount(raw_labels, minlength=k)
            entropy = normalized_classification_entropy(probabilities)
            log_likelihood = float(model.score(pc_scores) * n)
            n_parameters = int(model._n_parameters())
            previous = previous_by_covariance.get(covariance_type)
            if previous:
                lrt_stat = max(0.0, 2 * (log_likelihood - previous["log_likelihood"]))
                lrt_df = max(1, n_parameters - int(previous["n_parameters"]))
                lrt_p = float(stats.chi2.sf(lrt_stat, lrt_df))
            else:
                lrt_stat = np.nan
                lrt_df = np.nan
                lrt_p = np.nan
            previous_by_covariance[covariance_type] = {
                "log_likelihood": log_likelihood,
                "n_parameters": float(n_parameters),
            }
            models[(covariance_type, k)] = model
            fit_rows.append(
                {
                    "cohort_flag": COHORT_FLAG,
                    "analysis": "lpa_gmm_log_pca_sensitivity",
                    "input_space": "log1p(creatinine/inr)+zscore+pca_scores",
                    "covariance_type": covariance_type,
                    "k": int(k),
                    "n": n,
                    "n_dimensions": n_dimensions,
                    "converged": bool(model.converged_),
                    "n_iter": int(model.n_iter_),
                    "log_likelihood": log_likelihood,
                    "n_parameters": n_parameters,
                    "bic": float(model.bic(pc_scores)),
                    "aic": float(model.aic(pc_scores)),
                    "entropy": entropy,
                    "silhouette_pc_space": float(silhouette_score(pc_scores, raw_labels)) if k > 1 else np.nan,
                    "min_cluster_n": int(counts.min()),
                    "min_cluster_frac": float(counts.min() / n),
                    "max_cluster_n": int(counts.max()),
                    "max_cluster_frac": float(counts.max() / n),
                    "lrt_vs_k_minus_1_stat": lrt_stat,
                    "lrt_vs_k_minus_1_df_approx": lrt_df,
                    "lrt_vs_k_minus_1_p_value_approx": lrt_p,
                    "note": "GaussianMixture is used as a Python LPA approximation in the primary log-PCA score space; likelihood-ratio p values are descriptive chi-square approximations, not LMR-adjusted tests.",
                }
            )

    fit_indices = pd.DataFrame(fit_rows)
    best_row = fit_indices.sort_values(["bic", "aic"]).iloc[0]
    k3_candidates = fit_indices[fit_indices["k"] == PRIMARY_K].sort_values(["bic", "aic"])
    selected_row = k3_candidates.iloc[0] if not k3_candidates.empty else best_row
    selected_covariance = str(selected_row["covariance_type"])
    selected_k = int(selected_row["k"])
    selected_model = models[(selected_covariance, selected_k)]
    raw_labels = selected_model.predict(pc_scores)
    probabilities = selected_model.predict_proba(pc_scores)
    centers, label_map = build_ordered_phenotype_labels(x_scaled, raw_labels, features=FEATURES)
    assignments = build_assignments(df, raw_labels, label_map)
    assignments["phenotype_solution"] = "lpa_gmm_log_pca_k3_sensitivity"
    assignments["lpa_covariance_type"] = selected_covariance
    assignments["lpa_selected_k"] = selected_k
    assignments["lpa_posterior_max"] = probabilities.max(axis=1)
    assignments["lpa_classification_uncertainty"] = 1 - assignments["lpa_posterior_max"]
    for component_idx in range(probabilities.shape[1]):
        phenotype_id = label_map[int(component_idx)]
        assignments[f"lpa_posterior_phenotype_{phenotype_id}"] = probabilities[:, component_idx]
    centers["phenotype_solution"] = "lpa_gmm_log_pca_k3_sensitivity"
    centers["lpa_covariance_type"] = selected_covariance

    phenotype = assignments["phenotype"].astype(int).to_numpy()
    reference = primary_assignments["phenotype"].astype(int).to_numpy()
    ari_vs_primary = float(adjusted_rand_score(reference, phenotype))
    same_label_rate = float(np.mean(reference == phenotype))
    selected_counts = assignments["phenotype"].value_counts()
    selected_entropy = normalized_classification_entropy(probabilities)
    best_k = int(best_row["k"])
    best_covariance = str(best_row["covariance_type"])
    upgrade_candidate = bool(
        best_k == PRIMARY_K
        and selected_entropy >= 0.80
        and ari_vs_primary >= 0.70
        and float(selected_counts.min() / len(assignments)) >= 0.05
    )

    fit_indices["best_bic_model"] = (
        (fit_indices["k"] == best_k)
        & (fit_indices["covariance_type"].astype(str) == best_covariance)
    )
    fit_indices["selected_k3_model"] = (
        (fit_indices["k"] == selected_k)
        & (fit_indices["covariance_type"].astype(str) == selected_covariance)
    )
    fit_indices["ari_vs_primary_log_pca_kmeans"] = np.where(
        fit_indices["selected_k3_model"],
        ari_vs_primary,
        np.nan,
    )
    fit_indices["same_ordered_label_rate_vs_primary"] = np.where(
        fit_indices["selected_k3_model"],
        same_label_rate,
        np.nan,
    )
    fit_indices["upgrade_to_primary_candidate"] = np.where(
        fit_indices["selected_k3_model"],
        upgrade_candidate,
        False,
    )
    fit_indices["upgrade_rule"] = (
        "Only consider LPA/GMM as primary if best BIC supports K=3, entropy>=0.80, "
        "ARI vs primary log-PCA K-means>=0.70, and minimum phenotype fraction>=0.05."
    )

    outcome_summary = build_outcome_summary(assignments)
    outcome_summary["phenotype_solution"] = "lpa_gmm_log_pca_k3_sensitivity"
    outcome_summary["lpa_covariance_type"] = selected_covariance
    outcome_summary["entropy"] = selected_entropy
    outcome_summary["ari_vs_primary_log_pca_kmeans"] = ari_vs_primary
    outcome_summary["same_ordered_label_rate_vs_primary"] = same_label_rate
    outcome_summary["best_bic_k"] = best_k
    outcome_summary["best_bic_covariance_type"] = best_covariance
    outcome_summary["upgrade_to_primary_candidate"] = upgrade_candidate
    outcome_summary["note"] = (
        "Sensitivity analysis only unless the prespecified upgrade rule is satisfied; "
        "clinical reporting should still use raw phenotype medians/IQRs."
    )
    severity_validation = build_external_severity_validation(assignments)

    return {
        "fit_indices": fit_indices.sort_values(["covariance_type", "k"]),
        "assignments": assignments,
        "outcome_summary": outcome_summary,
        "centers": centers,
        "severity_validation": severity_validation,
        "selected_covariance": selected_covariance,
        "selected_k": selected_k,
        "best_k": best_k,
        "best_covariance": best_covariance,
        "upgrade_to_primary_candidate": upgrade_candidate,
    }


def strict_aneurysm_evidence_mask(df: pd.DataFrame) -> pd.Series:
    """High-specificity aneurysm evidence subgroup for etiology sensitivity analysis."""
    evidence_level = pd.to_numeric(df["nsah_evidence_level"], errors="coerce").fillna(0)
    if "has_ruptured_aneurysmal_sah_evidence" in df:
        has_dx = pd.to_numeric(df["has_ruptured_aneurysmal_sah_evidence"], errors="coerce").fillna(0)
    else:
        has_dx = pd.to_numeric(df["has_aneurysm_dx"], errors="coerce").fillna(0)
    has_procedure = pd.to_numeric(df["has_aneurysm_procedure"], errors="coerce").fillna(0)
    return (evidence_level >= 2) | (has_dx == 1) | (has_procedure == 1)


def run_strict_aneurysm_subgroup_analysis(df: pd.DataFrame, primary_assignments: pd.DataFrame):
    """Re-run the primary log-PCA K=3 workflow in the aneurysm-evidence subgroup."""
    strict_definition = "nsah_evidence_level>=2 OR has_ruptured_aneurysmal_sah_evidence=1 OR has_aneurysm_procedure=1"
    strict_df = df.loc[strict_aneurysm_evidence_mask(df)].copy()
    if len(strict_df) < PRIMARY_K * 20:
        note = (
            "Strict aneurysm-evidence subgroup is too small for a stable K=3 re-clustering; "
            f"definition: {strict_definition}."
        )
        placeholder = pd.DataFrame(
            [
                {
                    "cohort_flag": COHORT_FLAG,
                    "analysis": "strict_aneurysm_evidence_log_pca_kmeans_k3",
                    "strict_definition": strict_definition,
                    "n": int(len(strict_df)),
                    "phenotype": np.nan,
                    "phenotype_n": np.nan,
                    "hospital_deaths": np.nan,
                    "hospital_mortality_rate": np.nan,
                    "note": note,
                }
            ]
        )
        return {
            "assignments": pd.DataFrame(columns=ASSIGNMENT_COLUMNS),
            "summary": placeholder,
            "centers": pd.DataFrame(),
            "outcomes": pd.DataFrame(),
            "severity_validation": pd.DataFrame(),
            "regression": pd.DataFrame(),
            "severity_score_adjusted_models": pd.DataFrame(),
        }

    (
        _x_raw,
        _x_transformed,
        x_scaled,
        pc_scores,
        pc_columns,
        pca,
        _imputer,
        _scaler,
        missing_summary,
    ) = preprocess_log_pca_feature_matrix(strict_df)

    model = KMeans(n_clusters=PRIMARY_K, random_state=RANDOM_SEED, n_init=100)
    raw_labels = model.fit_predict(pc_scores)
    centers, label_map = build_ordered_phenotype_labels(x_scaled, raw_labels, features=FEATURES)
    assignments = build_assignments(strict_df, raw_labels, label_map)
    solution_label = "strict_aneurysm_evidence_log_pca_kmeans_k3"
    strict_solution = assemble_phenotype_solution(assignments, centers, raw_labels, pc_scores, PRIMARY_K, solution_label)

    assignments = strict_solution["assignments"]
    merged_reference = assignments[["stay_id", "phenotype"]].merge(
        primary_assignments[["stay_id", "phenotype"]].rename(columns={"phenotype": "primary_phenotype"}),
        on="stay_id",
        how="inner",
    )
    if len(merged_reference) and merged_reference["phenotype"].nunique() > 1 and merged_reference["primary_phenotype"].nunique() > 1:
        ari_vs_primary = float(adjusted_rand_score(merged_reference["primary_phenotype"], merged_reference["phenotype"]))
        same_label_rate = float((merged_reference["primary_phenotype"] == merged_reference["phenotype"]).mean())
    else:
        ari_vs_primary = np.nan
        same_label_rate = np.nan

    phenotype = assignments["phenotype"].astype(int).to_numpy()
    silhouette = float(silhouette_score(pc_scores, phenotype))
    counts = assignments["phenotype"].value_counts()
    explained = pca.explained_variance_ratio_
    n_total = int(len(df))
    n_strict = int(len(assignments))
    evidence_level = pd.to_numeric(assignments["nsah_evidence_level"], errors="coerce")

    summary_rows = []
    for phenotype_id, group in assignments.groupby("phenotype"):
        row = {
            "cohort_flag": COHORT_FLAG,
            "analysis": solution_label,
            "strict_definition": strict_definition,
            "phenotype": int(phenotype_id),
            "n": int(len(group)),
            "phenotype_n": int(len(group)),
            "strict_subgroup_n": n_strict,
            "strict_subgroup_frac_of_primary": float(n_strict / n_total) if n_total else np.nan,
            "aneurysm_dx_n": int((pd.to_numeric(assignments["has_aneurysm_dx"], errors="coerce") == 1).sum()),
            "aneurysm_procedure_n": int((pd.to_numeric(assignments["has_aneurysm_procedure"], errors="coerce") == 1).sum()),
            "evidence_level_2_n": int((evidence_level == 2).sum()),
            "evidence_level_3_n": int((evidence_level == 3).sum()),
            "hospital_deaths": int((group["hospital_mortality"] == 1).sum()),
            "hospital_mortality_rate": float(group["hospital_mortality"].mean()),
            "early_anemia_rate": float(group["early_anemia_all"].mean()),
            "silhouette_pc_space": silhouette,
            "ari_vs_primary_subset": ari_vs_primary,
            "same_ordered_label_rate_vs_primary_subset": same_label_rate,
            "min_cluster_n": int(counts.min()),
            "min_cluster_frac": float(counts.min() / n_strict),
            "pca_n_components": int(len(pc_columns)),
            "pca_explained_variance_total": float(explained.sum()),
            "max_feature_missing_rate": float(missing_summary["missing_rate"].max()),
            "note": "High-specificity aneurysm evidence subgroup; used as etiology sensitivity analysis, not as the primary real-world non-traumatic SAH cohort.",
        }
        for i, ratio in enumerate(explained, start=1):
            row[f"pc{i}_explained_variance"] = float(ratio)
        for feature in FEATURES:
            row[f"{feature}_median"] = float(group[feature].median())
            row[f"{feature}_q1"] = float(group[feature].quantile(0.25))
            row[f"{feature}_q3"] = float(group[feature].quantile(0.75))
        summary_rows.append(row)

    summary = pd.DataFrame(summary_rows).sort_values("phenotype")
    severity_validation = build_external_severity_validation(assignments)
    regression = run_adjusted_regression(assignments)
    severity_score_adjusted_models = run_severity_score_adjusted_models(assignments)

    return {
        "assignments": assignments,
        "summary": summary,
        "centers": strict_solution["centers"],
        "outcomes": strict_solution["outcome_summary"],
        "severity_validation": severity_validation,
        "regression": regression,
        "severity_score_adjusted_models": severity_score_adjusted_models,
        "pc_scores": pc_scores,
        "x_scaled": x_scaled,
        "pca": pca,
    }


def plot_k_metrics(metrics: pd.DataFrame) -> None:
    """画 K 选择指标图。"""
    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    axes = axes.ravel()
    specs = [
        ("inertia", "Elbow: inertia"),
        ("silhouette", "Silhouette"),
        ("calinski_harabasz", "Calinski-Harabasz"),
        ("davies_bouldin", "Davies-Bouldin"),
    ]
    for ax, (col, title) in zip(axes, specs):
        ax.plot(metrics["k"], metrics[col], marker="o")
        ax.set_xlabel("K")
        ax.set_ylabel(col)
        ax.set_title(title)
        ax.grid(alpha=0.25)
    fig.tight_layout()
    show_or_close_current_figure()


def plot_cluster_centers(centers: pd.DataFrame) -> None:
    """画标准化 cluster center 热图。"""
    matrix = centers.set_index("phenotype")[FEATURES]
    fig, ax = plt.subplots(figsize=(11, 5))
    im = ax.imshow(matrix.to_numpy(), aspect="auto", cmap="coolwarm", vmin=-2, vmax=2)
    ax.set_yticks(np.arange(len(matrix.index)))
    ax.set_yticklabels([f"Phenotype {int(x)}" for x in matrix.index])
    ax.set_xticks(np.arange(len(FEATURES)))
    ax.set_xticklabels([FEATURE_LABELS[col] for col in FEATURES], rotation=35, ha="right")
    ax.set_title("Standardized phenotype centers")
    fig.colorbar(im, ax=ax, label="Z-score")
    fig.tight_layout()
    show_or_close_current_figure()


def plot_anemia_mortality(assignments: pd.DataFrame) -> None:
    """画不同 phenotype 内贫血/非贫血死亡率。"""
    summary = (
        assignments.groupby(["phenotype", "early_anemia_all"])["hospital_mortality"]
        .mean()
        .reset_index()
    )
    phenotypes = sorted(summary["phenotype"].unique())
    x = np.arange(len(phenotypes))
    width = 0.36

    fig, ax = plt.subplots(figsize=(9, 5))
    for offset, anemia_value, label in [(-width / 2, 0, "No anemia"), (width / 2, 1, "Anemia")]:
        values = []
        for phenotype in phenotypes:
            matched = summary[
                (summary["phenotype"] == phenotype)
                & (summary["early_anemia_all"] == anemia_value)
            ]
            values.append(float(matched["hospital_mortality"].iloc[0]) if not matched.empty else np.nan)
        ax.bar(x + offset, values, width=width, label=label)
    ax.set_xticks(x)
    ax.set_xticklabels([f"P{int(p)}" for p in phenotypes])
    ax.set_ylabel("Hospital mortality")
    ax.set_title("Mortality by phenotype and early anemia")
    ax.legend()
    fig.tight_layout()
    show_or_close_current_figure()


def wilson_ci(events: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson 95% CI for a binomial proportion."""
    if n <= 0:
        return np.nan, np.nan
    p = events / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half_width = z * np.sqrt((p * (1 - p) + z**2 / (4 * n)) / n) / denom
    return max(0, centre - half_width), min(1, centre + half_width)


def plot_phenotype_mortality(outcome_summary: pd.DataFrame, title_suffix: str = "") -> None:
    """画 phenotype 住院死亡率，并标注样本量和 Wilson 95% CI。"""
    summary = outcome_summary.sort_values("phenotype").copy()
    phenotypes = summary["phenotype"].astype(int).to_numpy()
    rates = summary["hospital_mortality_rate"].to_numpy(dtype=float)
    ci = np.array(
        [
            wilson_ci(int(row["hospital_deaths"]), int(row["n"]))
            for _, row in summary.iterrows()
        ]
    )
    yerr = np.vstack([rates - ci[:, 0], ci[:, 1] - rates])

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar([f"P{p}" for p in phenotypes], rates, yerr=yerr, capsize=5, color="#4C78A8")
    ax.set_ylim(0, min(1.0, max(0.15, float(np.nanmax(ci[:, 1])) + 0.08)))
    ax.set_ylabel("Hospital mortality")
    ax.set_title(f"Hospital mortality by phenotype{title_suffix}")
    ax.grid(axis="y", alpha=0.2)
    for bar, n in zip(bars, summary["n"]):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.015,
            f"n={int(n)}",
            ha="center",
            va="bottom",
            fontsize=9,
        )
    fig.tight_layout()
    show_or_close_current_figure()


def plot_k3_k4_refinement_crosstab(crosstab: pd.DataFrame) -> None:
    """画 K=3 主分型与 K=4 高分辨率分型的交叉热图。"""
    if crosstab.empty:
        return
    count_matrix = crosstab.pivot(index="phenotype_k3", columns="phenotype_k4", values="n").fillna(0)
    frac_matrix = crosstab.pivot(index="phenotype_k3", columns="phenotype_k4", values="frac_within_k3").fillna(0)
    mortality_matrix = crosstab.pivot(
        index="phenotype_k3",
        columns="phenotype_k4",
        values="hospital_mortality_rate",
    ).fillna(np.nan)

    fig, ax = plt.subplots(figsize=(8, 5))
    im = ax.imshow(frac_matrix.to_numpy(), aspect="auto", cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(np.arange(len(count_matrix.columns)))
    ax.set_xticklabels([f"K4 P{int(col)}" for col in count_matrix.columns])
    ax.set_yticks(np.arange(len(count_matrix.index)))
    ax.set_yticklabels([f"K3 P{int(row)}" for row in count_matrix.index])
    ax.set_xlabel("Exploratory K=4 phenotype")
    ax.set_ylabel("Primary K=3 phenotype")
    ax.set_title("K=3 to K=4 refinement map")
    for i, k3 in enumerate(count_matrix.index):
        for j, k4 in enumerate(count_matrix.columns):
            n = int(count_matrix.loc[k3, k4])
            if n == 0:
                continue
            frac = frac_matrix.loc[k3, k4] * 100
            mortality = mortality_matrix.loc[k3, k4] * 100
            ax.text(j, i, f"n={n}\n{frac:.1f}%\nMort {mortality:.1f}%", ha="center", va="center", fontsize=9)
    fig.colorbar(im, ax=ax, label="Fraction within K=3 phenotype")
    fig.tight_layout()
    show_or_close_current_figure()


def plot_bootstrap_stability(bootstrap_stability: pd.DataFrame) -> None:
    """画 bootstrap ARI 与最小 cluster size 分布。"""
    if bootstrap_stability.empty:
        return
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    axes[0].hist(bootstrap_stability["adjusted_rand_index_vs_primary"], bins=20, color="#59A14F", alpha=0.85)
    axes[0].axvline(bootstrap_stability["adjusted_rand_index_vs_primary"].median(), color="black", linestyle="--")
    axes[0].set_xlabel("ARI vs primary K=3")
    axes[0].set_ylabel("Bootstrap iterations")
    axes[0].set_title("Bootstrap assignment stability")
    axes[0].grid(axis="y", alpha=0.2)

    axes[1].hist(bootstrap_stability["min_cluster_n"], bins=20, color="#F28E2B", alpha=0.85)
    axes[1].axvline(bootstrap_stability["min_cluster_n"].median(), color="black", linestyle="--")
    axes[1].set_xlabel("Minimum cluster size")
    axes[1].set_ylabel("Bootstrap iterations")
    axes[1].set_title("Bootstrap minimum phenotype size")
    axes[1].grid(axis="y", alpha=0.2)
    fig.tight_layout()
    show_or_close_current_figure()


def plot_candidate_feature_missingness(candidate_feature_audit: pd.DataFrame) -> None:
    """画候选增强变量缺失率，用于判断是否能进入敏感性分析。"""
    if candidate_feature_audit.empty:
        return
    audit = candidate_feature_audit.sort_values("missing_rate")
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(audit["feature"], audit["missing_rate"], color="#B07AA1")
    ax.axvline(0.2, color="black", linestyle="--", linewidth=1, label="20%")
    ax.axvline(0.4, color="black", linestyle=":", linewidth=1, label="40%")
    ax.set_xlim(0, 1)
    ax.set_xlabel("Missing rate")
    ax.set_title("Candidate feature missingness audit")
    ax.legend()
    fig.tight_layout()
    show_or_close_current_figure()


def plot_prediction_metrics(prediction_metrics: pd.DataFrame) -> None:
    """画死亡预测模型的 AUROC 和 Brier score 比较。"""
    if prediction_metrics.empty:
        return
    metrics = prediction_metrics.sort_values("auroc", ascending=False)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    axes[0].bar(metrics["model"], metrics["auroc"], color="#4C78A8")
    axes[0].set_ylim(0.5, min(1.0, max(0.7, float(metrics["auroc"].max()) + 0.05)))
    axes[0].set_ylabel("AUROC")
    axes[0].set_title("Discrimination")
    axes[0].tick_params(axis="x", rotation=25)
    axes[0].grid(axis="y", alpha=0.2)

    axes[1].bar(metrics["model"], metrics["brier_score"], color="#E15759")
    axes[1].set_ylabel("Brier score")
    axes[1].set_title("Overall prediction error")
    axes[1].tick_params(axis="x", rotation=25)
    axes[1].grid(axis="y", alpha=0.2)
    fig.tight_layout()
    show_or_close_current_figure()


def plot_survival_km(km_curve: pd.DataFrame) -> None:
    """Plot in-hospital Kaplan-Meier survival curves by phenotype."""
    if km_curve.empty:
        return
    fig, ax = plt.subplots(figsize=(8, 5))
    for phenotype, group in km_curve.groupby("phenotype"):
        group = group.sort_values("time_days")
        ax.step(
            group["time_days"].astype(float),
            group["survival_probability"].astype(float),
            where="post",
            linewidth=2,
            label=f"P{int(phenotype)}",
        )
    ax.set_xlabel("Hospital day")
    ax.set_ylabel("Survival probability")
    ax.set_ylim(0, 1.02)
    ax.set_title("In-hospital Kaplan-Meier survival by phenotype")
    ax.grid(alpha=0.2)
    ax.legend(title="Phenotype")
    fig.tight_layout()
    show_or_close_current_figure()


def plot_feature_heatmap(feature_heatmap: pd.DataFrame) -> None:
    """Plot phenotype heatmap with raw median labels."""
    if feature_heatmap.empty:
        return
    matrix = feature_heatmap.pivot(index="phenotype", columns="feature", values="z_center")
    labels = feature_heatmap.pivot(index="phenotype", columns="feature", values="display_value")
    matrix = matrix[FEATURES]
    labels = labels[FEATURES]

    fig, ax = plt.subplots(figsize=(12, 5))
    im = ax.imshow(matrix.to_numpy(dtype=float), aspect="auto", cmap="coolwarm", vmin=-2, vmax=2)
    ax.set_yticks(np.arange(len(matrix.index)))
    ax.set_yticklabels([f"P{int(value)}" for value in matrix.index])
    ax.set_xticks(np.arange(len(matrix.columns)))
    ax.set_xticklabels([FEATURE_LABELS.get(col, col) for col in matrix.columns], rotation=35, ha="right")
    ax.set_title("Primary phenotype feature heatmap")
    for i, phenotype in enumerate(matrix.index):
        for j, feature in enumerate(matrix.columns):
            ax.text(j, i, labels.loc[phenotype, feature], ha="center", va="center", fontsize=7)
    fig.colorbar(im, ax=ax, label="Standardized center")
    fig.tight_layout()
    show_or_close_current_figure()


def plot_shap_feature_importance(shap_importance: pd.DataFrame) -> None:
    """Plot SHAP-style mean absolute log-odds contributions."""
    if shap_importance.empty:
        return
    plot_df = shap_importance.sort_values("mean_abs_shap_log_odds", ascending=True)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(plot_df["feature_label"], plot_df["mean_abs_shap_log_odds"], color="#4C78A8")
    ax.set_xlabel("Mean absolute log-odds contribution")
    ax.set_title("Mortality model SHAP-style feature importance")
    ax.grid(axis="x", alpha=0.2)
    fig.tight_layout()
    show_or_close_current_figure()


def plot_external_severity_validation(severity_validation: pd.DataFrame) -> None:
    """Plot established ICU severity scores across ordered phenotypes."""
    if severity_validation.empty:
        return
    plot_df = severity_validation.sort_values(["validation_score", "phenotype"]).copy()
    scores = plot_df["validation_score"].dropna().unique().tolist()
    if not scores:
        return

    n_cols = 2
    n_rows = int(np.ceil(len(scores) / n_cols))
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(11, 4 * n_rows), squeeze=False)
    axes_flat = axes.ravel()

    for ax, score in zip(axes_flat, scores):
        sub = plot_df[plot_df["validation_score"] == score].sort_values("phenotype")
        x = sub["phenotype"].astype(int).to_numpy()
        y = sub["median"].astype(float).to_numpy()
        yerr = np.vstack(
            [
                y - sub["q1"].astype(float).to_numpy(),
                sub["q3"].astype(float).to_numpy() - y,
            ]
        )
        ax.errorbar(x, y, yerr=yerr, marker="o", capsize=4, linewidth=2, color="#4C78A8")
        ax.set_xticks(x)
        ax.set_xticklabels([f"P{int(value)}" for value in x])
        ax.set_ylabel(score)
        rho = sub["spearman_rho_vs_ordered_phenotype"].dropna()
        rho_label = f"rho={rho.iloc[0]:.2f}" if not rho.empty else ""
        ax.set_title(f"{score} by phenotype {rho_label}".strip())
        ax.grid(axis="y", alpha=0.2)

    for ax in axes_flat[len(scores):]:
        ax.axis("off")

    fig.suptitle("External severity score validation", y=1.02)
    fig.tight_layout()
    show_or_close_current_figure()


def plot_severity_score_adjusted_phenotype_or(models: pd.DataFrame) -> None:
    """Forest plot of phenotype ORs after adjustment for ICU severity scores."""
    if models.empty:
        return
    terms = models[models["term"].astype(str).str.startswith("C(phenotype)")].copy()
    if terms.empty:
        return

    model_order = [
        "phenotype_plus_sofa",
        "phenotype_plus_sapsii",
        "phenotype_plus_oasis",
        "phenotype_plus_lods",
        "phenotype_plus_sofa_clinical",
    ]
    terms["model"] = pd.Categorical(terms["model"], categories=model_order, ordered=True)
    terms = terms.sort_values(["model", "term"])
    labels = []
    for _, row in terms.iterrows():
        phenotype_label = "P2 vs P1" if "T.2" in str(row["term"]) else "P3 vs P1"
        labels.append(f"{row['model']}\n{phenotype_label}")

    y_pos = np.arange(len(terms))
    odds = terms["odds_ratio"].astype(float).to_numpy()
    lower = terms["ci_lower"].astype(float).to_numpy()
    upper = terms["ci_upper"].astype(float).to_numpy()
    xerr = np.vstack([odds - lower, upper - odds])

    fig, ax = plt.subplots(figsize=(10, max(5, 0.55 * len(terms))))
    colors = ["#4C78A8" if "T.2" in str(term) else "#E15759" for term in terms["term"]]
    ax.errorbar(odds, y_pos, xerr=xerr, fmt="none", ecolor="0.35", capsize=3, linewidth=1.5)
    ax.scatter(odds, y_pos, color=colors, s=42, zorder=3)
    ax.axvline(1.0, color="black", linestyle="--", linewidth=1)
    ax.set_xscale("log")
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel("Adjusted odds ratio for hospital mortality (log scale)")
    ax.set_title("Phenotype association after severity-score adjustment")
    ax.grid(axis="x", alpha=0.2)
    fig.tight_layout()
    show_or_close_current_figure()


ASSIGNMENT_COLUMNS = [
    "cohort_flag",
    "subject_id",
    "hadm_id",
    "stay_id",
    "raw_cluster",
    "phenotype",
    "phenotype_label",
    "phenotype_solution",
    "hospital_mortality",
    "early_anemia_all",
    "age",
    "gender",
    "race",
    "race_group",
    "admission_type",
    "insurance",
    "nsah_evidence_level",
    "has_aneurysm_dx",
    "has_unruptured_aneurysm_dx",
    "has_ruptured_aneurysmal_sah_dx",
    "has_ruptured_aneurysmal_sah_evidence",
    "has_aneurysm_procedure",
    "icu_los_days",
    "hospital_los_days",
    "icu_mortality",
    "early_anemia_pre_transfusion",
    "any_rbc_transfusion_48h",
    "massive_transfusion_24h",
    "vasopressor_48h",
    "first_vasopressor_time_48h",
    "vasopressor_events_48h",
    "vasopressor_labels_48h",
    "mech_vent_48h",
    "noninvasive_vent_48h",
    "first_mech_vent_time_48h",
    "invasive_vent_events_48h",
    "noninvasive_vent_events_48h",
    "ventilation_labels_48h",
    "evd_or_icp_48h",
    "first_evd_or_icp_time_48h",
    "evd_icp_proc_events_48h",
    "evd_icp_chart_events_48h",
    "evd_icp_proc_labels_48h",
    "evd_icp_chart_labels_48h",
    "crrt_48h",
    "first_crrt_time_48h",
    "crrt_events_48h",
    "crrt_modes_48h",
    "nimodipine_48h",
    "first_nimodipine_time_48h",
    "nimodipine_orders_48h",
    "nimodipine_drugs_48h",
    "nimodipine_routes_48h",
    "aneurysm_securing_hosp",
    "aneurysm_securing_codes_hosp",
    "fluid_input_ml_48h",
    "fluid_output_ml_48h",
    "fluid_input_events_48h",
    "fluid_output_events_48h",
    "fluid_balance_ml_48h",
    "fluid_balance_l_48h",
    "fluid_balance_complete_48h",
    "core_feature_missing_count",
    "core_feature_missing_count_24h",
    "hb_min_48h_all",
    "hb_min_48h_pre_transfusion",
    "hb_min_24h_all",
    "hb_min_24h_pre_transfusion",
    "gcs_min_48h",
    "gcs_grade_min_48h",
    "gcs_grade_min_24h",
    "gcs_motor_min_24h",
    "wfns_gcs_grade_min_48h",
    "epvs_mean_48h",
    "epvs_first_48h",
    "epvs_max_48h",
    "troponin_peak_48h",
    "troponin_peak_m6_48h",
    "troponin_labels_48h",
    "troponin_units_48h",
    "troponin_labels_m6_48h",
    "troponin_units_m6_48h",
    "lactate_max_48h",
    "lactate_max_m6_48h",
    "oxygenation_min_48h",
    "pao2_fio2_min_48h",
    "spo2_fio2_min_48h",
    "sofa_24h",
    "sofa_respiration_24h",
    "sofa_coagulation_24h",
    "sofa_liver_24h",
    "sofa_cardiovascular_24h",
    "sofa_cns_24h",
    "sofa_renal_24h",
    "sapsii_24h",
    "sapsii_prob_24h",
    "apsiii_24h",
    "apsiii_prob_24h",
    "oasis_24h",
    "oasis_prob_24h",
    "lods_24h",
    *FEATURES,
    *FEATURES_24H,
]
ASSIGNMENT_COLUMNS = list(dict.fromkeys(ASSIGNMENT_COLUMNS))


def assemble_phenotype_solution(
    assignments: pd.DataFrame,
    centers: pd.DataFrame,
    raw_labels: np.ndarray,
    clustering_matrix: np.ndarray,
    k: int,
    solution_label: str,
):
    """Build shared downstream tables for a fixed phenotype assignment."""
    assignments = assignments.copy()
    centers = centers.copy()
    assignments["phenotype_solution"] = solution_label
    centers["phenotype_solution"] = solution_label

    feature_summary = build_feature_summary(assignments)
    feature_summary["phenotype_solution"] = solution_label
    outcome_summary = build_outcome_summary(assignments)
    outcome_summary["phenotype_solution"] = solution_label
    anemia_feasibility = build_anemia_feasibility(assignments)
    anemia_feasibility["phenotype_solution"] = solution_label
    tests = run_lightweight_tests(assignments)
    tests["phenotype_solution"] = solution_label
    stability = run_stability_check(clustering_matrix, raw_labels, k)
    stability["phenotype_solution"] = solution_label

    return {
        "raw_labels": raw_labels,
        "centers": centers,
        "assignments": assignments,
        "feature_summary": feature_summary,
        "outcome_summary": outcome_summary,
        "anemia_feasibility": anemia_feasibility,
        "tests": tests,
        "stability": stability,
    }


def run_phenotype_solution(df: pd.DataFrame, x_scaled: np.ndarray, k: int, solution_label: str):
    """Fit one K-means solution and build all downstream summary tables."""
    print(f"\n{solution_label}: K = {k}")
    kmeans_model, raw_labels = fit_final_kmeans(x_scaled, k)
    centers, label_map = build_ordered_phenotype_labels(x_scaled, raw_labels)
    assignments = build_assignments(df, raw_labels, label_map)
    result = assemble_phenotype_solution(assignments, centers, raw_labels, x_scaled, k, solution_label)

    print("\nK-means 原始 cluster 到 phenotype 严重程度排序映射：")
    display(pd.DataFrame({"raw_cluster": list(label_map.keys()), "phenotype": list(label_map.values())}).sort_values("phenotype"))

    print("\n标准化 cluster center：")
    display(result["centers"])
    plot_cluster_centers(result["centers"])

    print("\nPhenotype 结局汇总：")
    display(result["outcome_summary"])
    plot_phenotype_mortality(result["outcome_summary"], title_suffix=f" ({solution_label})")

    print("\nPhenotype x anemia 可行性表：")
    display(result["anemia_feasibility"])
    plot_anemia_mortality(result["assignments"])

    print("\n轻量统计检验：")
    display(result["tests"])

    print("\n聚类稳定性：")
    display(result["stability"])

    result["model"] = kmeans_model
    return result


def build_k3_k4_refinement_crosstab(primary_assignments: pd.DataFrame, exploratory_assignments: pd.DataFrame) -> pd.DataFrame:
    """Compare primary K=3 phenotypes against exploratory K=4 phenotypes."""
    merged = primary_assignments[["stay_id", "phenotype", "hospital_mortality"]].rename(columns={"phenotype": "phenotype_k3"}).merge(
        exploratory_assignments[["stay_id", "phenotype"]].rename(columns={"phenotype": "phenotype_k4"}),
        on="stay_id",
        how="inner",
    )
    rows = []
    for (phenotype_k3, phenotype_k4), group in merged.groupby(["phenotype_k3", "phenotype_k4"]):
        k3_n = int((merged["phenotype_k3"] == phenotype_k3).sum())
        rows.append(
            {
                "cohort_flag": COHORT_FLAG,
                "phenotype_k3": int(phenotype_k3),
                "phenotype_k4": int(phenotype_k4),
                "n": int(len(group)),
                "frac_within_k3": float(len(group) / k3_n) if k3_n else np.nan,
                "hospital_deaths": int((group["hospital_mortality"] == 1).sum()),
                "hospital_mortality_rate": float(group["hospital_mortality"].mean()),
            }
        )
    return pd.DataFrame(rows).sort_values(["phenotype_k3", "phenotype_k4"])


# =============================================================================
# 4. 主流程
# =============================================================================


df = read_table_from_bigquery()
validate_input(df)

print("\n总体样本快速检查：")
display(
    pd.DataFrame(
        [
            {
                "cohort_flag": COHORT_FLAG,
                "n": len(df),
                "hospital_deaths": int((df["hospital_mortality"] == 1).sum()),
                "hospital_mortality_rate": float(df["hospital_mortality"].mean()),
                "early_anemia_n": int((df["early_anemia_all"] == 1).sum()),
                "early_anemia_rate": float(df["early_anemia_all"].mean()),
                "any_rbc_transfusion_48h_rate": float(df["any_rbc_transfusion_48h"].mean()),
            }
        ]
    )
)

x_raw, x_imputed, x_scaled, imputer, scaler, missing_summary = build_feature_matrix(df)

raw_k_metrics = run_k_selection(x_scaled, "raw_standardized_8_variable_kmeans")
plot_k_metrics(raw_k_metrics)

raw_reference = run_phenotype_solution(df, x_scaled, PRIMARY_K, "raw_kmeans_k3_sensitivity")
log_pca_kmeans_sensitivity = run_log_pca_kmeans_sensitivity(df, raw_reference["assignments"])
primary = assemble_phenotype_solution(
    log_pca_kmeans_sensitivity["assignments"],
    log_pca_kmeans_sensitivity["centers"],
    log_pca_kmeans_sensitivity["raw_labels"],
    log_pca_kmeans_sensitivity["pc_scores"],
    PRIMARY_K,
    "primary_log_pca_kmeans_k3",
)

pc_k_metrics = run_k_selection(
    log_pca_kmeans_sensitivity["pc_scores"],
    "primary_log1p_creatinine_inr_pca_kmeans",
)
metrics = pd.concat([pc_k_metrics, raw_k_metrics], ignore_index=True)
write_dataframe(metrics, OUTPUT_TABLES["k_metrics"])
plot_k_metrics(pc_k_metrics)

print("\n主分析：log1p(creatinine/INR) + PCA(3PC) + K-means K=3")
display(log_pca_kmeans_sensitivity["summary"])
print("\n主分析标准化中心：")
display(primary["centers"])
plot_cluster_centers(primary["centers"])
feature_heatmap = build_feature_heatmap_table(primary["assignments"], primary["centers"])
print("\n主分析 feature heatmap 长表：")
display(feature_heatmap)
plot_feature_heatmap(feature_heatmap)
print("\n主分析结局汇总：")
display(primary["outcome_summary"])
plot_phenotype_mortality(primary["outcome_summary"], title_suffix=" (primary log-PCA K=3)")
print("\n主分析 phenotype x anemia 可行性表：")
display(primary["anemia_feasibility"])
plot_anemia_mortality(primary["assignments"])
gcs_motor_distribution = build_gcs_motor_distribution(primary["assignments"])
print("\n主分析 GCS motor 分布审计表：")
display(gcs_motor_distribution)
print("\n主分析聚类稳定性：")
display(primary["stability"])

exploratory = run_phenotype_solution(df, x_scaled, EXPLORATORY_K, "exploratory_k4")
k3_k4_crosstab = build_k3_k4_refinement_crosstab(primary["assignments"], exploratory["assignments"])

print("\nK=3 主分型与 K=4 高分辨率分型交叉表：")
display(k3_k4_crosstab)
plot_k3_k4_refinement_crosstab(k3_k4_crosstab)

raw_bootstrap_stability = run_bootstrap_stability(
    x_scaled,
    raw_reference["assignments"]["phenotype"],
    PRIMARY_K,
)
log_pca_bootstrap_stability = run_log_pca_bootstrap_stability(
    log_pca_kmeans_sensitivity["pc_scores"],
    log_pca_kmeans_sensitivity["x_scaled"],
    primary["assignments"]["phenotype"],
    PRIMARY_K,
)
bootstrap_stability = log_pca_bootstrap_stability
print("\n主分析 log-PCA bootstrap 聚类稳定性汇总：")
display(
    bootstrap_stability[
        ["adjusted_rand_index_vs_primary", "adjusted_rand_index_vs_log_pca", "same_ordered_label_rate", "min_cluster_n"]
    ].describe()
)
plot_bootstrap_stability(bootstrap_stability)

gcs_sensitivity = run_gcs_sensitivity(df, primary["assignments"])
print("\nGCS motor 主方案与 total GCS / GCS grade 替代敏感性分析：")
display(gcs_sensitivity)

external_severity_validation = build_external_severity_validation(primary["assignments"])
print("\nSOFA/SAPS II/OASIS/LODS 外部严重程度验证：")
display(external_severity_validation)
plot_external_severity_validation(external_severity_validation)

candidate_feature_audit = build_candidate_feature_audit(df)
print("\nePVS、troponin、乳酸和血气氧合候选变量审计：")
display(candidate_feature_audit)
plot_candidate_feature_missingness(candidate_feature_audit)

baseline_characteristics = build_baseline_characteristics(primary["assignments"])
print("\n基线特征表：总体与 K=3 phenotype 分层")
display(baseline_characteristics)

process_of_care_audit = build_process_of_care_audit(primary["assignments"])
print("\n过程性治疗和液体平衡审计表：")
display(process_of_care_audit)

prediction_metrics = run_prediction_increment(primary["assignments"])
print("\n死亡预测增量比较：")
display(prediction_metrics)
plot_prediction_metrics(prediction_metrics)

shap_analysis = run_linear_shap_analysis(primary["assignments"])
print("\n死亡预测模型 SHAP-style 特征重要性：")
display(shap_analysis["importance"])
plot_shap_feature_importance(shap_analysis["importance"])
print("\n死亡预测模型 SHAP-style phenotype 内平均贡献：")
display(shap_analysis["phenotype_contributions"])

survival_km_curve = build_km_curve(primary["assignments"])
survival_logrank = run_survival_logrank(primary["assignments"])
survival_cox_models = run_survival_cox_models(primary["assignments"])
print("\n住院期 Kaplan-Meier 生存曲线数据：")
display(survival_km_curve.head(30))
plot_survival_km(survival_km_curve)
print("\n住院期 phenotype pairwise log-rank 检验：")
display(survival_logrank)
print("\n住院期 Cox 模型：")
display(survival_cox_models)

regression_models = run_adjusted_regression(primary["assignments"])
print("\n调整后死亡回归模型：")
display(regression_models)

severity_score_adjusted_models = run_severity_score_adjusted_models(primary["assignments"])
print("\n严重程度评分调整后死亡回归模型：")
display(severity_score_adjusted_models)
plot_severity_score_adjusted_phenotype_or(severity_score_adjusted_models)

process_of_care_adjusted_models = run_process_of_care_adjusted_models(primary["assignments"])
print("\n过程性治疗扩展调整后死亡回归模型：")
display(process_of_care_adjusted_models)

anemia_stratified_models = run_anemia_stratified_regression(primary["assignments"])
print("\n各 K=3 phenotype 内早期贫血调整后死亡模型：")
display(anemia_stratified_models)

sensitivity_cohort_summary = run_sensitivity_cohort_summaries(df, primary["assignments"])
print("\n敏感性子队列 K=3 重新聚类汇总：")
display(sensitivity_cohort_summary)

epvs_sensitivity = run_epvs_sensitivity(df, primary["assignments"])
print("\nePVS 候选增强变量 K=3 敏感性聚类：")
display(epvs_sensitivity)

hb_free_sensitivity = run_hb_free_sensitivity(df, primary["assignments"])
print("\n去除 Hb 后 K=3 敏感性聚类：")
display(hb_free_sensitivity["summary"])
print("\n去除 Hb 后标准化中心：")
display(hb_free_sensitivity["centers"])
hb_free_anemia_regression = run_hb_free_anemia_regression(hb_free_sensitivity["assignments"])
print("\n去除 Hb 后 phenotype 调整的早期贫血死亡回归：")
display(hb_free_anemia_regression)

inr_free_sensitivity = run_inr_free_sensitivity(df, primary["assignments"])
print("\n去除 INR 后 K=3 敏感性聚类：")
display(inr_free_sensitivity["summary"])
print("\n去除 INR 后标准化中心：")
display(inr_free_sensitivity["centers"])

complete_case_sensitivity = run_complete_case_sensitivity(df, primary["assignments"])
print("\n核心 8 变量 complete-case K=3 敏感性聚类：")
display(complete_case_sensitivity["summary"])
print("\nComplete-case 标准化中心：")
display(complete_case_sensitivity["centers"])

log_pca_complete_case_sensitivity = run_log_pca_complete_case_sensitivity(df, primary["assignments"])
print("\nlog-PCA complete-case K=3 敏感性聚类：")
display(log_pca_complete_case_sensitivity["summary"])
print("\nlog-PCA complete-case 标准化中心：")
display(log_pca_complete_case_sensitivity["centers"])

window_24h_sensitivity = run_24h_window_sensitivity(df, primary["assignments"])
print("\n0-24h log-PCA K=3 窗口敏感性聚类：")
display(window_24h_sensitivity["summary"])
print("\n0-24h log-PCA 标准化中心：")
display(window_24h_sensitivity["centers"])

strict_aneurysm_subgroup = run_strict_aneurysm_subgroup_analysis(df, primary["assignments"])
print("\n严格动脉瘤证据亚组 log-PCA K=3 敏感性分析：")
display(strict_aneurysm_subgroup["summary"])
print("\n严格动脉瘤证据亚组结局汇总：")
display(strict_aneurysm_subgroup["outcomes"])
print("\n严格动脉瘤证据亚组严重程度评分验证：")
display(strict_aneurysm_subgroup["severity_validation"])
print("\n严格动脉瘤证据亚组调整后死亡回归：")
display(strict_aneurysm_subgroup["regression"])

lpa_sensitivity = run_lpa_gmm_sensitivity(df, primary["assignments"])
print("\nLPA/GMM model-based clustering 敏感性分析拟合指标：")
display(lpa_sensitivity["fit_indices"])
print("\nLPA/GMM K=3 敏感性分析结局汇总：")
display(lpa_sensitivity["outcome_summary"])
print("\nLPA/GMM K=3 标准化中心：")
display(lpa_sensitivity["centers"])
print("\nLPA/GMM K=3 外部严重程度验证：")
display(lpa_sensitivity["severity_validation"])

print("\nlog-PCA K-means 主分析审计副本：")
display(log_pca_kmeans_sensitivity["summary"])
print("\nlog-PCA loadings：")
display(log_pca_kmeans_sensitivity["loadings"])

# 写回 BigQuery。
write_dataframe(primary["centers"], OUTPUT_TABLES["centers"])
write_dataframe(
    primary["assignments"][ASSIGNMENT_COLUMNS],
    OUTPUT_TABLES["assignments"],
)
write_dataframe(primary["feature_summary"], OUTPUT_TABLES["feature_summary"])
write_dataframe(primary["outcome_summary"], OUTPUT_TABLES["outcome_summary"])
write_dataframe(primary["anemia_feasibility"], OUTPUT_TABLES["anemia_feasibility"])
write_dataframe(gcs_motor_distribution, OUTPUT_TABLES["gcs_motor_distribution"])
write_dataframe(primary["tests"], OUTPUT_TABLES["tests"])
write_dataframe(primary["stability"], OUTPUT_TABLES["stability"])
write_dataframe(bootstrap_stability, OUTPUT_TABLES["bootstrap_stability"])
write_dataframe(gcs_sensitivity, OUTPUT_TABLES["gcs_sensitivity"])
write_dataframe(external_severity_validation, OUTPUT_TABLES["external_severity_validation"])
write_dataframe(candidate_feature_audit, OUTPUT_TABLES["candidate_feature_audit"])
write_dataframe(baseline_characteristics, OUTPUT_TABLES["baseline_characteristics"])
write_dataframe(process_of_care_audit, OUTPUT_TABLES["process_of_care_audit"])
write_dataframe(prediction_metrics, OUTPUT_TABLES["prediction_metrics"])
write_dataframe(shap_analysis["importance"], OUTPUT_TABLES["shap_feature_importance"])
write_dataframe(shap_analysis["phenotype_contributions"], OUTPUT_TABLES["shap_phenotype_contributions"])
write_dataframe(survival_km_curve, OUTPUT_TABLES["survival_km_curve"])
write_dataframe(survival_logrank, OUTPUT_TABLES["survival_logrank"])
write_dataframe(survival_cox_models, OUTPUT_TABLES["survival_cox_models"])
write_dataframe(feature_heatmap, OUTPUT_TABLES["feature_heatmap"])
write_dataframe(regression_models, OUTPUT_TABLES["regression_models"])
write_dataframe(severity_score_adjusted_models, OUTPUT_TABLES["severity_score_adjusted_models"])
write_dataframe(process_of_care_adjusted_models, OUTPUT_TABLES["process_of_care_adjusted_models"])
write_dataframe(anemia_stratified_models, OUTPUT_TABLES["anemia_stratified_models"])
write_dataframe(sensitivity_cohort_summary, OUTPUT_TABLES["sensitivity_cohort_summary"])
write_dataframe(epvs_sensitivity, OUTPUT_TABLES["epvs_sensitivity"])
write_dataframe(hb_free_sensitivity["summary"], OUTPUT_TABLES["hb_free_sensitivity"])
write_dataframe(hb_free_sensitivity["centers"], OUTPUT_TABLES["hb_free_centers"])
write_dataframe(hb_free_anemia_regression, OUTPUT_TABLES["hb_free_anemia_regression"])
write_dataframe(inr_free_sensitivity["summary"], OUTPUT_TABLES["inr_free_sensitivity"])
write_dataframe(inr_free_sensitivity["centers"], OUTPUT_TABLES["inr_free_centers"])
write_dataframe(complete_case_sensitivity["summary"], OUTPUT_TABLES["complete_case_sensitivity"])
write_dataframe(complete_case_sensitivity["centers"], OUTPUT_TABLES["complete_case_centers"])
write_dataframe(log_pca_complete_case_sensitivity["summary"], OUTPUT_TABLES["log_pca_complete_case_sensitivity"])
write_dataframe(log_pca_complete_case_sensitivity["centers"], OUTPUT_TABLES["log_pca_complete_case_centers"])
write_dataframe(window_24h_sensitivity["summary"], OUTPUT_TABLES["window_24h_sensitivity"])
write_dataframe(window_24h_sensitivity["centers"], OUTPUT_TABLES["window_24h_centers"])
write_dataframe(
    strict_aneurysm_subgroup["assignments"][ASSIGNMENT_COLUMNS],
    OUTPUT_TABLES["strict_aneurysm_assignments"],
)
write_dataframe(strict_aneurysm_subgroup["summary"], OUTPUT_TABLES["strict_aneurysm_summary"])
write_dataframe(strict_aneurysm_subgroup["centers"], OUTPUT_TABLES["strict_aneurysm_centers"])
write_dataframe(strict_aneurysm_subgroup["outcomes"], OUTPUT_TABLES["strict_aneurysm_outcomes"])
write_dataframe(strict_aneurysm_subgroup["severity_validation"], OUTPUT_TABLES["strict_aneurysm_severity_validation"])
write_dataframe(strict_aneurysm_subgroup["regression"], OUTPUT_TABLES["strict_aneurysm_regression"])
write_dataframe(
    strict_aneurysm_subgroup["severity_score_adjusted_models"],
    OUTPUT_TABLES["strict_aneurysm_severity_score_adjusted_models"],
)
write_dataframe(lpa_sensitivity["fit_indices"], OUTPUT_TABLES["lpa_fit_indices"])
write_dataframe(lpa_sensitivity["assignments"], OUTPUT_TABLES["lpa_assignments"])
write_dataframe(lpa_sensitivity["outcome_summary"], OUTPUT_TABLES["lpa_outcome_summary"])
write_dataframe(lpa_sensitivity["centers"], OUTPUT_TABLES["lpa_centers"])
write_dataframe(lpa_sensitivity["severity_validation"], OUTPUT_TABLES["lpa_severity_validation"])
write_dataframe(log_pca_kmeans_sensitivity["summary"], OUTPUT_TABLES["log_pca_kmeans_sensitivity"])
write_dataframe(log_pca_kmeans_sensitivity["centers"], OUTPUT_TABLES["log_pca_kmeans_centers"])
write_dataframe(log_pca_kmeans_sensitivity["loadings"], OUTPUT_TABLES["log_pca_kmeans_loadings"])
write_dataframe(log_pca_bootstrap_stability, OUTPUT_TABLES["log_pca_kmeans_bootstrap_stability"])
write_dataframe(raw_reference["centers"], OUTPUT_TABLES["raw_kmeans_centers"])
write_dataframe(
    raw_reference["assignments"][ASSIGNMENT_COLUMNS],
    OUTPUT_TABLES["raw_kmeans_assignments"],
)
write_dataframe(raw_reference["outcome_summary"], OUTPUT_TABLES["raw_kmeans_outcome_summary"])
write_dataframe(raw_bootstrap_stability, OUTPUT_TABLES["raw_kmeans_bootstrap_stability"])

write_dataframe(exploratory["centers"], OUTPUT_TABLES["centers_k4"])
write_dataframe(
    exploratory["assignments"][ASSIGNMENT_COLUMNS],
    OUTPUT_TABLES["assignments_k4"],
)
write_dataframe(exploratory["feature_summary"], OUTPUT_TABLES["feature_summary_k4"])
write_dataframe(exploratory["outcome_summary"], OUTPUT_TABLES["outcome_summary_k4"])
write_dataframe(exploratory["anemia_feasibility"], OUTPUT_TABLES["anemia_feasibility_k4"])
write_dataframe(exploratory["tests"], OUTPUT_TABLES["tests_k4"])
write_dataframe(exploratory["stability"], OUTPUT_TABLES["stability_k4"])
write_dataframe(k3_k4_crosstab, OUTPUT_TABLES["k3_k4_crosstab"])

print("\n分析完成。下一步请重点检查：")
print("1. phenotype_k_selection_metrics：优先查看 primary_log1p_creatinine_inr_pca_kmeans；raw_standardized_8_variable_kmeans 仅作敏感性参照")
print("2. phenotype_outcome_summary：主 log-PCA K=3 是否形成低风险 + 中危 + 多器官/凝血高危表型")
print("3. phenotype_outcome_summary_k4_exploratory：K=4 是否切出小型极高危表型")
print("4. phenotype_raw_kmeans_outcome_summary_sensitivity：原始 8 维 K-means 的死亡梯度是否与主分型方向一致")
print("5. phenotype_anemia_feasibility：K=3 每个 phenotype x anemia 格子的死亡事件数是否足够")
print("6. phenotype_gcs_motor_distribution / phenotype_gcs_sensitivity_summary：GCS motor 的完整分布及替代 GCS 方案是否支持主选择")
print("7. phenotype_bootstrap_stability：主 log-PCA K=3 bootstrap ARI 是否支持 assignment 稳健性")
print("8. phenotype_prediction_metrics：phenotype 是否比 GCS-only 提供预测增量")
print("9. phenotype_shap_feature_importance / phenotype_shap_phenotype_contributions：死亡预测模型的可解释贡献；不解释为聚类因果机制")
print("10. phenotype_survival_km_curve / logrank / cox_models：住院期 time-to-event 分析；活着出院按出院时间删失")
print("11. phenotype_feature_heatmap：主 phenotype 原始中位数[IQR] + 标准化中心热图长表")
print("12. phenotype_process_of_care_audit：Table 1 扩展过程性治疗、专科干预和 fluid balance 覆盖率/分布")
print("13. phenotype_process_of_care_adjusted_models：过程性治疗扩展模型；仅作敏感性调整，不作因果控制")
print("14. phenotype_regression_models：调整年龄、性别、入院类型、aneurysm evidence 和贫血后 phenotype 是否仍有关联；按关联解释，不作因果解释")
print("15. phenotype_severity_score_adjusted_models：加入 SOFA/SAPS II/OASIS/LODS 后 phenotype 是否仍提供增量关联")
print("16. phenotype_candidate_feature_audit：ePVS/troponin 是否适合作敏感性增强变量或仅描述")
print("17. phenotype_baseline_characteristics：总体与 K=3 phenotype 分层基线特征是否平衡、是否可作为 Table 1")
print("18. phenotype_anemia_stratified_models：各 phenotype 内贫血 aOR 是否稳定，稀疏格子仅作探索解释")
print("19. phenotype_sensitivity_cohort_summary：排除 RBC 和 ICU LOS >=48h 后 K=3 结构是否保留")
print("20. phenotype_epvs_sensitivity_summary：加入/替换 ePVS 后 assignment 是否明显改变")
print("21. phenotype_hb_free_sensitivity：去除 Hb 后死亡率和贫血梯度是否仍保留")
print("22. phenotype_hb_free_anemia_regression：用去 Hb 表型调整后 early anemia 是否仍有关联，避免 Hb 循环调整")
print("23. phenotype_inr_free_sensitivity：去除 INR 后几何指标是否改善、凝血表型是否削弱")
print("24. phenotype_complete_case_sensitivity：不用中位数填补时 K=3 结构是否保留")
print("25. phenotype_log_pca_kmeans_sensitivity / loadings：报告前三个 PC 的实际解释方差，不预设达到 85%")
print("26. phenotype_log_pca_complete_case_sensitivity：主 log-PCA 流程在 complete-case 子集是否保留死亡梯度")
print("27. phenotype_24h_window_sensitivity：0-24h 同源核心变量是否支持相近表型结构")
print("28. phenotype_external_severity_validation：SOFA/SAPS II/OASIS/LODS 是否随 phenotype 呈严重程度梯度")
print("29. phenotype_strict_aneurysm_subgroup_*：仅保留动脉瘤诊断或处置证据患者后，死亡梯度和严重程度验证是否仍保留")
print("30. phenotype_lpa_*_sensitivity：LPA/GMM 是否支持 K=3、entropy/ARI/最小类比例是否达到升级主方案标准")
