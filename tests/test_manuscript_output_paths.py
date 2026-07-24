from pathlib import Path
import re

import pytest

from scripts.convert_manuscript_to_pdf import CSS_EN, convert, preprocess_markdown


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_pdf_converter_uses_stable_dist_directory() -> None:
    script = read_text("scripts/convert_manuscript_to_pdf.py")

    assert 'base = "dist"' in script
    assert "date_dir" not in script
    assert "datetime" not in script


def test_pdf_converter_rebuilds_bilingual_manuscript_and_supporting_files() -> None:
    script = read_text("scripts/convert_manuscript_to_pdf.py")

    assert "resolve_citations" in script
    assert "--citeproc" in script
    assert "--fail-if-warnings" in script
    assert "--to=html5" in script
    assert "convert_resolved_html" in script
    for expected in (
        "manuscript_non_traumatic_sah_phenotypes_en.pdf",
        "manuscript_non_traumatic_sah_phenotypes_cn.pdf",
        "electronic_supplementary_material.pdf",
        "strobe_checklist.pdf",
    ):
        assert expected in script


def test_active_instructions_use_canonical_manuscript_paths() -> None:
    agents = read_text("AGENTS.md")
    prompt = read_text("scripts/prompt_for_regenerating_manuscript.md")

    assert "`dist/manuscript_non_traumatic_sah_phenotypes.md`" in agents
    assert "`dist/pdf/`" in agents
    assert "`dist/manuscript_non_traumatic_sah_phenotypes_cited.md`" in prompt
    assert "dist/YYYYMMDD/manuscript_non_traumatic_sah_phenotypes" not in prompt
    assert "dist/YYYYMMDD/electronic_supplementary_material" not in prompt
    assert "dist/YYYYMMDD/strobe_checklist" not in prompt
    assert "convert_manuscript_to_pdf.py YYYYMMDD" not in prompt


def test_bilingual_manuscripts_and_esm_reference_canonical_figures() -> None:
    english = read_text("dist/manuscript_non_traumatic_sah_phenotypes_cited.md")
    chinese = read_text("dist/manuscript_non_traumatic_sah_phenotypes_cn_cited.md")
    supplement = read_text("dist/electronic_supplementary_material.md")

    for document in (english, chinese, supplement):
        assert "](figures/" in document
        assert "](20260711/figures/" not in document


def test_reviewed_english_abstract_and_frozen_results_are_consistent() -> None:
    english = read_text("dist/manuscript_non_traumatic_sah_phenotypes_cited.md")
    supplement = read_text("dist/electronic_supplementary_material.md")

    abstract = english.split("## Structured abstract", 1)[1].split("**Keywords:**", 1)[0]
    abstract_body = re.sub(r"^### .+$", "", abstract, flags=re.MULTILINE)
    abstract_words = abstract_body.split()
    take_home = english.split("## Take-home message", 1)[1].split("## Structured abstract", 1)[0]
    take_home_words = take_home.split()

    assert 150 <= len(abstract_words) <= 250
    assert len(take_home_words) <= 65
    assert all(f"### {heading}" in abstract for heading in ("Purpose", "Methods", "Results", "Conclusion"))
    assert "### Conclusions" not in abstract

    for expected in (
        "1,186 ICU stays from 1,173",
        "K=2 to K=5",
        "0.8554",
        "539, 222, and 82",
        "-0.0017",
        "post hoc exploratory sensitivity analysis",
    ):
        assert expected in english

    for stale in (
        "1,186 patients",
        "K=2 to K=6",
        "0.920",
        "540 patients",
        "221 to P2",
        "prespecified sensitivity",
        "In unadjusted Cox",
        "a priori",
        "before outcome analyses",
        "selected because it provided the best balance",
        "We hypothesized",
    ):
        assert stale not in english

    for required_boundary in (
        "post-outcome exploratory",
        "unadjusted for multiplicity",
        "49.4%",
        "390 of 843 transported patients (46.3%)",
        "stay-level model covariance",
        "not clustered by `subject_id`",
        "no red-cell threshold was applied because eICU transfusion units were heterogeneous",
        "The process-of-care model was rank deficient and was not interpreted",
    ):
        assert required_boundary in english

    assert "—" not in english
    assert "–" not in english

    assert "ESM Note 1. Time-to-event analysis boundary" in supplement
    assert "ESM Table 10. Exploratory eICU frozen-transport" in supplement
    assert "ESM Table 10. Cox" not in supplement
    assert "fig4_external_severity_validation" not in english
    assert "fig_s7_eicu_external_validation" not in supplement
    assert "**ESM Fig. 6.** Cohort selection and analysis design" in supplement


def test_chinese_cited_manuscript_is_aligned_with_reviewed_english_source() -> None:
    english = read_text("dist/manuscript_non_traumatic_sah_phenotypes_cited.md")
    chinese = read_text("dist/manuscript_non_traumatic_sah_phenotypes_cn_cited.md")

    citation_keys = lambda text: set(re.findall(r"@([A-Za-z0-9_:-]+)", text))
    figure_paths = lambda text: re.findall(r"\]\((figures/[^)]+)\)", text)

    assert citation_keys(chinese) == citation_keys(english)
    assert len(citation_keys(chinese)) == 18
    assert figure_paths(chinese) == figure_paths(english)

    for expected in (
        "1,173 例患者、1,186 次 ICU 住院",
        "K=2 至 K=5",
        "0.8554",
        "539、222 和 82",
        "-0.0017",
        "1.54（1.06-2.22）",
        "事后、探索性敏感性分析",
        "ESM 图 6",
        "time-to-event 分析边界",
    ):
        assert expected in chinese

    for stale in (
        "开发队列纳入 1,186 例患者",
        "540 例",
        "221 例",
        "0.920",
        "-0.003",
        "Cox",
        "ESM 图 8",
        "fig4_external_severity_validation",
        "作为外部验证队列",
        "预先选择",
        "我们假设",
    ):
        assert stale not in chinese

    for required_boundary in (
        "结局访问后探索性",
        "P 值未经多重性校正",
        "49.4%",
        "390/843 例（46.3%）",
        "ICU 住院层面的模型协方差",
        "未按 `subject_id` 聚类",
        "由于 eICU 输血计量单位不一致，未设置红细胞输注硬排除",
        "秩亏的诊疗过程模型未作推断性解释",
    ):
        assert required_boundary in chinese

    assert "—" not in chinese
    assert "–" not in chinese

    assert all(f"### {heading}" in chinese for heading in ("目的", "方法", "结果", "结论"))
    assert "## 声明" in chinese
    assert "## 电子补充材料" in chinese


def test_supplement_does_not_present_rank_deficient_process_model_as_inference() -> None:
    supplement = read_text("dist/electronic_supplementary_material.md")

    assert "ESM Table 9. Implemented exploratory logistic regression" in supplement
    assert "Model 2 aOR" not in supplement
    assert "0.000–inf" not in supplement
    assert "is not presented as an inferential result" in supplement
    assert "390 (46.3%) had missing INR" in supplement


def test_preprocess_resolves_canonical_relative_figure_path(tmp_path: Path) -> None:
    manuscript = tmp_path / "manuscript.md"
    manuscript.write_text("![Figure](figures/figure.png)", encoding="utf-8")

    result = preprocess_markdown(manuscript)

    assert f"](file://{tmp_path}/figures/figure.png)" in result


def test_pdf_conversion_refuses_unresolved_pandoc_citations(tmp_path: Path) -> None:
    manuscript = tmp_path / "manuscript.md"
    manuscript.write_text("A claim [@verified_key].\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="citeproc-resolved"):
        convert(manuscript, tmp_path / "manuscript.pdf", CSS_EN)

    assert not (tmp_path / "manuscript.pdf").exists()
