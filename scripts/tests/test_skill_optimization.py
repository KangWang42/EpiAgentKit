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
