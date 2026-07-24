import importlib
import os
from pathlib import Path
import re
import subprocess
import sys

import pytest

from scripts.artifact_cli import accept_legacy_date_arg


ROOT = Path(__file__).resolve().parents[1]
DATED_DIST = re.compile(r"dist/(?:[0-9]{8}|YYYYMMDD)")


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


def test_figure_generator_import_is_side_effect_free(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["pytest-host", "--unrelated-host-option"])
    sys.modules.pop("scripts.generate_manuscript_figures", None)

    module = importlib.import_module("scripts.generate_manuscript_figures")
    importlib.reload(module)

    assert not (tmp_path / "dist" / "figures").exists()


def test_failed_pipeline_retains_log_without_replacing_canonical_report(
    tmp_path: Path,
) -> None:
    canonical_report = ROOT / "dist" / "analysis_result.md"
    original_bytes = canonical_report.read_bytes()
    existing_logs = set((ROOT / "dist").glob(".analysis_result.*.md"))
    stub_bin = tmp_path / "bin"
    stub_bin.mkdir()
    python_stub = stub_bin / "python3"
    python_stub.write_text("#!/usr/bin/env bash\necho 'forced python failure' >&2\nexit 23\n")
    python_stub.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{stub_bin}{os.pathsep}{env['PATH']}"
    retained_logs: set[Path] = set()
    try:
        result = subprocess.run(
            [
                "bash",
                "scripts/run_non_traumatic_sah_bigquery_pipeline.sh",
                "--analysis-only",
            ],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
        )
        retained_logs = (
            set((ROOT / "dist").glob(".analysis_result.*.md")) - existing_logs
        )

        assert result.returncode == 23
        assert canonical_report.read_bytes() == original_bytes
        assert len(retained_logs) == 1
        retained_log = next(iter(retained_logs))
        assert str(retained_log.relative_to(ROOT)) in result.stderr
        assert retained_log.read_text(encoding="utf-8").rstrip().endswith("```")
    finally:
        canonical_report.write_bytes(original_bytes)
        for retained_log in retained_logs:
            retained_log.unlink(missing_ok=True)


def test_successful_pipeline_publishes_canonical_report_with_public_mode(
    tmp_path: Path,
) -> None:
    canonical_report = ROOT / "dist" / "analysis_result.md"
    original_bytes = canonical_report.read_bytes()
    original_mode = canonical_report.stat().st_mode & 0o777
    existing_logs = set((ROOT / "dist").glob(".analysis_result.*.md"))
    stub_bin = tmp_path / "bin"
    stub_bin.mkdir()
    python_stub = stub_bin / "python3"
    python_stub.write_text(
        "#!/usr/bin/env bash\necho 'stubbed analysis completed successfully'\n"
    )
    python_stub.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{stub_bin}{os.pathsep}{env['PATH']}"
    try:
        result = subprocess.run(
            [
                "bash",
                "scripts/run_non_traumatic_sah_bigquery_pipeline.sh",
                "--analysis-only",
            ],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
        )
        new_logs = set((ROOT / "dist").glob(".analysis_result.*.md")) - existing_logs
        published = canonical_report.read_text(encoding="utf-8")

        assert result.returncode == 0
        assert "stubbed analysis completed successfully" in result.stdout
        assert "stubbed analysis completed successfully" in published
        assert published.rstrip().endswith("```")
        assert canonical_report.stat().st_mode & 0o777 == 0o644
        assert new_logs == set()
    finally:
        canonical_report.write_bytes(original_bytes)
        canonical_report.chmod(original_mode)
        for temporary_log in (
            set((ROOT / "dist").glob(".analysis_result.*.md")) - existing_logs
        ):
            temporary_log.unlink(missing_ok=True)


def test_active_files_have_no_dated_dist_paths() -> None:
    active_paths = [
        "AGENTS.md",
        "scripts/prompt_for_regenerating_manuscript.md",
        "scripts/run_non_traumatic_sah_bigquery_pipeline.sh",
        "scripts/generate_manuscript_figures.py",
        "dist/readme.txt",
        "dist/electronic_supplementary_material.md",
    ]
    for path in active_paths:
        assert not DATED_DIST.search(read_text(path)), path


@pytest.mark.parametrize(
    "path",
    ["dist/20260711/analysis_result.md", "dist/YYYYMMDD/analysis_result.md"],
)
def test_dated_dist_pattern_matches_legacy_forms(path: str) -> None:
    assert DATED_DIST.search(path)


def test_dist_is_not_ignored_and_has_no_dated_directories() -> None:
    ignored = subprocess.run(
        ["git", "check-ignore", "-q", "dist/analysis_result.md"], cwd=ROOT
    )
    assert ignored.returncode == 1
    assert not any(
        re.fullmatch(r"[0-9]{8}", path.name) for path in (ROOT / "dist").iterdir()
    )
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "dist"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    allowed_generated_artifacts = {
        "dist/pdf/generation-manifest.yaml",
        "dist/pdf/resolved/electronic_supplementary_material.html",
        "dist/pdf/resolved/manuscript_non_traumatic_sah_phenotypes_cn.html",
        "dist/pdf/resolved/manuscript_non_traumatic_sah_phenotypes_en.html",
        "dist/pdf/resolved/strobe_checklist.html",
    }
    unexpected = set(untracked.stdout.splitlines()) - allowed_generated_artifacts
    assert unexpected == set()
