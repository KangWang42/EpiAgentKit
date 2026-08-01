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

from config_core import (
    LOCAL_SKILL_EXCLUDES_FILE,
    SKILL_MANIFEST,
    SYNC_EXCLUDES,
    available_skills,
    local_skill_excludes,
)
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
        maintenance = (
            ROOT / "skills/epiagentkit-maintenance/SKILL.md"
        ).read_text(encoding="utf-8")
        creator = (ROOT / "skills/skill-creator/SKILL.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("regression-safe optimization", repo_rules)
        self.assertIn("观察到的缺口", maintenance)
        self.assertIn("必须保留的行为", maintenance)
        self.assertIn("最小变更集", maintenance)
        self.assertIn("代表性验证", maintenance)
        self.assertIn("sync --target all", maintenance)
        self.assertIn("doctor --target all", maintenance)
        self.assertIn("用户无需重复声明", maintenance)
        self.assertIn("Every request to add, revise, repair, rename or remove a skill", repo_rules)
        self.assertIn("Get-Content -Encoding utf8", repo_rules)
        self.assertIn("Treat mojibake as a failed read", repo_rules)
        self.assertIn("Optimize, Don't Accumulate", creator)
        self.assertIn("remove superseded text in the same edit", creator)
        for maintenance_detail in (
            "Skill 优化不是只增不减",
            "epiagentkit-maintenance",
            "sync --target all",
            "doctor --target all",
        ):
            self.assertNotIn(maintenance_detail, global_rules)

    def test_backup_workbench_is_the_isolated_experiment_contract(self) -> None:
        global_rules = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        repo_rules = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        hygiene = (
            ROOT / "skills/project-init/references/project-hygiene.md"
        ).read_text(encoding="utf-8")
        principles = (ROOT / "skills/biostat-principles/SKILL.md").read_text(
            encoding="utf-8"
        )
        initializer = (ROOT / "skills/project-init/scripts/init_project.R").read_text(
            encoding="utf-8"
        )
        publishing = (ROOT / "skills/academic-publishing/SKILL.md").read_text(
            encoding="utf-8"
        )
        assembly = (
            ROOT / "skills/academic-publishing/references/docx-assembly.md"
        ).read_text(encoding="utf-8")
        consulting = (ROOT / "skills/consulting-delivery/SKILL.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("09_backup/workbench/", global_rules)
        for body in (repo_rules, hygiene, principles, initializer, publishing, assembly, consulting):
            self.assertIn("09_backup/workbench/", body)
        for fragment in (
            "PLAN.md",
            "FINDINGS.md",
            "TEMP",
            "TMP",
            "TMPDIR",
            "晋级",
        ):
            self.assertIn(fragment, hygiene)
        self.assertIn('"09_backup/workbench"', initializer)
        self.assertNotIn("09_backup/<YYYY-MM-DD>_<主题>/", principles)
        self.assertNotIn("09_backup/<日期>_scripts_oneoff/", publishing + assembly)
        self.assertNotIn("系统创建的隔离临时目录", consulting)

    def test_global_rules_are_concise_complete_and_single_source(self) -> None:
        global_rules = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        lines = global_rules.splitlines()

        self.assertLessEqual(len(lines), 100)
        self.assertLessEqual(len(global_rules), 5600)
        self.assertLessEqual(max(map(len, lines)), 300)
        for daily_skill in (
            "project-init",
            "evidence-research",
            "biostat-principles",
            "r-biostats",
            "python-biostats",
            "publication-figures",
            "research-visuals",
            "academic-publishing",
            "academic-humanizer",
            "report-writing",
            "pptx",
            "consulting-delivery",
            "epi-project-audit",
            "docx",
            "xlsx",
            "pdf",
        ):
            self.assertIn(daily_skill, global_rules, daily_skill)

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

    def test_presentation_template_source_is_routed_before_creation(self) -> None:
        global_rules = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        pptx = (ROOT / "skills/pptx/SKILL.md").read_text(encoding="utf-8")
        sysu = (ROOT / "skills/sysu-ppt/SKILL.md").read_text(encoding="utf-8")
        cases = {
            case["id"]: case
            for case in json.loads(
                (ROOT / "scripts/skill_routing_cases.json").read_text(
                    encoding="utf-8"
                )
            )["cases"]
        }

        self.assertIn("先判模板来源", global_rules)
        self.assertIn("Template Routing Gate", pptx)
        self.assertIn("中大官方模板、其他学校/机构或特定汇报类型", pptx)
        self.assertIn("Load any matching presentation-content workflow or reference", pptx)
        self.assertIn("Use the template-editing workflow, not the from-scratch workflow", pptx)
        self.assertIn("不得把未说明学校的通用 PPT 自动套成中大模板", sysu)
        self.assertIn("绕过 `sysu_init()`", sysu)
        self.assertEqual(
            cases["generic_presentation_template_unspecified"]["primary"],
            "pptx",
        )
        self.assertEqual(
            cases["generic_presentation_template_unspecified"]["expected_action"],
            "clarify_template_source_before_creation",
        )
        self.assertIn(
            "sysu-ppt",
            cases["other_institution_presentation"]["excluded"],
        )
        self.assertEqual(
            cases["sysu_presentation_file"]["primary"],
            "sysu-ppt",
        )

    def test_papers_and_reports_use_content_driven_editorial_review(self) -> None:
        publishing = (
            ROOT / "skills/academic-publishing/SKILL.md"
        ).read_text(encoding="utf-8")
        playbook = (
            ROOT
            / "skills/academic-publishing/references/section-content-playbook.md"
        ).read_text(encoding="utf-8")
        chinese_paper = (
            ROOT / "skills/academic-publishing/references/chinese-paper.md"
        ).read_text(encoding="utf-8")
        chinese_thesis = (
            ROOT / "skills/academic-publishing/references/chinese-thesis.md"
        ).read_text(encoding="utf-8")
        english = (
            ROOT / "skills/academic-publishing/references/english-writing.md"
        ).read_text(encoding="utf-8")
        phrasebank = (
            ROOT / "skills/academic-publishing/references/english-phrasebank.md"
        ).read_text(encoding="utf-8")
        humanizer = (
            ROOT / "skills/academic-humanizer/SKILL.md"
        ).read_text(encoding="utf-8")
        editorial = (
            ROOT
            / "skills/academic-humanizer/references/patterns-and-preservation.md"
        ).read_text(encoding="utf-8")
        report = (ROOT / "skills/report-writing/SKILL.md").read_text(
            encoding="utf-8"
        )
        cases = {
            case["id"]: case
            for case in json.loads(
                (ROOT / "scripts/skill_routing_cases.json").read_text(
                    encoding="utf-8"
                )
            )["cases"]
        }

        for fragment in (
            "目的—方法—结果—表图—讨论主轴",
            "结构由研究问题、estimand、表图和目标期刊决定",
            "不以机械归零代替审校",
        ):
            self.assertIn(fragment, publishing)
        for fragment in (
            "本文件不提供固定段数",
            "不要以固定“总判断",
            "不得通过措辞隐藏",
            "不要求固定五块、七段",
        ):
            self.assertIn(fragment, playbook)
        self.assertIn("不要求恰好四段", chinese_paper)
        self.assertIn("不设置通用页数、字数、章节数", chinese_thesis)
        self.assertIn("do not require four paragraphs", english)
        self.assertIn("Do not begin from a stock sentence", phrasebank)
        self.assertIn("内容功能、论证结构、段落节奏", humanizer)
        self.assertIn("可迁移性测试", editorial)
        self.assertIn("文档层面结论先行", report)
        self.assertIn("不是每一节、每一段都必须套", report)
        self.assertIn(
            "academic-humanizer", cases["report_prose_only"]["companions"]
        )

        self.assertNotIn("CRGP 引言 / LOC-KD-COM", publishing)
        self.assertNotIn("每个显著因素一个小节", playbook)
        self.assertNotIn("每个章节、每个段落都先给", report)
        self.assertNotIn("每报一个数就跟一句", report)

    def test_manuscript_revision_routes_by_change_type_and_scope(self) -> None:
        cases = {
            case["id"]: case
            for case in json.loads(
                (ROOT / "scripts/skill_routing_cases.json").read_text(
                    encoding="utf-8"
                )
            )["cases"]
        }
        self.assertEqual(
            cases["existing_word_paragraph_revision"]["primary"],
            "academic-humanizer",
        )
        self.assertIn("docx", cases["existing_word_paragraph_revision"]["companions"])
        self.assertEqual(cases["existing_word_format_only_repair"]["primary"], "docx")
        self.assertEqual(
            cases["existing_manuscript_structural_rewrite"]["primary"],
            "academic-publishing",
        )
        self.assertEqual(
            cases["reviewer_response_closure"]["expected_action"],
            "close_each_comment_across_same_source_deliverables",
        )
        self.assertEqual(
            cases["ambiguous_current_manuscript"]["expected_action"],
            "stop_and_request_unique_input_selection",
        )

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

    def test_r_is_primary_and_python_requires_an_explicit_contract(self) -> None:
        cases = {
            case["id"]: case
            for case in json.loads(
                (ROOT / "scripts/skill_routing_cases.json").read_text(
                    encoding="utf-8"
                )
            )["cases"]
        }
        for case_id in (
            "existing_project_analysis",
            "analysis_with_plot",
            "r_dependency_missing_no_language_switch",
        ):
            self.assertEqual(cases[case_id]["primary"], "r-biostats")
            self.assertIn("python-biostats", cases[case_id]["excluded"])
        self.assertEqual(
            cases["existing_project_python_survival"]["primary"],
            "python-biostats",
        )
        self.assertIn(
            "r-biostats",
            cases["existing_project_python_survival"]["excluded"],
        )

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

    def test_static_local_only_skill_is_not_publicly_routed(self) -> None:
        global_rules = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        name = "python-ecg-analysis"
        self.assertIn(name, SYNC_EXCLUDES)
        self.assertTrue((ROOT / "skills" / name / "SKILL.md").is_file())
        self.assertNotIn(name, available_skills(ROOT))
        self.assertNotIn(name, source_skills(ROOT, set()))
        self.assertNotIn(name, global_rules)
        self.assertNotIn(name, readme)

    def test_machine_local_skill_file_hides_private_skills(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            for name in ("alpha", "private-skill"):
                skill = repo / "skills" / name
                skill.mkdir(parents=True)
                (skill / "SKILL.md").write_text(
                    f"---\nname: {name}\ndescription: test\n---\n",
                    encoding="utf-8",
                )
            (repo / LOCAL_SKILL_EXCLUDES_FILE).write_text(
                "# machine-local only\nprivate-skill\n",
                encoding="utf-8",
            )

            self.assertEqual(local_skill_excludes(repo), {"private-skill"})
            self.assertEqual(available_skills(repo), ["alpha"])
            self.assertEqual(set(source_skills(repo, set())), {"alpha"})

    def test_local_only_skills_cannot_be_explicitly_synchronized(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            private = repo / "skills" / "private-skill"
            private.mkdir(parents=True)
            (private / "SKILL.md").write_text(
                "---\nname: private-skill\ndescription: test\n---\n",
                encoding="utf-8",
            )
            (repo / LOCAL_SKILL_EXCLUDES_FILE).write_text(
                "private-skill\n", encoding="utf-8"
            )

            with self.assertRaisesRegex(ValueError, "Local-only skills"):
                sync_skills(
                    repo,
                    Path(directory) / "target",
                    set(),
                    dry_run=False,
                    include={"private-skill"},
                )

    def test_full_sync_prunes_previously_managed_local_only_skills(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            repo = base / "repo"
            target = base / "target"
            for name in ("alpha", "private-skill"):
                skill = repo / "skills" / name
                skill.mkdir(parents=True)
                (skill / "SKILL.md").write_text(
                    f"---\nname: {name}\ndescription: test\n---\n",
                    encoding="utf-8",
                )
            (repo / LOCAL_SKILL_EXCLUDES_FILE).write_text(
                "private-skill\n", encoding="utf-8"
            )
            stale = target / "private-skill"
            stale.mkdir(parents=True)
            (stale / "SKILL.md").write_text("stale\n", encoding="utf-8")
            (target / SKILL_MANIFEST).write_text(
                '{"managed": ["private-skill"]}\n',
                encoding="utf-8",
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
