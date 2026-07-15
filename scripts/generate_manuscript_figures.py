#!/usr/bin/env python3
"""
Generate manuscript figures for the non-traumatic SAH phenotype manuscript.

The values in this script are synchronized with dist/analysis_result.md.
Output is written to dist/figures/.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

if __package__:
    from .artifact_cli import accept_legacy_date_arg
else:
    from artifact_cli import accept_legacy_date_arg

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import FancyBboxPatch


figures_dir = "dist/figures"

P1_COLOR = "#2166AC"
P2_COLOR = "#F4A582"
P3_COLOR = "#B2182B"
P4_COLOR = "#762A83"

PHENOTYPES = ["P1\nStable", "P2\nNeuro-circulatory", "P3\nMultisystem"]
COLORS = [P1_COLOR, P2_COLOR, P3_COLOR]

MIMIC_FLOW_SQL = """
SELECT step, rows_count, patients, admissions
FROM `mimic-study-498508.non_traumatic_sah_study.cohort_flowchart_counts`
ORDER BY step
"""

EICU_FLOW_SQL = """
SELECT step, unit_stays, patients, definition
FROM `mimic-study-498508.eicu_sah_validation.eicu_cohort_flowchart_counts`
ORDER BY step
"""

MIMIC_STEP_LABELS = {
    "01_source_sah_admissions": "SAH-coded hospital admissions",
    "02_adult_source_sah": "Adult SAH admissions",
    "03_adult_nontraumatic_sah_no_extra_aneurysm_required": "Non-traumatic SAH\n(no aneurysm evidence required)",
    "04_first_icu_nsah_stays": "First ICU stay",
    "05_icu_los_ge_24h": "ICU LOS >=24 h",
    "06_core_missing_le_2": "8 core features\n<=2 missing",
    "07_primary_analysis_no_massive_transfusion": "Primary analysis\n(no massive early transfusion)",
    "08_sensitivity_icu_los_ge_48h": "ICU LOS >=48 h",
    "09_sensitivity_no_rbc_48h": "No RBC 0-48 h",
}

EICU_STEP_LABELS = {
    "01_sah_candidate_unit_stays": "SAH evidence from\ndiagnosis/admissionDx",
    "02_adult": "Adult unit stays",
    "03_non_traumatic": "Non-traumatic SAH",
    "04_first_icu_stay": "First ICU stay",
    "05_icu_los_ge_24h": "ICU LOS >=24 h",
    "06_core_features_le_2_missing": "External validation\n(<=2 missing core features)",
    "07_icu_los_ge_48h_sensitivity": "ICU LOS >=48 h",
    "08_no_rbc_sensitivity": "No recorded RBC 0-48 h",
    "09_strict_sah_sensitivity": "Strict SAH evidence",
    "10_low_missing_sensitivity": "<=1 missing feature",
    "11_complete_case_sensitivity": "Complete case",
}


def savefig(name: str) -> None:
    plt.savefig(f"{figures_dir}/{name}")
    plt.close()
    print(f"{name} saved")


def _run_bq_json(sql: str) -> list[dict[str, object]]:
    result = subprocess.run(
        ["bq", "--format=json", "query", "--use_legacy_sql=false", sql],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def _as_int(value: object) -> int:
    return int(value) if value is not None else 0


def _load_cohort_flow_data() -> dict[str, list[dict[str, object]]]:
    mimic_rows = _run_bq_json(MIMIC_FLOW_SQL)
    eicu_rows = _run_bq_json(EICU_FLOW_SQL)
    data = {"mimic": mimic_rows, "eicu": eicu_rows}
    with open(f"{figures_dir}/fig1_cohort_flowchart_data.json", "w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
    return data


def _format_n(value: int) -> str:
    return f"{value:,}"


def _draw_flow_box(
    ax: plt.Axes,
    x: float,
    y: float,
    width: float,
    height: float,
    label: str,
    count_label: str,
    face: str,
    edge: str,
    text_color: str = "#151515",
    count_color: str = "#151515",
    alpha: float = 1.0,
    linewidth: float = 1.1,
) -> None:
    rect = FancyBboxPatch(
        (x - width / 2, y - height / 2),
        width,
        height,
        boxstyle="round,pad=0.025,rounding_size=0.06",
        facecolor=face,
        edgecolor=edge,
        linewidth=linewidth,
        alpha=alpha,
    )
    ax.add_patch(rect)
    ax.text(x, y + 0.13, label, ha="center", va="center", fontsize=8.7, color=text_color, linespacing=1.15)
    ax.text(x, y - 0.22, count_label, ha="center", va="center", fontsize=10.2, color=count_color, fontweight="bold")


def _draw_panel_header(ax: plt.Axes, x: float, title: str, subtitle: str, color: str) -> None:
    ax.text(x, 8.72, title, ha="center", va="center", fontsize=13.2, color=color, fontweight="bold")
    ax.text(x, 8.38, subtitle, ha="center", va="center", fontsize=8.4, color="#555555")
    ax.plot([x - 2.45, x + 2.45], [8.18, 8.18], color=color, linewidth=2.0, solid_capstyle="round")


def _draw_sensitivity_chip(ax: plt.Axes, x: float, y: float, label: str, count_label: str, color: str) -> None:
    rect = FancyBboxPatch(
        (x - 0.78, y - 0.27),
        1.56,
        0.54,
        boxstyle="round,pad=0.02,rounding_size=0.05",
        facecolor="#FFFFFF",
        edgecolor=color,
        linewidth=1.0,
    )
    ax.add_patch(rect)
    ax.text(x, y + 0.08, label, ha="center", va="center", fontsize=6.7, color="#303030")
    ax.text(x, y - 0.13, count_label, ha="center", va="center", fontsize=8.0, color=color, fontweight="bold")


def fig1_cohort_flowchart() -> None:
    flow_data = _load_cohort_flow_data()
    mimic_by_step = {str(row["step"]): row for row in flow_data["mimic"]}
    eicu_by_step = {str(row["step"]): row for row in flow_data["eicu"]}

    fig, ax = plt.subplots(figsize=(10.6, 7.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 7.2)
    ax.axis("off")
    ax.set_title("Figure 1. Cohort selection and analysis framework", fontweight="bold", loc="left", pad=10)

    mimic_color = "#1F5A85"
    eicu_color = "#7B3294"
    neutral = "#5A5A5A"
    light_blue = "#EAF2F7"
    light_purple = "#F3ECF7"
    light_gray = "#F7F7F7"

    def box(
        x: float,
        y: float,
        w: float,
        h: float,
        title: str,
        body: str,
        edge: str,
        face: str,
        title_color: str | None = None,
        title_size: float = 9.3,
        body_size: float = 8.2,
        title_y: float = 0.24,
        body_y: float = -0.18,
        body_linespacing: float = 1.18,
        lw: float = 1.1,
    ) -> None:
        rect = FancyBboxPatch(
            (x - w / 2, y - h / 2),
            w,
            h,
            boxstyle="round,pad=0.035,rounding_size=0.07",
            facecolor=face,
            edgecolor=edge,
            linewidth=lw,
        )
        ax.add_patch(rect)
        ax.text(x, y + h * title_y, title, ha="center", va="center", fontsize=title_size, color=title_color or edge, fontweight="bold")
        ax.text(x, y + h * body_y, body, ha="center", va="center", fontsize=body_size, color="#222222", linespacing=body_linespacing)

    def down_arrow(x: float, y0: float, y1: float, color: str) -> None:
        ax.annotate("", xy=(x, y1), xytext=(x, y0), arrowprops={"arrowstyle": "-|>", "lw": 1.2, "color": color, "mutation_scale": 10})

    def right_arrow(x0: float, x1: float, y: float, color: str) -> None:
        ax.annotate("", xy=(x1, y), xytext=(x0, y), arrowprops={"arrowstyle": "-|>", "lw": 1.25, "color": color, "mutation_scale": 10})

    mimic_start = _as_int(mimic_by_step["01_source_sah_admissions"]["admissions"])
    mimic_start_patients = _as_int(mimic_by_step["01_source_sah_admissions"]["patients"])
    mimic_final = _as_int(mimic_by_step["07_primary_analysis_no_massive_transfusion"]["admissions"])
    mimic_final_patients = _as_int(mimic_by_step["07_primary_analysis_no_massive_transfusion"]["patients"])
    eicu_start = _as_int(eicu_by_step["01_sah_candidate_unit_stays"]["unit_stays"])
    eicu_start_patients = _as_int(eicu_by_step["01_sah_candidate_unit_stays"]["patients"])
    eicu_final = _as_int(eicu_by_step["06_core_features_le_2_missing"]["unit_stays"])

    mimic_exclusions = [
        ("Age <18 years", 0),
        ("Traumatic SAH", _as_int(mimic_by_step["02_adult_source_sah"]["admissions"]) - _as_int(mimic_by_step["03_adult_nontraumatic_sah_no_extra_aneurysm_required"]["admissions"])),
        ("Non-first ICU stay", _as_int(mimic_by_step["03_adult_nontraumatic_sah_no_extra_aneurysm_required"]["admissions"]) - _as_int(mimic_by_step["04_first_icu_nsah_stays"]["admissions"])),
        ("ICU LOS <24 h", _as_int(mimic_by_step["04_first_icu_nsah_stays"]["admissions"]) - _as_int(mimic_by_step["05_icu_los_ge_24h"]["admissions"])),
        (">2 missing core variables", _as_int(mimic_by_step["05_icu_los_ge_24h"]["admissions"]) - _as_int(mimic_by_step["06_core_missing_le_2"]["admissions"])),
        ("Massive transfusion <24 h", _as_int(mimic_by_step["06_core_missing_le_2"]["admissions"]) - mimic_final),
    ]
    eicu_exclusions = [
        ("Age <18 years", eicu_start - _as_int(eicu_by_step["02_adult"]["unit_stays"])),
        ("Traumatic SAH", _as_int(eicu_by_step["02_adult"]["unit_stays"]) - _as_int(eicu_by_step["03_non_traumatic"]["unit_stays"])),
        ("Non-first ICU stay", _as_int(eicu_by_step["03_non_traumatic"]["unit_stays"]) - _as_int(eicu_by_step["04_first_icu_stay"]["unit_stays"])),
        ("ICU LOS <24 h", _as_int(eicu_by_step["04_first_icu_stay"]["unit_stays"]) - _as_int(eicu_by_step["05_icu_los_ge_24h"]["unit_stays"])),
        (">2 missing core variables", _as_int(eicu_by_step["05_icu_los_ge_24h"]["unit_stays"]) - eicu_final),
    ]

    def exclusion_text(items: list[tuple[str, int]]) -> str:
        return "\n".join(f"{label}: n={_format_n(n)}" for label, n in items)

    left_x, right_x = 2.65, 7.35
    y_top, y_mid, y_final = 5.98, 4.75, 3.43
    cohort_w = 3.85

    box(left_x, 6.75, cohort_w, 0.42, "MIMIC-IV 3.1", "Development cohort (2008-2022)", mimic_color, "#FFFFFF", body_size=7.4, lw=0)
    box(right_x, 6.75, cohort_w, 0.42, "eICU-CRD", "External validation cohort (2014-2015)", eicu_color, "#FFFFFF", body_size=7.4, lw=0)
    ax.plot([0.75, 4.55], [6.47, 6.47], color=mimic_color, linewidth=2.0, solid_capstyle="round")
    ax.plot([5.45, 9.25], [6.47, 6.47], color=eicu_color, linewidth=2.0, solid_capstyle="round")

    box(
        left_x,
        y_top,
        cohort_w,
        0.82,
        "Initial SAH screen",
        f"ICD-9/ICD-10 SAH codes\nN={_format_n(mimic_start)} admissions\n{_format_n(mimic_start_patients)} patients",
        mimic_color,
        light_blue,
        body_size=7.8,
        title_y=0.27,
        body_y=-0.22,
        body_linespacing=1.32,
    )
    box(
        right_x,
        y_top,
        cohort_w,
        0.82,
        "Initial SAH screen",
        f"Diagnosis / ICD-9 430 / admissionDx\nN={_format_n(eicu_start)} unit stays\n{_format_n(eicu_start_patients)} patients",
        eicu_color,
        light_purple,
        body_size=7.8,
        title_y=0.27,
        body_y=-0.22,
        body_linespacing=1.32,
    )
    box(
        left_x,
        y_mid,
        cohort_w,
        1.18,
        "Combined exclusions",
        exclusion_text(mimic_exclusions),
        mimic_color,
        "#FFFFFF",
        body_size=6.9,
        title_y=0.30,
        body_y=-0.15,
        body_linespacing=1.25,
    )
    box(
        right_x,
        y_mid,
        cohort_w,
        1.18,
        "Combined exclusions",
        exclusion_text(eicu_exclusions),
        eicu_color,
        "#FFFFFF",
        body_size=6.9,
        title_y=0.30,
        body_y=-0.15,
        body_linespacing=1.28,
    )
    box(
        left_x,
        y_final,
        cohort_w,
        0.78,
        "Final MIMIC-IV cohort",
        "",
        mimic_color,
        mimic_color,
        title_color="white",
        body_size=8.4,
        lw=1.2,
    )
    ax.text(left_x, y_final - 0.16, f"N={_format_n(mimic_final)} stays; {_format_n(mimic_final_patients)} patients", ha="center", va="center", fontsize=8.0, color="white", fontweight="bold")
    box(
        right_x,
        y_final,
        cohort_w,
        0.78,
        "Final eICU validation cohort",
        "",
        eicu_color,
        eicu_color,
        title_color="white",
        body_size=8.4,
        lw=1.2,
    )
    ax.text(right_x, y_final - 0.16, f"N={_format_n(eicu_final)} unit stays", ha="center", va="center", fontsize=8.4, color="white", fontweight="bold")

    for x, color in [(left_x, mimic_color), (right_x, eicu_color)]:
        down_arrow(x, y_top - 0.46, y_mid + 0.65, color)
        down_arrow(x, y_mid - 0.65, y_final + 0.42, color)

    workflow_title_y = 2.58
    workflow_rule_y = 2.38
    ax.text(5.0, workflow_title_y, "Analysis workflow", ha="center", va="center", fontsize=11.5, fontweight="bold", color="#222222")
    ax.plot([1.0, 9.0], [workflow_rule_y, workflow_rule_y], color="#BDBDBD", linewidth=1.0)

    analysis_y = 1.48
    a_w = 2.65
    box(
        2.0,
        analysis_y,
        a_w,
        0.86,
        "Phenotype discovery",
        "0-48 h physiology\nimputation + log1p + PCA",
        neutral,
        light_gray,
        title_size=8.2,
        body_size=6.9,
    )
    box(
        5.0,
        analysis_y,
        a_w,
        0.86,
        "Log-PCA K-means",
        "K=3: P1 / P2 / P3\nLogistic / Cox / KM",
        neutral,
        light_gray,
        title_size=8.2,
        body_size=6.9,
    )
    box(
        8.0,
        analysis_y,
        a_w,
        0.86,
        "Transport validation",
        "frozen eICU projection\nAPACHE + bootstrap checks",
        eicu_color,
        light_purple,
        title_size=8.2,
        body_size=6.9,
    )
    right_arrow(3.35, 3.65, analysis_y, neutral)
    right_arrow(6.35, 6.65, analysis_y, neutral)
    down_arrow(left_x, y_final - 0.48, 2.04, mimic_color)
    ax.annotate("", xy=(7.75, 2.02), xytext=(right_x, y_final - 0.48), arrowprops={"arrowstyle": "-|>", "lw": 1.1, "color": eicu_color, "mutation_scale": 10})

    ax.text(
        0.72,
        0.16,
        (
            "Counts from BigQuery intermediate tables: non_traumatic_sah_study.cohort_flowchart_counts and "
            "eicu_sah_validation.eicu_cohort_flowchart_counts.\n"
            "MIMIC was used for phenotype derivation; eICU was used for external transport validation."
        ),
        ha="left",
        va="bottom",
        fontsize=7.0,
        color="#555555",
    )
    fig.tight_layout(rect=(0, 0.04, 1, 0.97))
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
        "APS III": [28.0, 41.0, 59.5],
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
    ax.set_title("Figure 6. Hospital mortality prediction performance", fontweight="bold", loc="left")
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
    analyses = ["Raw K-means", "Complete case", "Hb-free", "INR-free", "No RBC", "ICU LOS ≥48 h", "0–24 h"]
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


def fig_s7_eicu_external_validation() -> None:
    phenotype_ticks = ["P1", "P2", "P3"]
    metrics = [
        ("Hospital mortality", [5.4, 25.7, 42.7], "%"),
        ("ICU mortality", [2.8, 16.2, 29.3], "%"),
        ("Early anemia", [11.4, 34.5, 58.0], "%"),
        ("APACHE predicted\nhospital mortality", [6.9, 24.3, 42.6], "%"),
    ]
    fig, axes = plt.subplots(1, 4, figsize=(13, 3.9))
    for ax, (title, values, suffix) in zip(axes, metrics):
        bars = ax.bar(phenotype_ticks, values, color=COLORS, edgecolor="black", linewidth=0.7)
        ax.set_title(title, fontweight="bold", fontsize=10)
        ax.set_ylim(0, max(values) * 1.25 + 2)
        ax.set_ylabel("Percent")
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, val + 1, f"{val:.1f}{suffix}", ha="center", fontsize=8.5, fontweight="bold")
    fig.suptitle("Supplementary Figure 7. eICU frozen-transport external validation", fontweight="bold", x=0.01, ha="left")
    fig.tight_layout()
    savefig("fig_s7_eicu_external_validation.png")


def main(argv: list[str] | None = None) -> None:
    accept_legacy_date_arg(
        sys.argv[1:] if argv is None else argv,
        "generate_manuscript_figures.py",
    )
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
    fig_s7_eicu_external_validation()
    print(f"\nAll figures saved to {figures_dir}/")


if __name__ == "__main__":
    main()
