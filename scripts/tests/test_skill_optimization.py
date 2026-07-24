from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SkillOptimizationTests(unittest.TestCase):
    def test_cross_skill_contract_audit_passes(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/audit_skill_contracts.py"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertRegex(result.stdout, r"\d+ public skills")
        self.assertIn("no dependency cycles", result.stdout)

    def test_skill_validator_checks_directory_links_and_placeholders(self) -> None:
        validator = ROOT / "skills/skill-creator/scripts/quick_validate.py"
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            mismatch = base / "actual-name"
            mismatch.mkdir()
            (mismatch / "SKILL.md").write_text(
                "---\nname: other-name\ndescription: test\n---\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(validator), str(mismatch)],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("must match skill directory", result.stdout)

            broken = base / "broken-link"
            broken.mkdir()
            (broken / "SKILL.md").write_text(
                "---\nname: broken-link\ndescription: test\n---\n"
                "Read [missing](references/missing.md).\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(validator), str(broken)],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Missing local Markdown target", result.stdout)

            placeholder = base / "placeholder"
            (placeholder / "scripts").mkdir(parents=True)
            (placeholder / "SKILL.md").write_text(
                "---\nname: placeholder\ndescription: test\n---\n",
                encoding="utf-8",
            )
            (placeholder / "scripts/example.py").write_text(
                "# placeholder\n", encoding="utf-8"
            )
            result = subprocess.run(
                [sys.executable, str(validator), str(placeholder)],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Initializer placeholder", result.stdout)

    def test_python_result_helper_matches_shared_contract(self) -> None:
        helper = load_module(
            "python_emit_summary",
            ROOT / "skills/python-biostats/scripts/emit_summary.py",
        )
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            yaml_path = base / "results.yaml"
            md_path = base / "summary.md"
            rendered = helper.add_result(
                yaml_path,
                "exposure_hr",
                label="暴露与结局的关联",
                est=1.45,
                ci_low=1.12,
                ci_high=1.87,
                p=0.004,
                source="02_code/03_main.py",
                interp="暴露与较高风险相关。",
            )
            self.assertEqual(rendered, "1.45（95%CI：1.12，1.87），P = 0.004")
            self.assertEqual(helper.val(yaml_path, "exposure_hr"), rendered)
            helper.render_summary_md(yaml_path, md_path)
            self.assertIn("暴露与结局的关联", md_path.read_text(encoding="utf-8"))

            helper.add_result(
                yaml_path,
                "exposure_hr",
                label="暴露与结局的关联",
                est=1.20,
                ci_low=1.01,
                ci_high=1.42,
                p=0.03,
                source="02_code/03_main.py",
            )
            self.assertEqual(helper.stale_interps(yaml_path), ["exposure_hr"])
            helper.confirm_interp(yaml_path, "exposure_hr", "更新后的解释。")
            self.assertEqual(helper.stale_interps(yaml_path), [])

    def test_project_initializer_supports_r_and_python_without_default_git(self) -> None:
        script = ROOT / "skills/project-init/scripts/init_project.R"
        body = script.read_text(encoding="utf-8")
        self.assertIn('language = c("r", "python")', body)
        self.assertIn("git = FALSE", body)
        self.assertIn('find_skill_file("python-biostats", "scripts/emit_summary.py")', body)
        self.assertIn('language = if (language == "r") "R" else "python"', body)

        rscript = shutil.which("Rscript")
        if rscript is None:
            self.skipTest("Rscript is unavailable; static initializer contract passed")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).as_posix()
            source = script.as_posix()
            test_script = Path(directory) / "test_init_project.R"
            test_script.write_text(
                "\n".join(
                    [
                        f'source("{source}", encoding="UTF-8")',
                        f'init_project("r_demo", root="{root}", language="r", git=FALSE)',
                        f'init_project("py_demo", root="{root}", language="python", git=FALSE)',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            environment = dict(os.environ)
            environment["EPIAGENTKIT_SKILLS"] = str(ROOT / "skills")
            result = subprocess.run(
                [rscript, str(test_script)],
                cwd=ROOT,
                env=environment,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            r_project = Path(directory) / "r_demo"
            py_project = Path(directory) / "py_demo"
            self.assertTrue((r_project / "02_code/config.R").is_file())
            self.assertTrue((r_project / "02_code/vendored/emit_summary.R").is_file())
            self.assertTrue((r_project / "r_demo.Rproj").is_file())
            self.assertTrue((py_project / "02_code/config.py").is_file())
            self.assertTrue((py_project / "02_code/vendored/emit_summary.py").is_file())
            self.assertTrue((py_project / "02_code/01_data_cleaning.py").is_file())
            self.assertFalse((py_project / "py_demo.Rproj").exists())
            self.assertFalse((r_project / ".git").exists())
            self.assertFalse((py_project / ".git").exists())

    def test_global_writing_contract_and_r_first_default_are_preserved(self) -> None:
        rules = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        for fragment in (
            "研究者“我做了 X”的视角",
            "不使用助手口吻",
            "游戏化隐喻",
            "英文缩写首次出现给出全称",
            "未指定且无既有语言合同时默认 R",
            "不要求把可工作的 R 主流程迁移到 Python",
            "回复与交付说明简洁，不堆套话",
            "使用临床研究、流行病学与生物统计的准确术语",
            "调用条件、检查要求、停止条件和隔离执行",
            "平台术语没有稳定中文译名时保留原词并说明功能",
            "不作字面翻译",
        ):
            self.assertIn(fragment, rules)
        for inappropriate_term in ("\u95e8\u7981", "\u6273\u673a"):
            self.assertNotIn(inappropriate_term, rules)
        project_init = (ROOT / "skills/project-init/SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("分析语言：R（默认）或 Python", project_init)

    def test_shared_result_schema_keeps_interpretation_recovery_workflow(self) -> None:
        schema = (
            ROOT / "skills/biostat-principles/references/result-summary-schema.md"
        ).read_text(encoding="utf-8")
        for fragment in (
            "stale_interps(path)",
            "confirm_interp(path, key, interp=...)",
            "set_conclusion(path, text)",
            'style="zh"|"en"',
            'which="est|ci|p|est_ci|full"',
            "不得仅为清除标记而调用 `confirm_interp()`",
        ):
            self.assertIn(fragment, schema)

    def test_language_neutral_workflows_remain_coordinated(self) -> None:
        principles = (ROOT / "skills/biostat-principles/SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("R 用 `Rscript 02_code/NN_xxx.R`", principles)
        self.assertIn("Python 用项目已有兼容解释器", principles)

        publishing = (ROOT / "skills/academic-publishing/SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("`r-biostats` 或 `python-biostats`", publishing)
        self.assertNotIn("（r-biostats 产出）", publishing)

        evidence = (ROOT / "skills/evidence-research/SKILL.md").read_text(
            encoding="utf-8"
        )
        delivery = (ROOT / "skills/consulting-delivery/SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("项目 Python skill", evidence + delivery)

    def test_moved_contract_references_are_current(self) -> None:
        migration = (ROOT / "docs/global-rule-migration.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("biostat-principles/references/result-summary-schema.md", migration)
        self.assertNotIn("r-biostats/references/result-summary-schema.md", migration)

        publishing = (ROOT / "skills/academic-publishing/SKILL.md").read_text(
            encoding="utf-8"
        )
        review = (
            ROOT / "skills/academic-publishing/references/review-killers.md"
        ).read_text(encoding="utf-8")
        project_init = (ROOT / "skills/project-init/SKILL.md").read_text(
            encoding="utf-8"
        )
        figures = (ROOT / "skills/publication-figures/SKILL.md").read_text(
            encoding="utf-8"
        )
        report = (ROOT / "skills/report-writing/SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("`CLAUDE.md` §4", publishing + review)
        self.assertIn("`CLAUDE.md` §4 与 §7", project_init)
        self.assertIn("`CLAUDE.md` §6 的术语合同", figures)
        self.assertIn("`CLAUDE.md` §1 与 §8", report)

    def test_multi_outcome_figures_use_set_level_coverage(self) -> None:
        body = (ROOT / "skills/publication-figures/SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("整组表图覆盖完整结局集合", body)
        self.assertNotIn("多结局图含全部结局", body)

    def test_delivery_preserves_true_provenance(self) -> None:
        body = (ROOT / "skills/consulting-delivery/SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("不篡改真实溯源", body)
        self.assertIn("工具使用", body)
        self.assertIn("披露", body)
        self.assertNotIn("`AI_assisted` → `研究者`", body)

    def test_audit_uses_design_specific_scientific_judgment(self) -> None:
        body = (ROOT / "skills/epi-project-audit/SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("不把单一经验阈值作为普遍红线", body)
        self.assertIn("方向不一致是需要评估的证据，不自动判定失败", body)
        self.assertNotIn("事件数 ≥ 10×协变量数", body)
        self.assertNotIn("Reviewer: Agent", body)

    def test_file_skills_do_not_force_unrequested_artifacts_or_edits(self) -> None:
        report = (ROOT / "skills/report-writing/SKILL.md").read_text(encoding="utf-8")
        pptx = (ROOT / "skills/pptx/SKILL.md").read_text(encoding="utf-8")
        xlsx = (ROOT / "skills/xlsx/SKILL.md").read_text(encoding="utf-8")
        docx = (ROOT / "skills/docx/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("明确要求双格式时才同时生成", report)
        self.assertIn("without making a gratuitous edit", pptx)
        self.assertIn("Verified statistical result or archival export", xlsx)
        self.assertIn("neutral value `Reviewer`", docx)
        self.assertNotIn('Use "Claude" as the author', docx)


if __name__ == "__main__":
    unittest.main()
