"""Patient-grouped, full-pipeline bootstrap utilities for phenotype stability."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import adjusted_rand_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def grouped_bootstrap_indices(subjects: pd.Series, rng: np.random.Generator) -> np.ndarray:
    """Sample subjects with replacement and retain every row for each draw."""
    subject_values = subjects.reset_index(drop=True)
    unique_subjects = pd.unique(subject_values)
    sampled_subjects = rng.choice(unique_subjects, size=len(unique_subjects), replace=True)
    indices_by_subject = {
        subject: np.flatnonzero(subject_values.to_numpy() == subject)
        for subject in unique_subjects
    }
    return np.concatenate([indices_by_subject[subject] for subject in sampled_subjects])


def _transform_frame(frame: pd.DataFrame, log_features: set[str]) -> pd.DataFrame:
    transformed = frame.apply(pd.to_numeric, errors="coerce").copy()
    for feature in log_features.intersection(transformed.columns):
        transformed[feature] = np.log1p(transformed[feature].clip(lower=0))
    return transformed


def _ordered_labels(
    scaled_features: np.ndarray,
    raw_labels: np.ndarray,
    features: Sequence[str],
    severity_directions: Mapping[str, int],
) -> np.ndarray:
    directions = np.array([severity_directions.get(feature, 1) for feature in features])
    scores = {}
    for raw_label in np.unique(raw_labels):
        center = scaled_features[raw_labels == raw_label].mean(axis=0)
        scores[int(raw_label)] = float(np.mean(center * directions))
    label_map = {
        raw_label: ordered_label
        for ordered_label, (raw_label, _) in enumerate(
            sorted(scores.items(), key=lambda item: item[1]), start=1
        )
    }
    return np.array([label_map[int(label)] for label in raw_labels], dtype=int)


def _jaccard(reference: np.ndarray, predicted: np.ndarray, phenotype: int) -> float:
    reference_mask = reference == phenotype
    predicted_mask = predicted == phenotype
    union = np.logical_or(reference_mask, predicted_mask).sum()
    return float(np.logical_and(reference_mask, predicted_mask).sum() / union) if union else np.nan


def run_grouped_pipeline_bootstrap(
    frame: pd.DataFrame,
    *,
    features: Sequence[str],
    reference_phenotype: pd.Series,
    subject_column: str,
    k: int,
    random_seed: int,
    n_bootstrap: int,
    severity_directions: Mapping[str, int],
    log_features: Sequence[str] = (),
    pca_components: int | None = None,
) -> pd.DataFrame:
    """Refit imputation, scaling, optional PCA, and K-means by subject bootstrap."""
    if frame.empty:
        raise ValueError("Cannot bootstrap an empty analysis frame.")
    if frame[subject_column].isna().any():
        raise ValueError(f"{subject_column} must be complete for grouped resampling.")
    if len(reference_phenotype) != len(frame):
        raise ValueError("Reference phenotype length must match the analysis frame.")

    raw_features = frame[list(features)].reset_index(drop=True)
    subjects = frame[subject_column].reset_index(drop=True)
    reference = reference_phenotype.astype(int).reset_index(drop=True).to_numpy()
    unique_subjects = pd.unique(subjects)
    transformed_all = _transform_frame(raw_features, set(log_features))
    rng = np.random.default_rng(random_seed)
    rows: list[dict[str, float | int]] = []

    for iteration in range(1, n_bootstrap + 1):
        sampled_subjects = rng.choice(unique_subjects, size=len(unique_subjects), replace=True)
        indices_by_subject = {
            subject: np.flatnonzero(subjects.to_numpy() == subject)
            for subject in unique_subjects
        }
        sample_idx = np.concatenate([indices_by_subject[subject] for subject in sampled_subjects])
        sampled = transformed_all.iloc[sample_idx]

        imputer = SimpleImputer(strategy="median")
        scaler = StandardScaler()
        sampled_scaled = scaler.fit_transform(imputer.fit_transform(sampled))
        all_scaled = scaler.transform(imputer.transform(transformed_all))

        if pca_components is not None:
            n_components = min(pca_components, sampled_scaled.shape[0], sampled_scaled.shape[1])
            projector = PCA(n_components=n_components, random_state=random_seed + iteration)
            sampled_clustering = projector.fit_transform(sampled_scaled)
            all_clustering = projector.transform(all_scaled)
        else:
            sampled_clustering = sampled_scaled
            all_clustering = all_scaled

        model = KMeans(
            n_clusters=k,
            random_state=random_seed + iteration,
            n_init=50,
        ).fit(sampled_clustering)
        predicted_raw = model.predict(all_clustering)
        predicted = _ordered_labels(
            all_scaled,
            predicted_raw,
            features,
            severity_directions,
        )

        sampled_unique = set(sampled_subjects.tolist())
        oob_mask = ~subjects.isin(sampled_unique).to_numpy()
        oob_subjects_n = int(subjects[oob_mask].nunique())
        oob_ari = (
            float(adjusted_rand_score(reference[oob_mask], predicted[oob_mask]))
            if oob_mask.sum() >= 2 and len(np.unique(reference[oob_mask])) >= 2
            else np.nan
        )
        counts = pd.Series(predicted).value_counts()
        row: dict[str, float | int] = {
            "iteration": iteration,
            "sampled_subjects_n": int(len(sampled_subjects)),
            "unique_sampled_subjects_n": int(len(sampled_unique)),
            "oob_subjects_n": oob_subjects_n,
            "adjusted_rand_index_vs_primary": float(adjusted_rand_score(reference, predicted)),
            "oob_adjusted_rand_index_vs_primary": oob_ari,
            "same_ordered_label_rate": float(np.mean(reference == predicted)),
            "min_cluster_n": int(counts.min()),
        }
        for phenotype in range(1, k + 1):
            row[f"cluster_jaccard_p{phenotype}"] = _jaccard(reference, predicted, phenotype)
        rows.append(row)

    return pd.DataFrame(rows)


def grouped_logistic_predictions(
    frame: pd.DataFrame,
    *,
    predictors: Sequence[str],
    outcome: str,
    subject_column: str,
    n_splits: int,
    random_seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Generate out-of-fold probabilities with subject grouping and fold-local preprocessing."""
    model_frame = frame[[subject_column, outcome, *predictors]].copy()
    if model_frame[[subject_column, outcome]].isna().any().any():
        raise ValueError("Subject and outcome columns must be complete for grouped cross-validation.")
    y = model_frame[outcome].astype(int).to_numpy()
    groups = model_frame[subject_column].to_numpy()
    x = model_frame[list(predictors)]
    numeric = [column for column in predictors if pd.api.types.is_numeric_dtype(x[column])]
    categorical = [column for column in predictors if column not in numeric]

    transformers = []
    if numeric:
        transformers.append(
            (
                "numeric",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                numeric,
            )
        )
    if categorical:
        transformers.append(
            (
                "categorical",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("encoder", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categorical,
            )
        )

    splitter = StratifiedGroupKFold(
        n_splits=n_splits,
        shuffle=True,
        random_state=random_seed,
    )
    probabilities = np.full(len(model_frame), np.nan, dtype=float)
    fold_ids = np.full(len(model_frame), -1, dtype=int)
    for fold_id, (train_idx, test_idx) in enumerate(splitter.split(x, y, groups)):
        pipeline = Pipeline(
            [
                ("preprocess", ColumnTransformer(transformers=transformers)),
                ("model", LogisticRegression(max_iter=2000, solver="liblinear")),
            ]
        )
        pipeline.fit(x.iloc[train_idx], y[train_idx])
        probabilities[test_idx] = pipeline.predict_proba(x.iloc[test_idx])[:, 1]
        fold_ids[test_idx] = fold_id

    if np.isnan(probabilities).any() or (fold_ids < 0).any():
        raise RuntimeError("Grouped cross-validation did not produce one prediction per row.")
    return probabilities, fold_ids
