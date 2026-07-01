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
from sklearn.metrics import (
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)
from sklearn.preprocessing import StandardScaler


warnings.filterwarnings("ignore", category=FutureWarning)

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

# cohort 选择：
#   eligible_primary_analysis: 主分析
#   eligible_no_transfusion_sensitivity: 排除所有 0-48h RBC 输血患者
#   eligible_sensitivity_48h_los: ICU LOS >=48h 敏感性分析
COHORT_FLAG = "eligible_primary_analysis"

FEATURES = [
    "hb_min_48h_all",
    "gcs_min_48h",
    "gcs_grade_min_48h",
    "map_min_48h",
    "shock_index_max_48h",
    "spo2_min_48h",
    "creatinine_max_48h",
    "platelet_min_48h",
]

FEATURE_LABELS = {
    "hb_min_48h_all": "Hb min",
    "gcs_min_48h": "GCS min",
    "gcs_grade_min_48h": "GCS grade",
    "map_min_48h": "MAP min",
    "shock_index_max_48h": "Shock index max",
    "spo2_min_48h": "SpO2 min",
    "creatinine_max_48h": "Creatinine max",
    "platelet_min_48h": "Platelet min",
}

# 标准化后，正方向代表生理状态更差。
SEVERITY_DIRECTIONS = {
    "hb_min_48h_all": -1,
    "gcs_min_48h": -1,
    "gcs_grade_min_48h": 1,
    "map_min_48h": -1,
    "shock_index_max_48h": 1,
    "spo2_min_48h": -1,
    "creatinine_max_48h": 1,
    "platelet_min_48h": -1,
}

OUTPUT_TABLES = {
    "k_metrics": f"{PROJECT_ID}.{DATASET_ID}.phenotype_k_selection_metrics",
    "assignments": f"{PROJECT_ID}.{DATASET_ID}.phenotype_cluster_assignments",
    "centers": f"{PROJECT_ID}.{DATASET_ID}.phenotype_cluster_centers_zscore",
    "feature_summary": f"{PROJECT_ID}.{DATASET_ID}.phenotype_feature_summary_raw",
    "outcome_summary": f"{PROJECT_ID}.{DATASET_ID}.phenotype_outcome_summary",
    "anemia_feasibility": f"{PROJECT_ID}.{DATASET_ID}.phenotype_anemia_feasibility",
    "tests": f"{PROJECT_ID}.{DATASET_ID}.phenotype_lightweight_tests",
    "stability": f"{PROJECT_ID}.{DATASET_ID}.phenotype_cluster_stability",
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
        "has_aneurysm_procedure",
        "icu_los_days",
        "hospital_los_days",
        "hospital_mortality",
        "icu_mortality",
        "early_anemia_all",
        "early_anemia_pre_transfusion",
        "any_rbc_transfusion_48h",
        "massive_transfusion_24h",
        "core_feature_missing_count",
        "eligible_primary_analysis",
        "eligible_no_transfusion_sensitivity",
        "eligible_sensitivity_48h_los",
        "gcs_motor_min_48h",
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
    WHERE {COHORT_FLAG} = 1
    """
    print(f"读取 BigQuery 表：{INPUT_TABLE}")
    print(f"当前 cohort flag：{COHORT_FLAG} = 1")
    df = client.query(sql).to_dataframe()
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


def build_feature_matrix(df: pd.DataFrame):
    """对 8 个低缺失核心聚类变量做中位数填补和 Z-score 标准化。"""
    x_raw = df[FEATURES].apply(pd.to_numeric, errors="coerce")
    missing_summary = pd.DataFrame(
        {
            "feature": FEATURES,
            "missing_n": [int(x_raw[col].isna().sum()) for col in FEATURES],
            "total_n": len(x_raw),
            "missing_rate": [float(x_raw[col].isna().mean()) for col in FEATURES],
        }
    ).sort_values("missing_rate", ascending=False)
    display(missing_summary)

    imputer = SimpleImputer(strategy="median")
    scaler = StandardScaler()
    x_imputed = imputer.fit_transform(x_raw)
    x_scaled = scaler.fit_transform(x_imputed)
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


def build_ordered_phenotype_labels(x_scaled: np.ndarray, raw_labels: np.ndarray) -> tuple[pd.DataFrame, dict[int, int]]:
    """根据生理严重程度给原始 cluster 排序，生成 phenotype 1..K。"""
    raw_clusters = sorted(np.unique(raw_labels))
    centers = pd.DataFrame(
        [x_scaled[raw_labels == label].mean(axis=0) for label in raw_clusters],
        columns=FEATURES,
    )
    centers.insert(0, "raw_cluster", raw_clusters)

    severity_score = np.zeros(len(centers))
    for feature, direction in SEVERITY_DIRECTIONS.items():
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
    plt.show()


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
    plt.show()


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
    plt.show()


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
    "nsah_evidence_level",
    "has_aneurysm_dx",
    "has_aneurysm_procedure",
    "gcs_motor_min_48h",
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

metrics = run_k_selection(x_scaled)
plot_k_metrics(metrics)

primary = run_phenotype_solution(df, x_scaled, PRIMARY_K, "primary_k3")
exploratory = run_phenotype_solution(df, x_scaled, EXPLORATORY_K, "exploratory_k4")
k3_k4_crosstab = build_k3_k4_refinement_crosstab(primary["assignments"], exploratory["assignments"])

print("\nK=3 主分型与 K=4 高分辨率分型交叉表：")
display(k3_k4_crosstab)

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
