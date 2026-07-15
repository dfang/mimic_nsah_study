from pathlib import Path
import re
import subprocess

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


def test_active_files_have_no_dated_dist_paths() -> None:
    active_paths = [
        "AGENTS.md",
        "scripts/prompt_for_regenerating_manuscript.md",
        "scripts/run_non_traumatic_sah_bigquery_pipeline.sh",
        "scripts/generate_manuscript_figures.py",
        "dist/readme.txt",
        "dist/electronic_supplementary_material.md",
    ]
    dated_dist = re.compile(r"dist/[0-9]{8}")
    for path in active_paths:
        assert not dated_dist.search(read_text(path)), path


def test_dist_is_not_ignored_and_has_no_dated_directories() -> None:
    ignored = subprocess.run(
        ["git", "check-ignore", "-q", "dist/analysis_result.md"], cwd=ROOT
    )
    assert ignored.returncode == 1
    assert not any(
        re.fullmatch(r"[0-9]{8}", path.name) for path in (ROOT / "dist").iterdir()
    )
