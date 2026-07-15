from pathlib import Path

import pytest

from scripts.artifact_cli import accept_legacy_date_arg


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_no_legacy_date_argument_is_silent(capsys: pytest.CaptureFixture[str]) -> None:
    accept_legacy_date_arg([], "generator")
    assert capsys.readouterr().err == ""


def test_legacy_date_argument_warns_and_is_ignored(
    capsys: pytest.CaptureFixture[str],
) -> None:
    accept_legacy_date_arg(["20260711"], "generator")
    assert "deprecated" in capsys.readouterr().err.lower()


@pytest.mark.parametrize("args", [["not-a-date"], ["20260711", "extra"]])
def test_invalid_legacy_arguments_fail(args: list[str]) -> None:
    with pytest.raises(SystemExit, match="Usage"):
        accept_legacy_date_arg(args, "generator")


def test_generators_use_canonical_output_paths() -> None:
    pipeline = read_text("scripts/run_non_traumatic_sah_bigquery_pipeline.sh")
    figures = read_text("scripts/generate_manuscript_figures.py")
    converter = read_text("scripts/convert_manuscript_to_pdf.py")

    assert 'output_file="dist/analysis_result.md"' in pipeline
    assert 'figures_dir = "dist/figures"' in figures
    assert 'base = "dist"' in converter
    assert "date_dir" not in pipeline
    assert "date_dir" not in figures
    assert "date_dir" not in converter
