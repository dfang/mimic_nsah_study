#!/usr/bin/env python3
"""Run eICU external validation for the MIMIC non-traumatic SAH phenotypes.

Primary analysis: frozen_mimic_transport.
Sensitivity analysis: eICU de novo log-PCA K-means with ARI against transport labels.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score, silhouette_score
from sklearn.preprocessing import StandardScaler


PROJECT_ID = "mimic-study-498508"
MIMIC_DATASET = "non_traumatic_sah_study"
EICU_DATASET = "eicu_sah_validation"
RANDOM_SEED = 42
PRIMARY_K = 3

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
HB_FREE_FEATURES = [feature for feature in FEATURES if feature != "hb_min_48h_all"]
INR_FREE_FEATURES = [feature for feature in FEATURES if feature != "inr_max_48h"]
LOG_TRANSFORM_FEATURES = ["creatinine_max_48h", "inr_max_48h"]
SEVERITY_DIRECTIONS = {
    "hb_min_48h_all": -1,
    "gcs_motor_min_48h": -1,
    "map_min_48h": -1,
    "shock_index_max_48h": 1,
    "spo2_min_48h": -1,
    "creatinine_max_48h": 1,
    "inr_max_48h": 1,
    "platelet_min_48h": -1,
}


@dataclass
class FrozenPipeline:
    features: list[str]
    imputer: SimpleImputer
    scaler: StandardScaler
    pca: PCA
    centroids_pc: pd.DataFrame
    centers_z: pd.DataFrame


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run eICU frozen transport validation.")
    parser.add_argument("--project", default=PROJECT_ID)
    parser.add_argument("--mimic-dataset", default=MIMIC_DATASET)
    parser.add_argument("--eicu-dataset", default=EICU_DATASET)
    parser.add_argument("--location", default="US")
    return parser.parse_args()


def read_table(client, table: str) -> pd.DataFrame:
    job = client.query(f"SELECT * FROM `{table}`")
    print(f"BigQuery read job: {job.job_id}")
    return job.to_dataframe(create_bqstorage_client=False)


def write_table(client, df: pd.DataFrame, table: str) -> None:
    from google.cloud import bigquery

    job_config = bigquery.LoadJobConfig(write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE)
    job = client.load_table_from_dataframe(df, table, job_config=job_config)
    print(f"BigQuery load job: {job.job_id}")
    job.result()
    print(f"Wrote {len(df):,} rows to {table}")


def transform_feature_frame(df: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    x = df[features].apply(pd.to_numeric, errors="coerce").copy()
    for feature in LOG_TRANSFORM_FEATURES:
        if feature in x.columns:
            x[feature] = np.log1p(x[feature].clip(lower=0))
    return x


def fit_frozen_mimic_pipeline(mimic: pd.DataFrame, features: list[str]) -> FrozenPipeline:
    x = transform_feature_frame(mimic, features)
    imputer = SimpleImputer(strategy="median")
    x_imputed = imputer.fit_transform(x)
    scaler = StandardScaler()
    x_scaled = scaler.fit_transform(x_imputed)
    pca = PCA(n_components=3, random_state=RANDOM_SEED)
    pc_scores = pca.fit_transform(x_scaled)

    working = mimic[["phenotype"]].copy()
    for idx in range(pc_scores.shape[1]):
        working[f"pc{idx + 1}"] = pc_scores[:, idx]
    centroids_pc = working.groupby("phenotype")[[f"pc{i}" for i in range(1, 4)]].mean().reset_index()

    centers = pd.DataFrame(x_scaled, columns=features)
    centers["phenotype"] = mimic["phenotype"].astype(int).to_numpy()
    centers_z = centers.groupby("phenotype")[features].mean().reset_index()
    severity_score = np.zeros(len(centers_z))
    for feature, direction in SEVERITY_DIRECTIONS.items():
        if feature in centers_z:
            severity_score += direction * centers_z[feature].to_numpy()
    centers_z["severity_score"] = severity_score

    return FrozenPipeline(
        features=features,
        imputer=imputer,
        scaler=scaler,
        pca=pca,
        centroids_pc=centroids_pc,
        centers_z=centers_z,
    )


def apply_frozen_transport(eicu: pd.DataFrame, pipeline: FrozenPipeline) -> tuple[pd.DataFrame, np.ndarray]:
    x = transform_feature_frame(eicu, pipeline.features)
    x_imputed = pipeline.imputer.transform(x)
    x_scaled = pipeline.scaler.transform(x_imputed)
    pc_scores = pipeline.pca.transform(x_scaled)
    centroids = pipeline.centroids_pc[[f"pc{i}" for i in range(1, 4)]].to_numpy()
    centroid_phenotypes = pipeline.centroids_pc["phenotype"].astype(int).to_numpy()
    distances = np.linalg.norm(pc_scores[:, None, :] - centroids[None, :, :], axis=2)
    nearest_idx = distances.argmin(axis=1)
    sorted_distances = np.sort(distances, axis=1)

    out = eicu.copy()
    out["raw_cluster"] = nearest_idx
    out["phenotype"] = centroid_phenotypes[nearest_idx]
    out["phenotype_label"] = out["phenotype"].map(lambda value: f"Phenotype {int(value)}")
    for idx, phenotype in enumerate(centroid_phenotypes):
        out[f"distance_to_phenotype_{int(phenotype)}"] = distances[:, idx]
    out["nearest_distance"] = sorted_distances[:, 0]
    out["second_nearest_distance"] = sorted_distances[:, 1] if distances.shape[1] > 1 else np.nan
    out["assignment_margin"] = out["second_nearest_distance"] - out["nearest_distance"]
    out["external_validation_method"] = "frozen_mimic_transport"
    return out, pc_scores


def build_summary(assignments: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for phenotype, group in assignments.groupby("phenotype"):
        mortality = group["hospital_mortality"].astype(float)
        n = len(group)
        deaths = int(mortality.sum())
        ci_low, ci_high = stats.binomtest(deaths, n).proportion_ci(method="wilson") if n else (np.nan, np.nan)
        rows.append(
            {
                "phenotype": int(phenotype),
                "n": int(n),
                "hospital_deaths": deaths,
                "hospital_mortality_rate": float(mortality.mean()),
                "hospital_mortality_ci_low": float(ci_low),
                "hospital_mortality_ci_high": float(ci_high),
                "icu_deaths": int(group["icu_mortality"].astype(float).sum()),
                "icu_mortality_rate": float(group["icu_mortality"].astype(float).mean()),
                "early_anemia_n": int(group["early_anemia_all"].fillna(0).astype(float).sum()),
                "early_anemia_rate": float(group["early_anemia_all"].astype(float).mean()),
                "any_rbc_transfusion_48h_n": int(group["any_rbc_transfusion_48h"].fillna(0).astype(float).sum()),
                "any_rbc_transfusion_48h_rate": float(group["any_rbc_transfusion_48h"].astype(float).mean()),
                "median_nearest_distance": float(group["nearest_distance"].median()),
                "median_assignment_margin": float(group["assignment_margin"].median()),
            }
        )
    return pd.DataFrame(rows).sort_values("phenotype")


def build_feature_summary(assignments: pd.DataFrame, features: Iterable[str]) -> pd.DataFrame:
    rows = []
    for phenotype, group in assignments.groupby("phenotype"):
        row = {"phenotype": int(phenotype), "n": int(len(group))}
        for feature in features:
            values = pd.to_numeric(group[feature], errors="coerce")
            row[f"{feature}_median"] = float(values.median()) if values.notna().any() else np.nan
            row[f"{feature}_q1"] = float(values.quantile(0.25)) if values.notna().any() else np.nan
            row[f"{feature}_q3"] = float(values.quantile(0.75)) if values.notna().any() else np.nan
            row[f"{feature}_missing_rate"] = float(values.isna().mean())
        rows.append(row)
    return pd.DataFrame(rows).sort_values("phenotype")


def build_assignment_quality(assignments: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "n": int(len(assignments)),
                "phenotype_count": int(assignments["phenotype"].nunique()),
                "nearest_distance_median": float(assignments["nearest_distance"].median()),
                "nearest_distance_q1": float(assignments["nearest_distance"].quantile(0.25)),
                "nearest_distance_q3": float(assignments["nearest_distance"].quantile(0.75)),
                "assignment_margin_median": float(assignments["assignment_margin"].median()),
                "assignment_margin_q1": float(assignments["assignment_margin"].quantile(0.25)),
                "assignment_margin_q3": float(assignments["assignment_margin"].quantile(0.75)),
                "low_margin_0_10_rate": float((assignments["assignment_margin"] < 0.10).mean()),
                "low_margin_0_25_rate": float((assignments["assignment_margin"] < 0.25).mean()),
            }
        ]
    )


def build_lightweight_tests(assignments: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for feature in ["hospital_mortality", "icu_mortality", "early_anemia_all", "any_rbc_transfusion_48h"]:
        table = pd.crosstab(assignments["phenotype"], assignments[feature].fillna(0).astype(int))
        if table.shape[0] > 1 and table.shape[1] > 1:
            _, p_value, _, _ = stats.chi2_contingency(table)
        else:
            p_value = np.nan
        rows.append({"feature": feature, "test": "chi_square_by_transported_phenotype", "p_value": float(p_value)})
    return pd.DataFrame(rows)


def build_sensitivity_summary(
    mimic: pd.DataFrame,
    eicu_all: pd.DataFrame,
    analyses: list[tuple[str, pd.Series, list[str], str]],
) -> pd.DataFrame:
    """Run frozen transport over prespecified eICU subsets/features."""
    rows = []
    for analysis_name, mask, features, note in analyses:
        subset = eicu_all[mask.fillna(False)].copy()
        if subset.empty:
            rows.append(
                {
                    "analysis": analysis_name,
                    "features": ",".join(features),
                    "n": 0,
                    "phenotype": np.nan,
                    "phenotype_n": 0,
                    "hospital_mortality_rate": np.nan,
                    "icu_mortality_rate": np.nan,
                    "early_anemia_rate": np.nan,
                    "any_rbc_transfusion_48h_rate": np.nan,
                    "median_nearest_distance": np.nan,
                    "median_assignment_margin": np.nan,
                    "phenotype_count": 0,
                    "min_phenotype_n": 0,
                    "note": note,
                }
            )
            continue

        pipeline = fit_frozen_mimic_pipeline(mimic, features)
        assignments, _ = apply_frozen_transport(subset, pipeline)
        phenotype_counts = assignments["phenotype"].value_counts()
        phenotype_count = int(phenotype_counts.size)
        min_phenotype_n = int(phenotype_counts.min()) if phenotype_count else 0
        for phenotype, group in assignments.groupby("phenotype"):
            rows.append(
                {
                    "analysis": analysis_name,
                    "features": ",".join(features),
                    "n": int(len(assignments)),
                    "phenotype": int(phenotype),
                    "phenotype_n": int(len(group)),
                    "hospital_mortality_rate": float(group["hospital_mortality"].astype(float).mean()),
                    "icu_mortality_rate": float(group["icu_mortality"].astype(float).mean()),
                    "early_anemia_rate": float(group["early_anemia_all"].astype(float).mean()),
                    "any_rbc_transfusion_48h_rate": float(group["any_rbc_transfusion_48h"].astype(float).mean()),
                    "median_nearest_distance": float(group["nearest_distance"].median()),
                    "median_assignment_margin": float(group["assignment_margin"].median()),
                    "phenotype_count": phenotype_count,
                    "min_phenotype_n": min_phenotype_n,
                    "note": note,
                }
            )
    return pd.DataFrame(rows).sort_values(["analysis", "phenotype"], na_position="last")


def build_severity_validation(assignments: pd.DataFrame) -> pd.DataFrame:
    """Validate transported phenotype order against eICU APACHE severity outputs."""
    severity_features = [
        "acutephysiologyscore",
        "apachescore",
        "predictedicumortality",
        "predictedhospitalmortality",
    ]
    rows = []
    for feature in severity_features:
        values = pd.to_numeric(assignments[feature], errors="coerce") if feature in assignments.columns else pd.Series(dtype=float)
        tmp = assignments[["phenotype"]].copy()
        tmp[feature] = values
        tmp = tmp.dropna(subset=[feature])
        groups = [group[feature].astype(float).to_numpy() for _, group in tmp.groupby("phenotype") if len(group) > 0]
        if len(tmp) >= 3 and tmp["phenotype"].nunique() > 1:
            rho, spearman_p = stats.spearmanr(tmp["phenotype"].astype(int), tmp[feature].astype(float))
        else:
            rho, spearman_p = np.nan, np.nan
        if len(groups) > 1:
            try:
                kruskal_p = stats.kruskal(*groups).pvalue
            except ValueError:
                kruskal_p = np.nan
        else:
            kruskal_p = np.nan

        for phenotype, group in tmp.groupby("phenotype"):
            group_values = group[feature].astype(float)
            rows.append(
                {
                    "severity_feature": feature,
                    "phenotype": int(phenotype),
                    "n_nonmissing": int(group_values.notna().sum()),
                    "median": float(group_values.median()),
                    "q1": float(group_values.quantile(0.25)),
                    "q3": float(group_values.quantile(0.75)),
                    "spearman_rho_vs_phenotype": float(rho) if pd.notna(rho) else np.nan,
                    "spearman_p_value": float(spearman_p) if pd.notna(spearman_p) else np.nan,
                    "kruskal_p_value": float(kruskal_p) if pd.notna(kruskal_p) else np.nan,
                    "note": "External criterion validity: APACHE severity should increase across transported phenotype order.",
                }
            )
    return pd.DataFrame(rows).sort_values(["severity_feature", "phenotype"])


def order_de_novo_labels(x_scaled: np.ndarray, raw_labels: np.ndarray, features: list[str]) -> dict[int, int]:
    centers = pd.DataFrame(
        [x_scaled[raw_labels == label].mean(axis=0) for label in sorted(np.unique(raw_labels))],
        columns=features,
    )
    centers["raw_cluster"] = sorted(np.unique(raw_labels))
    severity = np.zeros(len(centers))
    for feature, direction in SEVERITY_DIRECTIONS.items():
        if feature in centers:
            severity += direction * centers[feature].to_numpy()
    centers["severity_score"] = severity
    ordered = centers.sort_values("severity_score")["raw_cluster"].tolist()
    return {int(raw): int(idx + 1) for idx, raw in enumerate(ordered)}


def run_de_novo(eicu: pd.DataFrame, transport_assignments: pd.DataFrame, features: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    x = transform_feature_frame(eicu, features)
    imputer = SimpleImputer(strategy="median")
    x_imputed = imputer.fit_transform(x)
    scaler = StandardScaler()
    x_scaled = scaler.fit_transform(x_imputed)
    pca = PCA(n_components=3, random_state=RANDOM_SEED)
    pc_scores = pca.fit_transform(x_scaled)
    model = KMeans(n_clusters=PRIMARY_K, random_state=RANDOM_SEED, n_init=100)
    raw_labels = model.fit_predict(pc_scores)
    label_map = order_de_novo_labels(x_scaled, raw_labels, features)
    labels = np.array([label_map[int(label)] for label in raw_labels])

    summary_rows = []
    tmp = eicu.copy()
    tmp["de_novo_phenotype"] = labels
    for phenotype, group in tmp.groupby("de_novo_phenotype"):
        summary_rows.append(
            {
                "de_novo_phenotype": int(phenotype),
                "n": int(len(group)),
                "hospital_mortality_rate": float(group["hospital_mortality"].astype(float).mean()),
                "early_anemia_rate": float(group["early_anemia_all"].astype(float).mean()),
            }
        )

    metrics = pd.DataFrame(
        [
            {
                "analysis": "eicu_de_novo_k3_vs_mimic_projection",
                "adjusted_rand_index": float(adjusted_rand_score(transport_assignments["phenotype"].astype(int), labels)),
                "normalized_mutual_information": float(normalized_mutual_info_score(transport_assignments["phenotype"].astype(int), labels)),
                "same_ordered_label_rate": float((transport_assignments["phenotype"].astype(int).to_numpy() == labels).mean()),
                "silhouette": float(silhouette_score(pc_scores, labels)),
                "n": int(len(eicu)),
                "min_de_novo_cluster_n": int(pd.Series(labels).value_counts().min()),
                "note": "De novo eICU clustering is a structural sensitivity analysis, not the primary external validation.",
            }
        ]
    )
    return pd.DataFrame(summary_rows).sort_values("de_novo_phenotype"), metrics


def run_hb_free_anemia_regression(assignments: pd.DataFrame) -> pd.DataFrame:
    """phenotype_hb_free_anemia_regression analogue for eICU."""
    try:
        import statsmodels.formula.api as smf
    except ImportError:
        return pd.DataFrame(
            [
                {
                    "model": "eicu_hb_free_phenotype_anemia_adjusted",
                    "term": "statsmodels_unavailable",
                    "odds_ratio": np.nan,
                    "ci_lower": np.nan,
                    "ci_upper": np.nan,
                    "p_value": np.nan,
                    "n": int(len(assignments)),
                    "events": int(assignments["hospital_mortality"].astype(int).sum()),
                    "note": "statsmodels unavailable",
                }
            ]
        )

    model_df = assignments[
        ["hospital_mortality", "phenotype", "early_anemia_all", "age", "gender", "admission_type"]
    ].copy()
    model_df = model_df.dropna(subset=["hospital_mortality", "phenotype", "early_anemia_all", "age"])
    model_df["gender"] = model_df["gender"].fillna("Unknown")
    model_df["admission_type_group"] = model_df["admission_type"].fillna("Unknown").astype(str).str.slice(0, 60)
    formula = "hospital_mortality ~ C(phenotype) + early_anemia_all + age + C(gender)"
    rows = []
    try:
        fitted = smf.logit(formula, data=model_df).fit(disp=False, maxiter=200)
        conf = fitted.conf_int()
        for term, coef in fitted.params.items():
            rows.append(
                {
                    "model": "eicu_hb_free_phenotype_anemia_adjusted",
                    "term": term,
                    "formula": formula,
                    "odds_ratio": float(np.exp(coef)),
                    "ci_lower": float(np.exp(conf.loc[term, 0])),
                    "ci_upper": float(np.exp(conf.loc[term, 1])),
                    "p_value": float(fitted.pvalues[term]),
                    "n": int(fitted.nobs),
                    "events": int(model_df["hospital_mortality"].astype(int).sum()),
                    "note": "Hb-free transport sensitivity: phenotype assignment rebuilt without Hb before anemia adjustment.",
                }
            )
    except Exception as exc:
        rows.append(
            {
                "model": "eicu_hb_free_phenotype_anemia_adjusted",
                "term": "model_failed",
                "formula": formula,
                "odds_ratio": np.nan,
                "ci_lower": np.nan,
                "ci_upper": np.nan,
                "p_value": np.nan,
                "n": int(len(model_df)),
                "events": int(model_df["hospital_mortality"].astype(int).sum()),
                "note": str(exc),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    args = parse_args()
    from google.cloud import bigquery

    client = bigquery.Client(project=args.project, location=args.location)
    mimic_table = f"{args.project}.{args.mimic_dataset}.phenotype_cluster_assignments"
    eicu_table = f"{args.project}.{args.eicu_dataset}.eicu_analysis_features_48h"

    mimic = read_table(client, mimic_table)
    mimic = mimic[mimic["phenotype_solution"].fillna("").eq("primary_log_pca_kmeans_k3")].copy()
    if mimic.empty:
        mimic = read_table(client, mimic_table).copy()
    mimic = mimic.dropna(subset=["phenotype"])

    eicu_all = read_table(client, eicu_table)
    eicu = eicu_all[eicu_all["eligible_external_validation"].astype(int).eq(1)].copy()
    print(f"MIMIC training rows: {len(mimic):,}")
    print(f"eICU validation rows: {len(eicu):,}")

    pipeline = fit_frozen_mimic_pipeline(mimic, FEATURES)
    assignments, _pc_scores = apply_frozen_transport(eicu, pipeline)
    assignments = assignments.sort_values("patientunitstayid").reset_index(drop=True)

    outcome_summary = build_summary(assignments)
    feature_summary = build_feature_summary(assignments, FEATURES)
    assignment_quality = build_assignment_quality(assignments)
    lightweight_tests = build_lightweight_tests(assignments)
    de_novo_summary, de_novo_metrics = run_de_novo(eicu, assignments, FEATURES)
    severity_validation = build_severity_validation(assignments)

    inr_free_missing_count = eicu_all[INR_FREE_FEATURES].apply(pd.to_numeric, errors="coerce").isna().sum(axis=1)
    sensitivity_analyses = [
        (
            "primary_frozen_transport",
            eicu_all["eligible_external_validation"].astype(int).eq(1),
            FEATURES,
            "Primary eICU transport: 8 features with <=2 missing.",
        ),
        (
            "los48_frozen_transport",
            eicu_all["eligible_external_los48_sensitivity"].astype(int).eq(1),
            FEATURES,
            "Patients observed for at least 48 ICU hours; addresses early death/treatment-window sensitivity.",
        ),
        (
            "no_recorded_rbc_frozen_transport",
            eicu_all["eligible_external_no_rbc_sensitivity"].astype(int).eq(1),
            FEATURES,
            "Excludes any recorded RBC exposure during 0-48h; eICU RBC units are not harmonized.",
        ),
        (
            "strict_sah_frozen_transport",
            eicu_all["eligible_external_strict_sah_sensitivity"].astype(int).eq(1),
            FEATURES,
            "Requires SAH evidence from diagnosis ICD/text, excluding admissionDx-only cases.",
        ),
        (
            "low_missing_frozen_transport",
            eicu_all["eligible_external_low_missing_sensitivity"].astype(int).eq(1),
            FEATURES,
            "8-feature model restricted to <=1 missing core feature.",
        ),
        (
            "complete_case_frozen_transport",
            eicu_all["eligible_external_complete_case_sensitivity"].astype(int).eq(1),
            FEATURES,
            "8-feature model restricted to complete cases.",
        ),
        (
            "inr_free_frozen_transport",
            inr_free_missing_count.le(2),
            INR_FREE_FEATURES,
            "Transport sensitivity excluding INR from both frozen MIMIC training and eICU projection.",
        ),
    ]
    sensitivity_summary = build_sensitivity_summary(mimic, eicu_all, sensitivity_analyses)

    hb_free_pipeline = fit_frozen_mimic_pipeline(mimic, HB_FREE_FEATURES)
    hb_free_assignments, _ = apply_frozen_transport(eicu, hb_free_pipeline)
    hb_free_regression = run_hb_free_anemia_regression(hb_free_assignments)

    metadata_rows = [
        {"key": "validation_strategy", "value": "frozen_mimic_transport_primary_de_novo_sensitivity"},
        {"key": "features", "value": ",".join(FEATURES)},
        {"key": "hb_free_features", "value": ",".join(HB_FREE_FEATURES)},
        {"key": "inr_free_features", "value": ",".join(INR_FREE_FEATURES)},
        {"key": "mimic_training_n", "value": str(len(mimic))},
        {"key": "eicu_validation_n", "value": str(len(eicu))},
        {"key": "primary_k", "value": str(PRIMARY_K)},
        {"key": "random_seed", "value": str(RANDOM_SEED)},
        {"key": "frozen_imputation", "value": "MIMIC median"},
        {"key": "frozen_scaling", "value": "MIMIC StandardScaler mean/std"},
        {"key": "frozen_pca", "value": "MIMIC PCA eigenvectors"},
        {"key": "frozen_centroids", "value": "MIMIC phenotype centroids in PCA space"},
    ]
    for feature, median in zip(FEATURES, pipeline.imputer.statistics_, strict=False):
        metadata_rows.append({"key": f"mimic_imputation_median_{feature}", "value": str(float(median))})
    metadata = pd.DataFrame(metadata_rows)

    centers = pipeline.centers_z.copy()
    for idx, row in pipeline.centroids_pc.iterrows():
        for pc in ["pc1", "pc2", "pc3"]:
            centers.loc[centers["phenotype"] == row["phenotype"], pc] = row[pc]

    output_prefix = f"{args.project}.{args.eicu_dataset}"
    write_table(client, metadata, f"{output_prefix}.mimic_fixed_k3_model_metadata")
    write_table(client, centers, f"{output_prefix}.mimic_fixed_k3_centers_zscore")
    write_table(client, assignments, f"{output_prefix}.eicu_external_phenotype_assignments")
    write_table(client, outcome_summary, f"{output_prefix}.eicu_external_outcome_summary_by_phenotype")
    write_table(client, feature_summary, f"{output_prefix}.eicu_external_feature_summary_by_phenotype")
    write_table(client, assignment_quality, f"{output_prefix}.eicu_external_assignment_quality")
    write_table(client, lightweight_tests, f"{output_prefix}.eicu_external_lightweight_tests")
    write_table(client, sensitivity_summary, f"{output_prefix}.eicu_external_sensitivity_summary")
    write_table(client, severity_validation, f"{output_prefix}.eicu_external_severity_validation")
    write_table(client, de_novo_summary, f"{output_prefix}.eicu_de_novo_k3_summary")
    write_table(client, de_novo_metrics, f"{output_prefix}.eicu_de_novo_k3_metrics")
    write_table(client, hb_free_regression, f"{output_prefix}.eicu_hb_free_anemia_regression")


if __name__ == "__main__":
    main()
