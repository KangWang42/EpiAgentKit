from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from config_core import SKILL_MANIFEST, SYNC_EXCLUDES, available_skills
from sync_user_configs import source_skills, sync_skills


class WorkflowRoutingTests(unittest.TestCase):
    def test_skill_maintenance_contract_is_regression_safe(self) -> None:
        global_rules = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        repo_rules = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        creator = (ROOT / "skills/skill-creator/SKILL.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("Skill 优化不是只增不减", global_rules)
        self.assertIn("同时验证触发边界、旧能力、新场景", global_rules)
        self.assertIn("regression-safe optimization", repo_rules)
        self.assertIn("Optimize, Don't Accumulate", creator)
        self.assertIn("remove superseded text in the same edit", creator)

    def test_skill_validator_enforces_metadata_and_context_budget(self) -> None:
        validator = ROOT / "skills/skill-creator/scripts/quick_validate.py"
        cases = {
            "empty-description": (
                "---\nname: empty-description\ndescription: ''\n---\n",
                False,
            ),
            "large-body": (
                (
                    "---\nname: large-body\ndescription: test skill\n---\n"
                    + "instruction\n" * 500
                ),
                False,
            ),
            "claude-only-valid": (
                "---\nname: claude-only-valid\ndescription: test skill\n"
                "disable-model-invocation: true\n---\n",
                True,
            ),
        }

        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            for name, (content, should_pass) in cases.items():
                with self.subTest(name=name):
                    skill = base / name
                    skill.mkdir()
                    (skill / "SKILL.md").write_text(content, encoding="utf-8")
                    result = subprocess.run(
                        [sys.executable, str(validator), str(skill)],
                        cwd=ROOT,
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                    )
                    self.assertEqual(result.returncode == 0, should_pass)

    def test_python_ecg_is_local_only_and_not_publicly_routed(self) -> None:
        global_rules = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("python-ecg-analysis", SYNC_EXCLUDES)
        self.assertNotIn("python-ecg-analysis", available_skills(ROOT))
        self.assertNotIn("python-ecg-analysis", source_skills(ROOT, set()))
        self.assertNotIn("python-ecg-analysis", global_rules)
        self.assertNotIn("python-ecg-analysis", readme)

    def test_python_ecg_cannot_be_explicitly_synchronized(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "Local-only skills"):
                sync_skills(
                    ROOT,
                    Path(directory) / "skills",
                    set(),
                    dry_run=False,
                    include={"python-ecg-analysis"},
                )

    def test_full_sync_prunes_previously_managed_python_ecg(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            repo = base / "repo"
            target = base / "target"
            for name in ("alpha", "python-ecg-analysis"):
                skill = repo / "skills" / name
                skill.mkdir(parents=True)
                (skill / "SKILL.md").write_text(
                    f"---\nname: {name}\ndescription: test\n---\n",
                    encoding="utf-8",
                )
            stale = target / "python-ecg-analysis"
            stale.mkdir(parents=True)
            (stale / "SKILL.md").write_text("stale\n", encoding="utf-8")
            (target / SKILL_MANIFEST).write_text(
                '{"managed": ["python-ecg-analysis"]}\n', encoding="utf-8"
            )

            sync_skills(repo, target, set(), dry_run=False)

            self.assertFalse(stale.exists())
            self.assertTrue((target / "alpha" / "SKILL.md").is_file())

    def test_readme_keeps_statistical_and_writing_boundaries_narrow(self) -> None:
        body = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("制作发表级统计图", body)
        self.assertIn("写论文与投稿材料", body)
        self.assertIn("全项目质量审查", body)
        self.assertIn("项目能做到什么", body)
        self.assertNotIn("一次性生成全文", body)
        self.assertNotIn('审查只看代码即可通过', body)

    def test_publication_figures_trigger_is_statistical(self) -> None:
        body = (ROOT / "skills" / "publication-figures" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("发表级统计图、数据图", body)
        self.assertIn("非统计视觉不触发本技能", body)
        self.assertIn("先锁定图前合同", body)
        self.assertIn("多面板已完成两两去冗余", body)
        self.assertIn("07_paper/results.yaml", body)
        self.assertNotIn("用户要求出图、画图、做图、生成 Fig", body)

    def test_results_machine_source_is_not_the_derived_markdown(self) -> None:
        body = (
            ROOT
            / "skills"
            / "academic-publishing"
            / "references"
            / "chinese-thesis.md"
        ).read_text(encoding="utf-8")
        self.assertIn("数字机器单源 = `07_paper/results.yaml`", body)
        self.assertNotIn("结果变 → 回写 `0_result_summaries.md`", body)

    def test_audit_continues_all_layers_but_blocks_signoff(self) -> None:
        body = (ROOT / "skills" / "epi-project-audit" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("继续完成其余层审查", body)
        self.assertIn("任何未闭环的 fail 都阻止签发", body)
        self.assertIn("仅在“审查并修复”模式", body)
        self.assertNotIn("不通过不进入下一层", body)
        self.assertNotIn("### 自动修复动作", body)

        checklist = (
            ROOT
            / "skills"
            / "epi-project-audit"
            / "references"
            / "audit-checklist.md"
        ).read_text(encoding="utf-8")
        self.assertIn("`results.yaml` ↔ 派生 `0_result_summaries.md`", checklist)


if __name__ == "__main__":
    unittest.main()
