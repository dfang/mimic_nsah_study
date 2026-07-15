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
#   phenotype_cluster_assignments                  (primary K=3)
#   phenotype_cluster_centers_zscore              (primary K=3)
#   phenotype_feature_summary_raw                 (primary K=3)
#   phenotype_outcome_summary                     (primary K=3)
#   phenotype_anemia_feasibility                  (primary K=3)
#   phenotype_lightweight_tests                   (primary K=3)
#   phenotype_cluster_stability                   (primary K=3)
#   phenotype_bootstrap_stability                 (primary K=3)
#   phenotype_gcs_sensitivity_summary             (primary K=3 sensitivity)
#   phenotype_prediction_metrics                  (mortality prediction increment)
#   phenotype_regression_models                   (adjusted outcome models)
#   phenotype_anemia_stratified_models            (anemia OR within each K=3 phenotype)
#   phenotype_candidate_feature_audit             (ePVS/troponin/blood gas audit)
#   phenotype_baseline_characteristics            (Table 1 baseline by phenotype)
#   phenotype_sensitivity_cohort_summary          (no RBC and ICU LOS >=48h sensitivity)
#   phenotype_epvs_sensitivity_summary            (candidate ePVS clustering sensitivity)
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

# cohort 选择：
#   eligible_primary_analysis: 主分析
#   eligible_no_transfusion_sensitivity: 排除所有 0-48h RBC 输血患者
#   eligible_sensitivity_48h_los: ICU LOS >=48h 敏感性分析
#   eligible_include_massive_transfusion_sensitivity: 不排除 0-24h 大量输血
COHORT_FLAG = "eligible_primary_analysis"
ANALYSIS_SUPERSET_FLAG = "eligible_include_massive_transfusion_sensitivity"

FEATURES = [
    "gcs_motor_min_48h",
    "map_min_48h",
    "shock_index_max_48h",
    "spo2_min_48h",
    "creatinine_max_48h",
    "sodium_max_48h",
    "platelet_min_48h",
]

FEATURE_LABELS = {
    "hb_min_48h_all": "Hb min",
    "gcs_min_48h": "GCS min",
    "gcs_motor_min_48h": "GCS motor min",
    "map_min_48h": "MAP min",
    "shock_index_max_48h": "Shock index max",
    "spo2_min_48h": "SpO2 min",
    "creatinine_max_48h": "Creatinine max",
    "sodium_max_48h": "Sodium max",
    "platelet_min_48h": "Platelet min",
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
    "sodium_max_48h": 1,
    "platelet_min_48h": -1,
    "epvs_mean_48h": 1,
}

GCS_SENSITIVITY_FEATURE_SETS = {
    "primary_gcs_motor": FEATURES,
    "add_total_gcs": [
        "gcs_min_48h",
        "gcs_motor_min_48h",
        "map_min_48h",
        "shock_index_max_48h",
        "spo2_min_48h",
        "creatinine_max_48h",
        "sodium_max_48h",
        "platelet_min_48h",
    ],
    "gcs_total_only": [
        "gcs_min_48h",
        "map_min_48h",
        "shock_index_max_48h",
        "spo2_min_48h",
        "creatinine_max_48h",
        "sodium_max_48h",
        "platelet_min_48h",
    ],
    "gcs_grade_alternative": [
        "gcs_grade_min_48h",
        "map_min_48h",
        "shock_index_max_48h",
        "spo2_min_48h",
        "creatinine_max_48h",
        "sodium_max_48h",
        "platelet_min_48h",
    ],
}

CANDIDATE_AUDIT_FEATURES = [
    "epvs_mean_48h",
    "epvs_first_48h",
    "epvs_max_48h",
    "troponin_peak_48h",
    "lactate_max_48h",
    "pao2_fio2_min_48h",
    "spo2_fio2_min_48h",
    "oxygenation_min_48h",
    "sapsiii_24h",
    "sofa_24h",
]

SENSITIVITY_COHORT_FLAGS = {
    "no_rbc_48h": "eligible_no_transfusion_sensitivity",
    "icu_los_ge_48h": "eligible_sensitivity_48h_los",
    "include_massive_transfusion": "eligible_include_massive_transfusion_sensitivity",
}

EPVS_SENSITIVITY_FEATURE_SETS = {
    "main_7": FEATURES,
    "add_epvs_mean": [*FEATURES, "epvs_mean_48h"],
}

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
    "sapsiii_24h",
    "sofa_24h",
    *FEATURES,
]

BASELINE_CATEGORICAL_FEATURES = [
    "gender",
    "race",
    "admission_type",
    "insurance",
    "nsah_evidence_level",
    "has_aneurysm_dx",
    "has_aneurysm_procedure",
    "early_anemia_all",
    "early_anemia_pre_transfusion",
    "any_rbc_transfusion_48h",
    "massive_transfusion_24h",
]

OUTPUT_TABLES = {
    "k_metrics": f"{PROJECT_ID}.{DATASET_ID}.phenotype_k_selection_metrics",
    "assignments": f"{PROJECT_ID}.{DATASET_ID}.phenotype_cluster_assignments",
    "centers": f"{PROJECT_ID}.{DATASET_ID}.phenotype_cluster_centers_zscore",
    "feature_summary": f"{PROJECT_ID}.{DATASET_ID}.phenotype_feature_summary_raw",
    "outcome_summary": f"{PROJECT_ID}.{DATASET_ID}.phenotype_outcome_summary",
    "anemia_feasibility": f"{PROJECT_ID}.{DATASET_ID}.phenotype_anemia_feasibility",
    "tests": f"{PROJECT_ID}.{DATASET_ID}.phenotype_lightweight_tests",
    "stability": f"{PROJECT_ID}.{DATASET_ID}.phenotype_cluster_stability",
    "bootstrap_stability": f"{PROJECT_ID}.{DATASET_ID}.phenotype_bootstrap_stability",
    "gcs_sensitivity": f"{PROJECT_ID}.{DATASET_ID}.phenotype_gcs_sensitivity_summary",
    "prediction_metrics": f"{PROJECT_ID}.{DATASET_ID}.phenotype_prediction_metrics",
    "regression_models": f"{PROJECT_ID}.{DATASET_ID}.phenotype_regression_models",
    "anemia_stratified_models": f"{PROJECT_ID}.{DATASET_ID}.phenotype_anemia_stratified_models",
    "candidate_feature_audit": f"{PROJECT_ID}.{DATASET_ID}.phenotype_candidate_feature_audit",
    "baseline_characteristics": f"{PROJECT_ID}.{DATASET_ID}.phenotype_baseline_characteristics",
    "sensitivity_cohort_summary": f"{PROJECT_ID}.{DATASET_ID}.phenotype_sensitivity_cohort_summary",
    "epvs_sensitivity": f"{PROJECT_ID}.{DATASET_ID}.phenotype_epvs_sensitivity_summary",
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
    """从 BigQuery 读取覆盖主分析及队列敏感性分析的最小宽表超集。"""
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
        "has_aneurysm_procedure",
        "icu_los_days",
        "hospital_los_days",
        "hospital_mortality",
        "icu_mortality",
        "early_anemia_all",
        "early_anemia_pre_transfusion",
        "any_rbc_transfusion_48h",
        "massive_transfusion_24h",
        "hb_min_48h_all",
        "hb_min_48h_pre_transfusion",
        "core_feature_missing_count",
        "eligible_primary_analysis",
        "eligible_no_transfusion_sensitivity",
        "eligible_sensitivity_48h_los",
        "eligible_include_massive_transfusion_sensitivity",
        "gcs_min_48h",
        "gcs_grade_min_48h",
        "wfns_gcs_grade_min_48h",
        "epvs_mean_48h",
        "epvs_first_48h",
        "epvs_max_48h",
        "troponin_peak_48h",
        "troponin_labels_48h",
        "troponin_units_48h",
        "lactate_max_48h",
        "oxygenation_min_48h",
        "pao2_fio2_min_48h",
        "spo2_fio2_min_48h",
        "sapsiii_24h",
        "sofa_24h",
        *FEATURES,
    ]
    sql = f"""
    SELECT {", ".join(selected_columns)}
    FROM `{INPUT_TABLE}`
    WHERE {ANALYSIS_SUPERSET_FLAG} = 1
    """
    print(f"读取 BigQuery 表：{INPUT_TABLE}")
    print(f"读取 cohort superset flag：{ANALYSIS_SUPERSET_FLAG} = 1")
    df = client.query(sql).to_dataframe(create_bqstorage_client=False)
    print(f"读取完成：{len(df):,} 行，{df.shape[1]} 列")
    return df


def write_dataframe(df: pd.DataFrame, table_id: str) -> None:
    """将 DataFrame 写回 BigQuery，覆盖同名结果表。"""
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


def build_feature_matrix(df: pd.DataFrame):
    """对 7 个低缺失核心聚类变量做中位数填补和 Z-score 标准化。"""
    x_raw, x_imputed, x_scaled, imputer, scaler, missing_summary = preprocess_feature_matrix(df, FEATURES)
    display(missing_summary)
    return x_raw, x_imputed, x_scaled, imputer, scaler, missing_summary


def run_k_selection(x_scaled: np.ndarray) -> pd.DataFrame:
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
    write_dataframe(metrics, OUTPUT_TABLES["k_metrics"])
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
            "ari_vs_primary_gcs_motor": float(adjusted_rand_score(reference, phenotype)),
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
                    "phenotype_solution": "primary_k3",
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
                        "phenotype_solution": "primary_k3",
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
    """比较 GCS-only、7 变量、phenotype、phenotype+贫血+协变量的预测性能。"""
    assignments = assignments.copy()
    assignments["phenotype_factor"] = assignments["phenotype"].map(lambda x: f"P{int(x)}")
    model_specs = {
        "gcs_only": ["gcs_min_48h"],
        "features_7": FEATURES,
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
    """在覆盖预定义队列的宽表超集中分别重新聚类并汇总结局。"""
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
                    "ari_vs_primary_main_7": np.nan,
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
                    "ari_vs_primary_main_7": ari,
                    "min_cluster_n": int(counts.min()),
                    "min_cluster_frac": float(counts.min() / len(df)),
                    "max_feature_missing_rate": float(missing_summary["missing_rate"].max()),
                    "note": "Exploratory only; ePVS is highly related to hemoglobin/hematocrit and should not be added to the main 7-variable solution without clinical justification.",
                }
            )

    return pd.DataFrame(rows).sort_values(["feature_set", "phenotype"])


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


ASSIGNMENT_COLUMNS = [
    "cohort_flag",
    "subject_id",
    "hadm_id",
    "stay_id",
    "raw_cluster",
    "phenotype",
    "phenotype_label",
    "hospital_mortality",
    "early_anemia_all",
    "age",
    "gender",
    "race",
    "admission_type",
    "insurance",
    "nsah_evidence_level",
    "has_aneurysm_dx",
    "has_aneurysm_procedure",
    "icu_los_days",
    "hospital_los_days",
    "icu_mortality",
    "early_anemia_pre_transfusion",
    "any_rbc_transfusion_48h",
    "massive_transfusion_24h",
    "core_feature_missing_count",
    "hb_min_48h_all",
    "hb_min_48h_pre_transfusion",
    "gcs_min_48h",
    "gcs_grade_min_48h",
    "wfns_gcs_grade_min_48h",
    "epvs_mean_48h",
    "epvs_first_48h",
    "epvs_max_48h",
    "troponin_peak_48h",
    "troponin_labels_48h",
    "troponin_units_48h",
    "sapsiii_24h",
    "sofa_24h",
    *FEATURES,
]


def run_phenotype_solution(df: pd.DataFrame, x_scaled: np.ndarray, k: int, solution_label: str):
    """Fit one K-means solution and build all downstream summary tables."""
    print(f"\n{solution_label}: K = {k}")
    kmeans_model, raw_labels = fit_final_kmeans(x_scaled, k)
    centers, label_map = build_ordered_phenotype_labels(x_scaled, raw_labels)
    assignments = build_assignments(df, raw_labels, label_map)
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
    stability = run_stability_check(x_scaled, raw_labels, k)
    stability["phenotype_solution"] = solution_label

    print("\nK-means 原始 cluster 到 phenotype 严重程度排序映射：")
    display(pd.DataFrame({"raw_cluster": list(label_map.keys()), "phenotype": list(label_map.values())}).sort_values("phenotype"))

    print("\n标准化 cluster center：")
    display(centers)
    plot_cluster_centers(centers)

    print("\nPhenotype 结局汇总：")
    display(outcome_summary)
    plot_phenotype_mortality(outcome_summary, title_suffix=f" ({solution_label})")

    print("\nPhenotype x anemia 可行性表：")
    display(anemia_feasibility)
    plot_anemia_mortality(assignments)

    print("\n轻量统计检验：")
    display(tests)

    print("\n聚类稳定性：")
    display(stability)

    return {
        "model": kmeans_model,
        "raw_labels": raw_labels,
        "centers": centers,
        "assignments": assignments,
        "feature_summary": feature_summary,
        "outcome_summary": outcome_summary,
        "anemia_feasibility": anemia_feasibility,
        "tests": tests,
        "stability": stability,
    }


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


analysis_df = read_table_from_bigquery()
df = analysis_df[analysis_df[COHORT_FLAG] == 1].copy()
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

metrics = run_k_selection(x_scaled)
plot_k_metrics(metrics)

primary = run_phenotype_solution(df, x_scaled, PRIMARY_K, "primary_k3")
exploratory = run_phenotype_solution(df, x_scaled, EXPLORATORY_K, "exploratory_k4")
k3_k4_crosstab = build_k3_k4_refinement_crosstab(primary["assignments"], exploratory["assignments"])

print("\nK=3 主分型与 K=4 高分辨率分型交叉表：")
display(k3_k4_crosstab)
plot_k3_k4_refinement_crosstab(k3_k4_crosstab)

bootstrap_stability = run_bootstrap_stability(x_scaled, primary["assignments"]["phenotype"], PRIMARY_K)
print("\nBootstrap 聚类稳定性汇总：")
display(
    bootstrap_stability[
        ["adjusted_rand_index_vs_primary", "same_ordered_label_rate", "min_cluster_n"]
    ].describe()
)
plot_bootstrap_stability(bootstrap_stability)

gcs_sensitivity = run_gcs_sensitivity(df, primary["assignments"])
print("\nGCS motor 主方案与 total GCS / GCS grade 替代敏感性分析：")
display(gcs_sensitivity)

candidate_feature_audit = build_candidate_feature_audit(df)
print("\nePVS、troponin、乳酸和血气氧合候选变量审计：")
display(candidate_feature_audit)
plot_candidate_feature_missingness(candidate_feature_audit)

baseline_characteristics = build_baseline_characteristics(primary["assignments"])
print("\n基线特征表：总体与 K=3 phenotype 分层")
display(baseline_characteristics)

prediction_metrics = run_prediction_increment(primary["assignments"])
print("\n死亡预测增量比较：")
display(prediction_metrics)
plot_prediction_metrics(prediction_metrics)

regression_models = run_adjusted_regression(primary["assignments"])
print("\n调整后死亡回归模型：")
display(regression_models)

anemia_stratified_models = run_anemia_stratified_regression(primary["assignments"])
print("\n各 K=3 phenotype 内早期贫血调整后死亡模型：")
display(anemia_stratified_models)

sensitivity_cohort_summary = run_sensitivity_cohort_summaries(
    analysis_df,
    primary["assignments"],
)
print("\n敏感性子队列 K=3 重新聚类汇总：")
display(sensitivity_cohort_summary)

epvs_sensitivity = run_epvs_sensitivity(df, primary["assignments"])
print("\nePVS 候选增强变量 K=3 敏感性聚类：")
display(epvs_sensitivity)

# 写回 BigQuery。
write_dataframe(primary["centers"], OUTPUT_TABLES["centers"])
write_dataframe(
    primary["assignments"][ASSIGNMENT_COLUMNS],
    OUTPUT_TABLES["assignments"],
)
write_dataframe(primary["feature_summary"], OUTPUT_TABLES["feature_summary"])
write_dataframe(primary["outcome_summary"], OUTPUT_TABLES["outcome_summary"])
write_dataframe(primary["anemia_feasibility"], OUTPUT_TABLES["anemia_feasibility"])
write_dataframe(primary["tests"], OUTPUT_TABLES["tests"])
write_dataframe(primary["stability"], OUTPUT_TABLES["stability"])
write_dataframe(bootstrap_stability, OUTPUT_TABLES["bootstrap_stability"])
write_dataframe(gcs_sensitivity, OUTPUT_TABLES["gcs_sensitivity"])
write_dataframe(candidate_feature_audit, OUTPUT_TABLES["candidate_feature_audit"])
write_dataframe(baseline_characteristics, OUTPUT_TABLES["baseline_characteristics"])
write_dataframe(prediction_metrics, OUTPUT_TABLES["prediction_metrics"])
write_dataframe(regression_models, OUTPUT_TABLES["regression_models"])
write_dataframe(anemia_stratified_models, OUTPUT_TABLES["anemia_stratified_models"])
write_dataframe(sensitivity_cohort_summary, OUTPUT_TABLES["sensitivity_cohort_summary"])
write_dataframe(epvs_sensitivity, OUTPUT_TABLES["epvs_sensitivity"])

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
print("1. phenotype_k_selection_metrics：确认 K=3 比 K=4 更适合作为稳定主分型")
print("2. phenotype_outcome_summary：K=3 是否形成低风险 + 两个机制不同的中高危表型")
print("3. phenotype_outcome_summary_k4_exploratory：K=4 是否切出小型极高危表型")
print("4. phenotype_k3_k4_refinement_crosstab：K=4 极高危小亚型是否主要来自 K=3 重症组")
print("5. phenotype_anemia_feasibility：K=3 每个 phenotype x anemia 格子的死亡事件数是否足够")
print("6. phenotype_gcs_sensitivity_summary：加入 total GCS、仅用 total GCS、或用 GCS grade 替代后主分型是否仍稳定")
print("7. phenotype_bootstrap_stability：bootstrap ARI 是否支持 K=3 assignment 的稳健性")
print("8. phenotype_prediction_metrics：phenotype 是否比 GCS-only 提供预测增量")
print("9. phenotype_regression_models：调整年龄、性别、入院类型、aneurysm evidence 和贫血后 phenotype 是否仍有关联")
print("10. phenotype_candidate_feature_audit：ePVS/troponin 是否适合作敏感性增强变量或仅描述")
print("11. phenotype_baseline_characteristics：总体与 K=3 phenotype 分层基线特征是否平衡、是否可作为 Table 1")
print("12. phenotype_anemia_stratified_models：各 phenotype 内贫血 aOR 是否稳定，稀疏格子仅作探索解释")
print("13. phenotype_sensitivity_cohort_summary：排除 RBC 和 ICU LOS >=48h 后 K=3 结构是否保留")
print("14. phenotype_epvs_sensitivity_summary：加入/替换 ePVS 后 assignment 是否明显改变")
