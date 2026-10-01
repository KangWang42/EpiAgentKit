import importlib.util
import re
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "scan_placeholders", ROOT / "skills/academic-publishing/scripts/scan_placeholders.py"
)
scan_placeholders = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = scan_placeholders
SPEC.loader.exec_module(scan_placeholders)


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def r_code(text: str) -> str:
    return "\n".join(re.findall(r"```r\n(.*?)```", text, flags=re.S))


class StatisticalReferenceTests(unittest.TestCase):
    def test_survival_reference_avoids_known_errors(self) -> None:
        survival = read("skills/r-biostats/references/survival.md")
        self.assertNotIn("P > 0.05 表示满足", survival)
        self.assertIn("plot(zph)", survival)
        self.assertIn("quantile(fit, probs = 0.5)", survival)
        self.assertNotIn('summary(fit)$table[, "median"]', survival)
        self.assertIn("tt = function(x, t, ...)", survival)
        self.assertIn("病因别 Cox", survival)
        self.assertIn("删失为第一水平", survival)

    def test_meta_reference_reports_heterogeneity_without_fixed_cutoffs(self) -> None:
        meta = read("skills/r-biostats/references/meta.md")
        self.assertNotRegex(meta, r"I²\s*>\s*50%\s*[:：]")
        self.assertIn("prediction = TRUE", meta)
        self.assertIn('method.random.ci = "HK"', meta)
        self.assertIn("k.min = 10", meta)

    def test_mediation_reference_states_identification_assumptions(self) -> None:
        mediation = read("skills/r-biostats/references/mediation.md")
        self.assertIn("无未测混杂", mediation)
        self.assertIn("exposure * mediator", mediation)
        self.assertIn("medsens", mediation)
        self.assertIn("方向相反", mediation)

    def test_prognostic_code_runs_with_required_arguments(self) -> None:
        code = r_code(read("skills/r-biostats/references/prognostic-models.md"))
        self.assertIn("x = TRUE", code)
        self.assertNotRegex(code, r"~\s*\.\s*,\s*data")
        self.assertNotIn("VIF>10", code)
        self.assertNotIn("win <- win", code)

    def test_regression_reference_distinguishes_or_from_rr(self) -> None:
        regression = read("skills/r-biostats/references/regression.md")
        self.assertIn('family = poisson(link = "log")', regression)
        self.assertIn("sandwich::vcovHC", regression)

    def test_visualization_uses_shared_figure_helpers(self) -> None:
        code = r_code(read("skills/r-biostats/references/visualization.md"))
        self.assertNotIn("geom_errorbarh(", code)
        self.assertIn('orientation = "y"', code)
        self.assertIn("theme_pub(", code)
        self.assertIn("ragg::agg_png", code)
        self.assertNotIn("theme_cn", code)


class CodeStyleTests(unittest.TestCase):
    def test_code_style_teaches_current_tidyverse_idioms(self) -> None:
        style = read("skills/r-biostats/references/code-style.md")
        for fragment in (
            "新脚本使用原生管道 `|>`",
            ".by = ",
            "list_rbind()",
            "possibly(",
            "pmap()",
            "nest(.by = ",
            "broom::tidy()",
            'relationship = "many-to-one"',
            'unmatched = c("error", "drop")',
            "col_types",
            "styler::style_file",
        ):
            self.assertIn(fragment, style)

    def test_left_join_unmatched_semantics_are_stated_correctly(self) -> None:
        style = read("skills/r-biostats/references/code-style.md")
        self.assertIn("`left_join()` 的 `unmatched = \"error\"` 检查的是查找表中未被使用的键", style)

    def test_code_examples_do_not_use_superseded_functions(self) -> None:
        code = r_code(read("skills/r-biostats/references/code-style.md"))
        for superseded in ("map_dfr(", "sapply(", "gather(", "spread(", "ifelse(", "%>%"):
            self.assertNotIn(superseded, code)


class PythonAndDesignTests(unittest.TestCase):
    def test_python_code_style_is_linked_and_guards_merges(self) -> None:
        self.assertIn("references/code-style.md", read("skills/python-biostats/SKILL.md"))
        style = read("skills/python-biostats/references/code-style.md")
        for fragment in ('validate="many_to_one"', "indicator=True", "observed=True", 'cov_type="HC0"', "dtype="):
            self.assertIn(fragment, style)

    def test_study_design_covers_target_trial_and_dag(self) -> None:
        self.assertIn("观察性研究的因果设计", read("skills/epi-study-design/SKILL.md"))
        spec = read("skills/epi-study-design/references/protocol-sap-specification.md")
        for fragment in ("目标试验", "永恒时间偏倚", "新用户设计", "DAG", "E 值"):
            self.assertIn(fragment, spec)


class FileSkillEntryTests(unittest.TestCase):
    def test_pptx_exposes_editing_and_rendering_tools(self) -> None:
        pptx = read("skills/pptx/SKILL.md")
        for fragment in ("editing.md", "render_slides.ps1", "add_slide.py", "clean.py"):
            self.assertIn(fragment, pptx)
        editing = read("skills/pptx/editing.md")
        self.assertNotIn("USE VARIED LAYOUTS", editing)
        self.assertNotIn("Use the Edit tool", editing)

    def test_xlsx_is_not_triggered_by_reading_analysis_csv(self) -> None:
        self.assertIn("统计分析中读入 CSV 数据不触发", read("skills/xlsx/SKILL.md"))

    def test_orphan_resources_have_workflow_entries(self) -> None:
        self.assertIn("thesis-formatting.md", read("skills/academic-publishing/SKILL.md"))
        self.assertIn("references/templates.md", read("skills/consulting-delivery/SKILL.md"))
        self.assertIn("archive_deliverables.py", read("skills/project-init/references/project-hygiene.md"))
        self.assertIn("scripts/fig_setup.R", read("skills/publication-figures/SKILL.md"))


class PlaceholderScanTests(unittest.TestCase):
    def test_scan_finds_current_and_legacy_markers(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            draft = Path(temporary) / "draft.md"
            draft.write_text(
                "伦理 [待补充：批号]\n引文[待补充引用]\n[待核验：方向]\n旧 [待确认] [ref] TODO\n"
                "IRB [NEED CONFIRMATION: number]\n正常引用 [1]\n",
                encoding="utf-8",
            )
            findings, errors = scan_placeholders.scan([draft])
        self.assertEqual(errors, [])
        kinds = [item["kind"] for item in findings]
        self.assertEqual(
            kinds,
            ["missing_info", "pending_citation", "unverified", "unverified", "legacy_ref", "todo", "need_confirmation"],
        )

    def test_scan_reads_docx_text(self) -> None:
        import zipfile

        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "paper.docx"
            body = (
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                "<w:body><w:p><w:r><w:t>基金 [待补充：基金号]</w:t></w:r></w:p></w:body></w:document>"
            )
            with zipfile.ZipFile(path, "w") as package:
                package.writestr("word/document.xml", body)
            findings, errors = scan_placeholders.scan([path])
        self.assertEqual(errors, [])
        self.assertEqual([item["marker"] for item in findings], ["[待补充：基金号]"])

    def test_placeholder_convention_has_single_definition(self) -> None:
        publishing = read("skills/academic-publishing/SKILL.md")
        self.assertIn("`[待补充：内容]`", publishing)
        self.assertIn("scripts/scan_placeholders.py", publishing)
        for relative in (
            "skills/academic-publishing/references/chinese-thesis.md",
            "skills/academic-publishing/references/statistical-reporting.md",
            "skills/academic-publishing/references/review-killers.md",
        ):
            body = read(relative)
            self.assertNotIn("[ref]", body, relative)
            self.assertNotIn("[待确认]", body, relative)


if __name__ == "__main__":
    unittest.main()
