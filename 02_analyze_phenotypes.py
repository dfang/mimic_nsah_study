#!/usr/bin/env python3
"""Analyze early physiological phenotypes for the MIMIC-IV SAH cohort.

Input is a CSV export of:
    mimic-study-498508.non_traumatic_sah_study.physiology_features_48h

The script performs:
    1. primary cohort filtering
    2. missingness and feasibility summaries
    3. median imputation + z-score scaling
    4. K-means K selection metrics
    5. phenotype assignment and severity-ordered labels
    6. phenotype center, outcome, and anemia summaries
    7. basic publication-oriented figures

No patient-level outputs should be committed to git.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
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


RANDOM_SEED = 42

FEATURES = [
    "hb_min_48h_all",
    "gcs_min_48h",
    "map_min_48h",
    "shock_index_max_48h",
    "lactate_max_48h",
    "oxygenation_min_48h",
    "creatinine_max_48h",
    "platelet_min_48h",
]

FEATURE_LABELS = {
    "hb_min_48h_all": "Hb min",
    "gcs_min_48h": "GCS min",
    "map_min_48h": "MAP min",
    "shock_index_max_48h": "Shock index max",
    "lactate_max_48h": "Lactate max",
    "oxygenation_min_48h": "Oxygenation min",
    "creatinine_max_48h": "Creatinine max",
    "platelet_min_48h": "Platelet min",
}

# Positive means physiologically worse after standardization.
SEVERITY_DIRECTIONS = {
    "hb_min_48h_all": -1,
    "gcs_min_48h": -1,
    "map_min_48h": -1,
    "shock_index_max_48h": 1,
    "lactate_max_48h": 1,
    "oxygenation_min_48h": -1,
    "creatinine_max_48h": 1,
    "platelet_min_48h": -1,
}

REQUIRED_COLUMNS = [
    "eligible_primary_analysis",
    "hospital_mortality",
    "early_anemia_all",
    "age",
    "gender",
    "icu_los_days",
    "hospital_los_days",
    *FEATURES,
]


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Run SAH early physiological phenotype analysis."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="CSV exported from mimic-study-498508.non_traumatic_sah_study.physiology_features_48h.",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs/phenotype_analysis",
        help="Directory for analysis outputs. Default: outputs/phenotype_analysis.",
    )
    parser.add_argument(
        "--k",
        default="4",
        help="K for K-means, or 'auto' to select by silhouette with minimum cluster size. Default: 4.",
    )
    parser.add_argument(
        "--k-min",
        type=int,
        default=2,
        help="Minimum K for K selection metrics. Default: 2.",
    )
    parser.add_argument(
        "--k-max",
        type=int,
        default=5,
        help="Maximum K for K selection metrics. Default: 5.",
    )
    parser.add_argument(
        "--min-cluster-frac",
        type=float,
        default=0.05,
        help="Minimum cluster fraction for auto K. Default: 0.05.",
    )
    parser.add_argument(
        "--sensitivity-no-transfusion",
        action="store_true",
        help="Use eligible_no_transfusion_sensitivity == 1 instead of primary cohort.",
    )
    parser.add_argument(
        "--sensitivity-48h-los",
        action="store_true",
        help="Use eligible_sensitivity_48h_los == 1 instead of primary cohort.",
    )
    return parser.parse_args()


def ensure_columns(df: pd.DataFrame, columns: list[str]) -> None:
    """Fail early if required input columns are absent."""
    missing = [col for col in columns if col not in df.columns]
    if missing:
        raise ValueError(f"Input is missing required columns: {missing}")


def select_analysis_cohort(df: pd.DataFrame, args: argparse.Namespace) -> pd.DataFrame:
    """Select the requested analysis cohort."""
    if args.sensitivity_no_transfusion:
        flag = "eligible_no_transfusion_sensitivity"
    elif args.sensitivity_48h_los:
        flag = "eligible_sensitivity_48h_los"
    else:
        flag = "eligible_primary_analysis"

    if flag not in df.columns:
        raise ValueError(f"Input does not contain cohort flag column: {flag}")

    selected = df[df[flag] == 1].copy()
    if selected.empty:
        raise ValueError(f"No rows selected with {flag} == 1")

    print(f"Selected cohort: {flag} == 1")
    print(f"Rows: {len(selected):,}")
    return selected


def summarize_missingness(df: pd.DataFrame, out_dir: Path) -> pd.DataFrame:
    """Write missingness summary for clustering features."""
    summary = pd.DataFrame(
        {
            "feature": FEATURES,
            "missing_n": [int(df[col].isna().sum()) for col in FEATURES],
            "total_n": len(df),
            "missing_rate": [float(df[col].isna().mean()) for col in FEATURES],
        }
    )
    summary.to_csv(out_dir / "feature_missingness.csv", index=False)
    return summary


def prepare_feature_matrix(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, SimpleImputer, StandardScaler]:
    """Impute and standardize clustering features."""
    values = df[FEATURES].apply(pd.to_numeric, errors="coerce").to_numpy()
    imputer = SimpleImputer(strategy="median")
    scaler = StandardScaler()
    imputed = imputer.fit_transform(values)
    scaled = scaler.fit_transform(imputed)
    return imputed, scaled, imputer, scaler


def run_k_selection(x_scaled: np.ndarray, args: argparse.Namespace, out_dir: Path) -> pd.DataFrame:
    """Run K-means metrics for the configured K range."""
    rows = []
    n = x_scaled.shape[0]
    for k in range(args.k_min, args.k_max + 1):
        if k >= n:
            continue
        model = KMeans(n_clusters=k, random_state=RANDOM_SEED, n_init=50)
        labels = model.fit_predict(x_scaled)
        counts = np.bincount(labels)
        rows.append(
            {
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
    metrics.to_csv(out_dir / "k_selection_metrics.csv", index=False)
    plot_k_selection(metrics, out_dir)
    return metrics


def choose_k(metrics: pd.DataFrame, args: argparse.Namespace) -> int:
    """Choose K from user input or silhouette with a minimum cluster-size constraint."""
    if args.k != "auto":
        k = int(args.k)
        if k not in set(metrics["k"]):
            raise ValueError(f"Requested k={k} is outside evaluated K values.")
        return k

    eligible = metrics[metrics["min_cluster_frac"] >= args.min_cluster_frac].copy()
    if eligible.empty:
        eligible = metrics.copy()
    best = eligible.sort_values(["silhouette", "min_cluster_frac"], ascending=False).iloc[0]
    return int(best["k"])


def severity_order_labels(centers: pd.DataFrame) -> dict[int, int]:
    """Map raw K-means labels to ordered phenotype labels by physiological severity."""
    score = np.zeros(len(centers))
    for col, direction in SEVERITY_DIRECTIONS.items():
        score += direction * centers[col].to_numpy()
    ordered_raw = np.argsort(score)
    return {int(raw): int(rank + 1) for rank, raw in enumerate(ordered_raw)}


def fit_kmeans(x_scaled: np.ndarray, k: int) -> tuple[KMeans, np.ndarray]:
    """Fit final K-means model."""
    model = KMeans(n_clusters=k, random_state=RANDOM_SEED, n_init=100)
    labels = model.fit_predict(x_scaled)
    return model, labels


def summarize_clusters(
    df: pd.DataFrame,
    x_scaled: np.ndarray,
    labels_raw: np.ndarray,
    out_dir: Path,
) -> pd.DataFrame:
    """Create phenotype labels and write cluster summaries."""
    centers = pd.DataFrame(
        [x_scaled[labels_raw == label].mean(axis=0) for label in sorted(set(labels_raw))],
        columns=FEATURES,
    )
    centers.insert(0, "raw_cluster", sorted(set(labels_raw)))
    label_map = severity_order_labels(centers.set_index("raw_cluster"))

    out = df.copy()
    out["raw_cluster"] = labels_raw
    out["phenotype"] = out["raw_cluster"].map(label_map)
    out["phenotype_label"] = out["phenotype"].map(lambda x: f"Phenotype {int(x)}")

    center_ordered = centers.copy()
    center_ordered["phenotype"] = center_ordered["raw_cluster"].map(label_map)
    center_ordered = center_ordered.sort_values("phenotype")
    center_ordered.to_csv(out_dir / "cluster_centers_zscore.csv", index=False)

    raw_summary = (
        out.groupby("phenotype")[FEATURES]
        .agg(["median", "mean", "std"])
        .reset_index()
    )
    raw_summary.columns = [
        "_".join([str(part) for part in col if part != ""]).rstrip("_")
        for col in raw_summary.columns.to_flat_index()
    ]
    raw_summary.to_csv(out_dir / "cluster_feature_summary_raw.csv", index=False)

    outcome_summary = build_outcome_summary(out)
    outcome_summary.to_csv(out_dir / "phenotype_outcome_summary.csv", index=False)

    feasibility = build_feasibility_summary(out)
    feasibility.to_csv(out_dir / "phenotype_anemia_feasibility.csv", index=False)

    out.to_csv(out_dir / "clustered_features.csv", index=False)
    plot_cluster_heatmap(center_ordered, out_dir)
    plot_cluster_sizes(out, out_dir)
    plot_anemia_mortality(out, out_dir)
    return out


def build_outcome_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Summarize outcomes and core variables by phenotype."""
    rows = []
    for phenotype, group in df.groupby("phenotype"):
        row = {
            "phenotype": phenotype,
            "n": len(group),
            "hospital_deaths": int((group["hospital_mortality"] == 1).sum()),
            "hospital_mortality_rate": float(group["hospital_mortality"].mean()),
            "early_anemia_n": int((group["early_anemia_all"] == 1).sum()),
            "early_anemia_rate": float(group["early_anemia_all"].mean()),
            "age_median": float(group["age"].median()),
            "icu_los_days_median": float(group["icu_los_days"].median()),
            "hospital_los_days_median": float(group["hospital_los_days"].median()),
        }
        for col in FEATURES:
            row[f"{col}_median"] = float(group[col].median())
        rows.append(row)
    return pd.DataFrame(rows).sort_values("phenotype")


def build_feasibility_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Build phenotype x anemia event-count summary for regression feasibility."""
    rows = []
    for phenotype, group in df.groupby("phenotype"):
        for anemia_value, anemia_group in group.groupby("early_anemia_all"):
            rows.append(
                {
                    "phenotype": phenotype,
                    "early_anemia_all": int(anemia_value),
                    "n": len(anemia_group),
                    "deaths": int((anemia_group["hospital_mortality"] == 1).sum()),
                    "mortality_rate": float(anemia_group["hospital_mortality"].mean()),
                }
            )
    return pd.DataFrame(rows).sort_values(["phenotype", "early_anemia_all"])


def run_statistical_summaries(df: pd.DataFrame, out_dir: Path) -> None:
    """Run lightweight statistical summaries that do not require statsmodels."""
    rows = []
    phenotype_groups = [g["hospital_mortality"].dropna() for _, g in df.groupby("phenotype")]
    if len(phenotype_groups) > 1:
        contingency = pd.crosstab(df["phenotype"], df["hospital_mortality"])
        chi2, p_value, _, _ = stats.chi2_contingency(contingency)
        rows.append(
            {
                "test": "chi_square_phenotype_vs_hospital_mortality",
                "statistic": float(chi2),
                "p_value": float(p_value),
            }
        )

    for col in FEATURES:
        groups = [g[col].dropna() for _, g in df.groupby("phenotype")]
        if all(len(g) > 0 for g in groups) and len(groups) > 1:
            stat, p_value = stats.kruskal(*groups)
            rows.append(
                {
                    "test": f"kruskal_{col}_by_phenotype",
                    "statistic": float(stat),
                    "p_value": float(p_value),
                }
            )

    pd.DataFrame(rows).to_csv(out_dir / "statistical_tests_lightweight.csv", index=False)


def run_cluster_stability(x_scaled: np.ndarray, labels: np.ndarray, k: int, out_dir: Path) -> None:
    """Compare K-means with hierarchical clustering using adjusted Rand index."""
    if x_scaled.shape[0] <= k:
        return
    hierarchical = AgglomerativeClustering(n_clusters=k)
    h_labels = hierarchical.fit_predict(x_scaled)
    ari = adjusted_rand_score(labels, h_labels)
    pd.DataFrame(
        [
            {
                "comparison": "kmeans_vs_hierarchical",
                "k": k,
                "adjusted_rand_index": float(ari),
            }
        ]
    ).to_csv(out_dir / "cluster_stability.csv", index=False)


def plot_k_selection(metrics: pd.DataFrame, out_dir: Path) -> None:
    """Plot K selection metrics."""
    fig, axes = plt.subplots(2, 2, figsize=(10, 8))
    axes = axes.ravel()
    plot_specs = [
        ("inertia", "Elbow: inertia"),
        ("silhouette", "Silhouette"),
        ("calinski_harabasz", "Calinski-Harabasz"),
        ("davies_bouldin", "Davies-Bouldin"),
    ]
    for ax, (col, title) in zip(axes, plot_specs):
        ax.plot(metrics["k"], metrics[col], marker="o")
        ax.set_xlabel("K")
        ax.set_ylabel(col)
        ax.set_title(title)
        ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(out_dir / "k_selection_metrics.png", dpi=180)
    plt.close(fig)


def plot_cluster_heatmap(centers: pd.DataFrame, out_dir: Path) -> None:
    """Plot standardized cluster centers."""
    matrix = centers.set_index("phenotype")[FEATURES]
    fig, ax = plt.subplots(figsize=(10, 4.8))
    im = ax.imshow(matrix.to_numpy(), aspect="auto", cmap="coolwarm", vmin=-2, vmax=2)
    ax.set_yticks(np.arange(len(matrix.index)))
    ax.set_yticklabels([f"Phenotype {int(x)}" for x in matrix.index])
    ax.set_xticks(np.arange(len(FEATURES)))
    ax.set_xticklabels([FEATURE_LABELS[col] for col in FEATURES], rotation=35, ha="right")
    ax.set_title("Standardized Phenotype Centers")
    fig.colorbar(im, ax=ax, label="Z-score")
    fig.tight_layout()
    fig.savefig(out_dir / "cluster_centers_heatmap.png", dpi=180)
    plt.close(fig)


def plot_cluster_sizes(df: pd.DataFrame, out_dir: Path) -> None:
    """Plot phenotype counts."""
    counts = df["phenotype"].value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar([f"P{int(idx)}" for idx in counts.index], counts.values)
    ax.set_ylabel("N")
    ax.set_title("Phenotype Size")
    fig.tight_layout()
    fig.savefig(out_dir / "phenotype_sizes.png", dpi=180)
    plt.close(fig)


def plot_anemia_mortality(df: pd.DataFrame, out_dir: Path) -> None:
    """Plot mortality by phenotype and anemia status."""
    summary = (
        df.groupby(["phenotype", "early_anemia_all"])["hospital_mortality"]
        .mean()
        .reset_index()
    )
    phenotypes = sorted(summary["phenotype"].unique())
    x = np.arange(len(phenotypes))
    width = 0.36

    fig, ax = plt.subplots(figsize=(8, 4.5))
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
    ax.set_title("Mortality by Phenotype and Early Anemia")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / "anemia_mortality_by_phenotype.png", dpi=180)
    plt.close(fig)


def write_next_steps(out_dir: Path, selected_k: int) -> None:
    """Write a short markdown guide for interpreting outputs."""
    text = f"""# Phenotype Analysis Outputs

Selected K: `{selected_k}`

Review files in this order:

1. `feature_missingness.csv`
2. `k_selection_metrics.csv` and `k_selection_metrics.png`
3. `cluster_centers_zscore.csv` and `cluster_centers_heatmap.png`
4. `phenotype_outcome_summary.csv`
5. `phenotype_anemia_feasibility.csv`
6. `anemia_mortality_by_phenotype.png`
7. `cluster_stability.csv`

Interpretation rules:

- Do not name phenotypes before inspecting cluster centers.
- If any phenotype has very small N or very few deaths, avoid complex within-phenotype regression.
- The primary claim should be phenotype-associated prognosis and phenotype-dependent anemia association, not causal effect of anemia or transfusion.
- If K=4 has a tiny cluster, compare against K=3 before writing results.
"""
    (out_dir / "README_outputs.md").write_text(text)


def main() -> int:
    """Run the full phenotype analysis pipeline."""
    args = parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.input)
    ensure_columns(df, REQUIRED_COLUMNS)
    cohort = select_analysis_cohort(df, args)

    summarize_missingness(cohort, out_dir)
    _, x_scaled, _, _ = prepare_feature_matrix(cohort)
    metrics = run_k_selection(x_scaled, args, out_dir)
    selected_k = choose_k(metrics, args)
    print(f"Selected K: {selected_k}")

    model, raw_labels = fit_kmeans(x_scaled, selected_k)
    clustered = summarize_clusters(cohort, x_scaled, raw_labels, out_dir)
    run_statistical_summaries(clustered, out_dir)
    run_cluster_stability(x_scaled, raw_labels, selected_k, out_dir)
    write_next_steps(out_dir, selected_k)

    print(f"Outputs written to: {out_dir}")
    print("Key next file: phenotype_anemia_feasibility.csv")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
