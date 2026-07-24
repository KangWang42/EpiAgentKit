from __future__ import annotations

import json
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
    def test_workflow_audit_forces_utf8_diagnostics(self) -> None:
        audit = (ROOT / "scripts" / "audit_workflow_contracts.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("def configure_utf8_output()", audit)
        self.assertIn('reconfigure(encoding="utf-8", errors="replace")', audit)
        self.assertIn('os.environ["PYTHONIOENCODING"] = "utf-8"', audit)
        self.assertIn("configure_utf8_output()\n    raise SystemExit(main())", audit)

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

    def test_global_rules_are_concise_complete_and_single_source(self) -> None:
        global_rules = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        lines = global_rules.splitlines()

        self.assertLessEqual(len(lines), 200)
        self.assertLessEqual(max(map(len, lines)), 300)
        for skill in available_skills(ROOT):
            self.assertIn(skill, global_rules, skill)

        for quality_rule in (
            "功能与读者匹配",
            "事实和数字准确",
            "层级清楚",
            "结构紧凑",
            "术语一致",
            "版式克制",
            "最终尺寸可读",
            "未指定风格时采用对应 skill 的中性默认",
        ):
            self.assertIn(quality_rule, global_rules)

        for conditional_detail in (
            "HTTP 524",
            "referenced_image_paths",
            "num_last_images_to_include",
            "Image 1 为验收基线",
        ):
            self.assertNotIn(conditional_detail, global_rules)

    def test_epiagentkit_maintenance_contract_is_dedicated_and_portable(self) -> None:
        maintenance = (
            ROOT / "skills" / "epiagentkit-maintenance" / "SKILL.md"
        ).read_text(encoding="utf-8")
        routing = (ROOT / "scripts" / "skill_routing_cases.json").read_text(
            encoding="utf-8"
        )

        for fragment in (
            "name: epiagentkit-maintenance",
            "CLAUDE.md",
            "AGENTS.md",
            "skills",
            "hooks",
            "观察到的缺口",
            "必须保留的行为",
            "最小变更集",
            "代表性验证",
            "每个概念保持一个单源",
            "不执行 `git init`",
            "不安装 Git",
            "sync --target all",
            "doctor --target all",
            "普通研究项目的数据分析、写作或项目初始化不触发本 skill",
        ):
            self.assertIn(fragment, maintenance)
        self.assertIn("maintain_epiagentkit_contracts", routing)
        cases = {case["id"]: case for case in json.loads(routing)["cases"]}
        self.assertIn("epiagentkit-maintenance", cases["new_empty_project"]["excluded"])
        self.assertIn(
            "epiagentkit-maintenance",
            cases["existing_project_analysis"]["excluded"],
        )

    def test_neutral_document_defaults_live_in_file_skills(self) -> None:
        docx = (ROOT / "skills" / "docx" / "SKILL.md").read_text(encoding="utf-8")
        xlsx = (ROOT / "skills" / "xlsx" / "SKILL.md").read_text(encoding="utf-8")
        report = (ROOT / "skills" / "report-writing" / "SKILL.md").read_text(
            encoding="utf-8"
        )

        for fragment in (
            "Neutral Default Formatting",
            "Keep every table cell white by default",
            "preserve its existing styles and layout",
        ):
            self.assertIn(fragment, docx)
        for fragment in (
            "Neutral Default Formatting",
            "Do not automatically add dark header bands",
        ):
            self.assertIn(fragment, xlsx)
        for fragment in ("默认中性排版", "无填充、白底黑字"):
            self.assertIn(fragment, report)

    def test_analysis_agent_reports_anomalies_as_monitor(self) -> None:
        global_rules = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        principles = (ROOT / "skills" / "biostat-principles" / "SKILL.md").read_text(
            encoding="utf-8"
        )

        for fragment in (
            "同时承担执行与监测职责",
            "主动向用户报告",
            "现象、证据位置、影响范围、已采取动作及待决定事项",
            "停在安全点等待确认",
            "不静默修补后继续",
        ):
            self.assertIn(fragment, global_rules)
        for fragment in (
            "执行者也是监测者",
            "发生了什么、证据在哪里、影响什么、已经做了什么、还需要决定什么",
            "停在安全点等待确认",
        ):
            self.assertIn(fragment, principles)

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
        self.assertIn("其它非统计视觉默认调用 `research-visuals`", body)
        self.assertIn("先锁定图前合同", body)
        self.assertIn("多面板已完成两两去冗余", body)
        self.assertIn("07_paper/results.yaml", body)
        self.assertNotIn("用户要求出图、画图、做图、生成 Fig", body)

    def test_publication_figures_preserves_visual_grammar_and_redesigns_when_requested(
        self,
    ) -> None:
        body = (ROOT / "skills" / "publication-figures" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("只更新数值、术语、标签、精度或注释时", body)
        self.assertIn("除非存在明确不合规问题", body)
        self.assertIn("保持原图的视觉语法", body)
        self.assertIn("明确对图形样式不满", body)
        self.assertIn("主动重新设计", body)
        self.assertIn("同一项目", body)
        self.assertIn("PubMed", body)
        self.assertIn("不把纯白背景当作投稿要求", body)
        self.assertNotIn("无 3D / 默认灰底 / 彩虹色 / 单独 JPEG", body)

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
