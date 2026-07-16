from pathlib import Path
import re

import matplotlib.pyplot as plt
from PIL import Image

from scripts import generate_manuscript_figures as figures


def test_savefig_writes_600_dpi_png_and_vector_pdf(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(figures, "figures_dir", str(tmp_path))
    plt.figure(figsize=(1, 1))
    plt.plot([0, 1], [0, 1])

    figures.savefig("test_figure.png")

    png_path = tmp_path / "test_figure.png"
    pdf_path = tmp_path / "test_figure.pdf"
    assert png_path.is_file()
    assert pdf_path.is_file()
    with Image.open(png_path) as image:
        dpi_x, dpi_y = image.info["dpi"]
    assert dpi_x >= 599
    assert dpi_y >= 599


def test_submission_figures_do_not_embed_conflicting_numbers(monkeypatch) -> None:
    captured_titles: list[str] = []

    def capture_and_close(_name: str) -> None:
        figure = plt.gcf()
        if figure._suptitle is not None:
            captured_titles.append(figure._suptitle.get_text())
        captured_titles.extend(ax.get_title() for ax in figure.axes if ax.get_title())
        plt.close(figure)

    mimic_rows = [
        {"step": step, "admissions": "100", "patients": "90"}
        for step in figures.MIMIC_STEP_LABELS
    ]
    eicu_rows = [
        {"step": step, "unit_stays": "100", "patients": "90"}
        for step in figures.EICU_STEP_LABELS
    ]
    monkeypatch.setattr(
        figures,
        "_load_cohort_flow_data",
        lambda: {"mimic": mimic_rows, "eicu": eicu_rows},
    )
    monkeypatch.setattr(figures, "savefig", capture_and_close)

    figures.fig1_cohort_flowchart()
    figures.fig2_primary_log_pca_heatmap()
    figures.fig3_outcomes_anemia()
    figures.fig4_external_severity_validation()

    assert captured_titles
    assert not any(re.match(r"^Figure\s+\d+\.", title) for title in captured_titles)
