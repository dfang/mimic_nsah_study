from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_pdf_converter_uses_stable_dist_directory() -> None:
    script = read_text("scripts/convert_manuscript_to_pdf.py")

    assert 'base = "dist"' in script
    assert "date_dir" not in script
    assert "datetime" not in script
    assert "sys.argv" not in script


def test_active_instructions_use_canonical_manuscript_paths() -> None:
    agents = read_text("AGENTS.md")
    prompt = read_text("scripts/prompt_for_regenerating_manuscript.md")

    assert "`dist/manuscript_non_traumatic_sah_phenotypes.md`" in agents
    assert "`dist/pdf/`" in agents
    assert "dist/YYYYMMDD/manuscript_non_traumatic_sah_phenotypes" not in prompt
    assert "dist/YYYYMMDD/electronic_supplementary_material" not in prompt
    assert "dist/YYYYMMDD/strobe_checklist" not in prompt
    assert "convert_manuscript_to_pdf.py YYYYMMDD" not in prompt


def test_canonical_manuscripts_reference_dated_figures() -> None:
    english = read_text("dist/manuscript_non_traumatic_sah_phenotypes.md")
    chinese = read_text("dist/manuscript_non_traumatic_sah_phenotypes_cn.md")
    supplement = read_text("dist/electronic_supplementary_material.md")

    for document in (english, chinese, supplement):
        assert "](figures/" not in document
        assert "](20260711/figures/" in document
