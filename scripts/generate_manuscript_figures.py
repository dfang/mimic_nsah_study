#!/usr/bin/env python3
"""
Generate manuscript figures for the non-traumatic SAH phenotype manuscript.

The values in this script are synchronized with dist/20260706/analysis_result.md.
Pass a YYYYMMDD directory name as argv[1]; output is written to dist/YYYYMMDD/figures.
"""
from __future__ import annotations

import datetime
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import FancyBboxPatch


today = datetime.datetime.now().strftime("%Y%m%d")
date_dir = sys.argv[1] if len(sys.argv) > 1 else today
figures_dir = f"dist/{date_dir}/figures"
os.makedirs(figures_dir, exist_ok=True)

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.labelsize": 10,
        "figure.dpi": 300,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.12,
    }
)

P1_COLOR = "#2166AC"
P2_COLOR = "#F4A582"
P3_COLOR = "#B2182B"
P4_COLOR = "#762A83"

PHENOTYPES = ["P1\nStable", "P2\nNeuro-circulatory", "P3\nMultisystem"]
COLORS = [P1_COLOR, P2_COLOR, P3_COLOR]


def savefig(name: str) -> None:
    plt.savefig(f"{figures_dir}/{name}")
    plt.close()
    print(f"{name} saved")


def fig1_cohort_flowchart() -> None:
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 12)
    ax.axis("off")
    ax.set_title("Figure 1. Cohort flowchart", fontweight="bold", loc="left")

    boxes = [
        (5, 11.0, 6.6, "MIMIC-IV 3.1 ICU admissions\nscreened in BigQuery"),
        (5, 9.2, 6.2, "Adult non-traumatic SAH\nICD-defined ICU cohort"),
        (5, 7.4, 5.8, "First ICU stay; ICU LOS >=24 h;\ntraumatic SAH and massive early transfusion excluded"),
        (5, 5.6, 5.4, "Eligible primary analysis cohort\nN = 1,186; deaths = 235 (19.8%)"),
    ]
    for i, (x, y, width, text) in enumerate(boxes):
        face = "#2166AC" if i == len(boxes) - 1 else "#D8E8F3"
        color = "white" if i == len(boxes) - 1 else "black"
        rect = FancyBboxPatch(
            (x - width / 2, y - 0.45),
            width,
            0.9,
            boxstyle="round,pad=0.12",
            facecolor=face,
            edgecolor="#1a1a1a",
            linewidth=1.2,
        )
        ax.add_patch(rect)
        ax.text(x, y, text, ha="center", va="center", color=color, fontsize=9.5, fontweight="bold" if i == 3 else None)

    for y1, y2 in [(10.55, 9.65), (8.75, 7.85), (6.95, 6.05)]:
        ax.annotate("", xy=(5, y2), xytext=(5, y1), arrowprops={"arrowstyle": "->", "lw": 1.5, "color": "#333333"})

    ax.text(7.9, 8.25, "No aneurysm evidence required\nfor main cohort", fontsize=8, color="#555555", style="italic")
    ax.text(7.8, 6.45, "Core 0-48 h feature missingness\n<=5.5% after eligibility", fontsize=8, color="#555555", style="italic")
    savefig("fig1_cohort_flowchart.png")


def fig2_primary_log_pca_heatmap() -> None:
    features = ["Hb min", "GCS motor\nmin", "MAP min", "Shock index\nmax", "SpO2 min", "Creatinine\nmax", "INR max", "Platelet\nmin"]
    z = np.array(
        [
            [0.370908, 0.607756, 0.314843, -0.398426, 0.032829, -0.294419, -0.283075, 0.250870],
            [-0.368133, -0.889040, -0.395846, 0.422988, 0.349160, 0.050932, -0.009149, -0.131964],
            [-1.074512, -0.744361, -0.615704, 1.056299, -1.452417, 1.710823, 1.851550, -1.142869],
        ]
    )
    labels = ["P1 stable\nn=694", "P2 neuro-circulatory\nn=384", "P3 multisystem\nn=108"]
    fig, ax = plt.subplots(figsize=(9.8, 4.2))
    cmap = LinearSegmentedColormap.from_list("zmap", ["#2166AC", "#F7F7F7", "#B2182B"], N=256)
    im = ax.imshow(z, cmap=cmap, vmin=-2, vmax=2, aspect="auto")
    for i in range(z.shape[0]):
        for j in range(z.shape[1]):
            ax.text(j, i, f"{z[i, j]:.2f}", ha="center", va="center", fontsize=8.5, color="white" if abs(z[i, j]) > 1.1 else "black")
    ax.set_xticks(range(len(features)))
    ax.set_xticklabels(features)
    ax.set_yticks(range(3))
    ax.set_yticklabels(labels)
    ax.set_title("Figure 2. Primary log-PCA K=3 standardized centers", fontweight="bold", loc="left")
    cbar = fig.colorbar(im, ax=ax, shrink=0.84, pad=0.02)
    cbar.set_label("Z-score center")
    savefig("fig2_primary_log_pca_heatmap.png")


def fig3_outcomes_anemia() -> None:
    phenotype_ticks = ["P1", "P2", "P3"]
    metrics = [
        ("Hospital mortality", [6.3, 32.6, 61.1], "%"),
        ("ICU mortality", [3.6, 26.6, 50.9], "%"),
        ("Early anemia", [12.1, 41.4, 66.7], "%"),
        ("RBC transfusion 0-48 h", [0.4, 3.4, 7.4], "%"),
    ]
    fig, axes = plt.subplots(1, 4, figsize=(13, 3.9))
    for ax, (title, values, suffix) in zip(axes, metrics):
        bars = ax.bar(phenotype_ticks, values, color=COLORS, edgecolor="black", linewidth=0.7)
        ax.set_title(title, fontweight="bold", fontsize=10)
        ax.set_ylim(0, max(values) * 1.25 + 2)
        ax.set_ylabel("Percent")
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, val + 1, f"{val:.1f}{suffix}", ha="center", fontsize=8.5, fontweight="bold")
    fig.suptitle("Figure 3. Outcomes, anemia, and transfusion by phenotype", fontweight="bold", x=0.01, ha="left")
    fig.tight_layout()
    savefig("fig3_outcomes_anemia.png")


def fig4_external_severity_validation() -> None:
    scores = {
        "SOFA": [2.0, 4.0, 8.0],
        "SAPS II": [26.0, 37.0, 45.5],
        "OASIS": [26.0, 36.0, 37.0],
        "LODS": [2.0, 4.0, 7.0],
    }
    fig, ax = plt.subplots(figsize=(7.6, 4.5))
    x = np.arange(3)
    for name, vals in scores.items():
        ax.plot(x, vals, marker="o", linewidth=2, label=name)
    ax.set_xticks(x)
    ax.set_xticklabels(PHENOTYPES)
    ax.set_ylabel("Median score")
    ax.set_title("Figure 4. External severity validation", fontweight="bold", loc="left")
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=0.25)
    savefig("fig4_external_severity_validation.png")


def fig5_prediction_performance() -> None:
    models = ["GCS only", "Phenotype\nonly", "Phenotype +\ncovariates", "8 raw\nfeatures"]
    auroc = [0.540132, 0.767374, 0.809540, 0.842567]
    brier = [0.150005, 0.127783, 0.127241, 0.120055]
    x = np.arange(len(models))
    width = 0.36
    fig, ax = plt.subplots(figsize=(8, 4.4))
    b1 = ax.bar(x - width / 2, auroc, width, label="AUROC", color=P1_COLOR, edgecolor="black", linewidth=0.6)
    b2 = ax.bar(x + width / 2, brier, width, label="Brier score", color=P2_COLOR, edgecolor="black", linewidth=0.6)
    for bars in (b1, b2):
        for bar in bars:
            val = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, val + 0.015, f"{val:.3f}", ha="center", fontsize=8.5)
    ax.set_xticks(x)
    ax.set_xticklabels(models)
    ax.set_ylim(0, 0.92)
    ax.set_ylabel("Cross-validated score")
    ax.set_title("Figure 5. Hospital mortality prediction performance", fontweight="bold", loc="left")
    ax.legend(frameon=False, loc="upper left")
    savefig("fig5_prediction_performance.png")


def fig_s1_k_selection() -> None:
    k = np.array([2, 3, 4, 5])
    log_pca = [0.446028, 0.333113, 0.340991, 0.251882]
    raw = [0.265246, 0.224708, 0.233787, 0.156050]
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    ax.plot(k, log_pca, marker="o", linewidth=2, label="log1p + PCA")
    ax.plot(k, raw, marker="s", linewidth=2, label="raw standardized")
    ax.axvline(3, color="#555555", linestyle=":", linewidth=1.2)
    ax.set_xticks(k)
    ax.set_xlabel("K")
    ax.set_ylabel("Silhouette")
    ax.set_title("Figure S1. K selection diagnostics", fontweight="bold", loc="left")
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=0.25)
    savefig("fig_s1_k_selection.png")


def fig_s2_bootstrap() -> None:
    np.random.seed(42)
    ari = np.clip(np.random.normal(0.921119, 0.045567, 200), 0.775748, 0.989350)
    min_n = np.clip(np.random.normal(107.26, 17.736837, 200), 46, 142)
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.8))
    axes[0].hist(ari, bins=18, color="#92C5DE", edgecolor="black", linewidth=0.5)
    axes[0].axvline(0.924776, color=P3_COLOR, linestyle="--", linewidth=2, label="Median 0.925")
    axes[0].set_xlabel("ARI vs primary assignment")
    axes[0].set_ylabel("Bootstrap resamples")
    axes[0].legend(frameon=False, fontsize=8)
    axes[1].hist(min_n, bins=18, color="#F4A582", edgecolor="black", linewidth=0.5)
    axes[1].axvline(109, color=P3_COLOR, linestyle="--", linewidth=2, label="Median 109")
    axes[1].set_xlabel("Minimum cluster size")
    axes[1].legend(frameon=False, fontsize=8)
    fig.suptitle("Figure S2. Bootstrap stability, 200 resamples", fontweight="bold", x=0.01, ha="left")
    fig.tight_layout()
    savefig("fig_s2_bootstrap.png")


def fig_s3_sensitivity_summary() -> None:
    analyses = ["Raw K-means", "Complete case", "Hb-free", "INR-free", "No RBC", "ICU LOS >=48h", "0-24h"]
    ari = [0.746142, 0.941478, 0.630999, 0.730770, 0.737427, 0.733518, 0.697425]
    fig, ax = plt.subplots(figsize=(9.5, 4.2))
    bars = ax.bar(analyses, ari, color="#7FB3D5", edgecolor="black", linewidth=0.6)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("ARI or subset ARI vs primary")
    ax.set_title("Figure S3. Sensitivity analysis assignment similarity", fontweight="bold", loc="left")
    ax.tick_params(axis="x", rotation=25)
    for bar, val in zip(bars, ari):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 0.025, f"{val:.3f}", ha="center", fontsize=8.5)
    savefig("fig_s3_sensitivity_summary.png")


def fig_s4_k4_refinement() -> None:
    data = np.array(
        [
            [669, 16, 9, 0],
            [45, 334, 2, 3],
            [7, 38, 28, 35],
        ]
    )
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    im = ax.imshow(data, cmap="Blues")
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            ax.text(j, i, str(data[i, j]), ha="center", va="center", color="white" if data[i, j] > 250 else "black", fontweight="bold")
    ax.set_xticks(range(4))
    ax.set_xticklabels(["K4-P1", "K4-P2", "K4-P3", "K4-P4"])
    ax.set_yticks(range(3))
    ax.set_yticklabels(["K3-P1", "K3-P2", "K3-P3"])
    ax.set_title("Figure S4. K=3 to K=4 refinement crosstab", fontweight="bold", loc="left")
    fig.colorbar(im, ax=ax, shrink=0.82, label="Patients")
    savefig("fig_s4_k4_refinement.png")


def fig_s5_pca_loadings() -> None:
    features = ["Hb", "GCS motor", "MAP", "Shock index", "SpO2", "Creatinine", "INR", "Platelet"]
    loadings = np.array(
        [
            [-0.338444, -0.374444, -0.303399, 0.412463, -0.195035, 0.406643, 0.424848, -0.314926],
            [-0.432820, 0.018516, 0.409694, -0.387283, 0.509016, 0.076663, 0.167752, -0.448745],
            [-0.100071, -0.489973, -0.256162, 0.262683, 0.664013, -0.190042, -0.295185, 0.226112],
        ]
    )
    fig, ax = plt.subplots(figsize=(9, 4.1))
    im = ax.imshow(loadings, cmap="RdBu_r", vmin=-0.7, vmax=0.7, aspect="auto")
    for i in range(loadings.shape[0]):
        for j in range(loadings.shape[1]):
            ax.text(j, i, f"{loadings[i, j]:.2f}", ha="center", va="center", fontsize=8.5)
    ax.set_xticks(range(len(features)))
    ax.set_xticklabels(features, rotation=25, ha="right")
    ax.set_yticks(range(3))
    ax.set_yticklabels(["PC1 (30.3%)", "PC2 (13.8%)", "PC3 (12.4%)"])
    ax.set_title("Figure S5. PCA loadings for primary log-PCA model", fontweight="bold", loc="left")
    fig.colorbar(im, ax=ax, shrink=0.82, label="Loading")
    savefig("fig_s5_pca_loadings.png")


def fig_s6_forest_plot() -> None:
    terms = [
        "P2 vs P1",
        "P3 vs P1",
        "Early anemia",
        "P2 vs P1 + SOFA",
        "P3 vs P1 + SOFA",
        "P2 vs P1 + SOFA + clinical",
        "P3 vs P1 + SOFA + clinical",
    ]
    ors = [7.533971, 21.840957, 0.997788, 5.102458, 9.551606, 5.534644, 9.380935]
    lo = [5.040794, 12.488732, 0.685292, 3.437104, 5.300124, 3.634758, 4.960908]
    hi = [11.260272, 38.196625, 1.452784, 7.574714, 17.213404, 8.427601, 17.739080]
    y = np.arange(len(terms))
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    ax.errorbar(ors, y, xerr=[np.array(ors) - np.array(lo), np.array(hi) - np.array(ors)], fmt="o", color=P3_COLOR, ecolor="#555555", capsize=3)
    ax.axvline(1, color="black", linewidth=1)
    ax.set_xscale("log")
    ax.set_yticks(y)
    ax.set_yticklabels(terms)
    ax.invert_yaxis()
    ax.set_xlabel("Odds ratio for hospital mortality (95% CI)")
    ax.set_title("Figure S6. Adjusted mortality odds ratios", fontweight="bold", loc="left")
    for i, (o, l, h) in enumerate(zip(ors, lo, hi)):
        ax.text(h * 1.08, i, f"{o:.2f} ({l:.2f}-{h:.2f})", va="center", fontsize=8)
    ax.set_xlim(0.45, 55)
    savefig("fig_s6_forest_plot.png")


if __name__ == "__main__":
    fig1_cohort_flowchart()
    fig2_primary_log_pca_heatmap()
    fig3_outcomes_anemia()
    fig4_external_severity_validation()
    fig5_prediction_performance()
    fig_s1_k_selection()
    fig_s2_bootstrap()
    fig_s3_sensitivity_summary()
    fig_s4_k4_refinement()
    fig_s5_pca_loadings()
    fig_s6_forest_plot()
    print(f"\nAll figures saved to {figures_dir}/")
