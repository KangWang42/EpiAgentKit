from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from config_core import (
    LOCAL_RULES_PRESERVE_FILE,
    LOCAL_SKILL_EXCLUDES_FILE,
    SKILL_MANIFEST,
    SYNC_EXCLUDES,
    available_skills,
    expand_dependencies,
    local_skill_excludes,
    preserve_global_rules,
    public_skills,
)
from sync_user_configs import source_skills, sync_skills
from audit_workflow_contracts import (
    RESEARCH_TERMINOLOGY,
    audit_research_terminology,
    research_term_violations,
)


class WorkflowRoutingTests(unittest.TestCase):
    def test_research_terminology_audit_is_context_aware(self) -> None:
        self.assertEqual(
            research_term_violations(
                "skills/consulting-delivery/SKILL.md",
                "必须保留法规、期刊、合同要求披露的事实；合同允许时方可排除。",
            ),
            (),
        )
        flagged = " ".join(RESEARCH_TERMINOLOGY[index] for index in (0, 6, 7))
        self.assertEqual(
            research_term_violations("skills/example/SKILL.md", flagged),
            tuple(RESEARCH_TERMINOLOGY[index] for index in (0, 6, 7)),
        )
        self.assertEqual(
            research_term_violations(
                "AGENTS.md", "Run scripts/audit_workflow_contracts.py."
            ),
            (),
        )
        self.assertEqual(audit_research_terminology(), [])
        self.assertEqual(
            research_term_violations(
                "skills/research-visuals/references/carrier-specs.md",
                "检查网页加载体积和清晰度",
            ),
            (),
        )
        self.assertEqual(
            research_term_violations("skills/example/SKILL.md", "调用载体 skill"),
            ("载体",),
        )
        rules = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        maintenance = (ROOT / "skills/epiagentkit-maintenance/SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("中文终审不能只查词", rules)
        self.assertIn("谁依据什么，在什么条件下做什么", rules)
        self.assertIn("词面扫描只用于发现高确定性线索", maintenance)

    def test_workflow_audit_forces_utf8_diagnostics(self) -> None:
        audit = (ROOT / "scripts" / "audit_workflow_contracts.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("def configure_utf8_output()", audit)
        self.assertIn('reconfigure(encoding="utf-8", errors="replace")', audit)
        self.assertIn('os.environ["PYTHONIOENCODING"] = "utf-8"', audit)
        self.assertIn("for name in public_skills(ROOT):", audit)
        self.assertNotIn("local_skill_excludes(ROOT)", audit)
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
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("regression-safe optimization", repo_rules)
        self.assertIn("观察到的缺口", maintenance)
        self.assertIn("必须保留的行为", maintenance)
        self.assertIn("最小变更集", maintenance)
        self.assertIn("代表性验证", maintenance)
        self.assertIn("对照用户要求、实际产物和当时适用的规则", maintenance)
        self.assertIn("判断最早出现问题的规则或步骤", maintenance)
        self.assertIn("修改最早且可复用的规则或步骤", maintenance)
        self.assertIn("完成状态不再夸大", maintenance)
        self.assertIn("sync --target all", repo_rules)
        self.assertIn("doctor --target all", repo_rules)
        self.assertIn("其余提交、push、提交后同步和 doctor", maintenance)
        self.assertIn("用户无需重复声明", maintenance)
        self.assertIn("新建 Skill 与按需成果审阅", maintenance)
        self.assertIn("至少两份可独立打开、分别验收的真实成果", maintenance)
        self.assertIn("既有 skill 时，默认使用代表性实跑和回归测试验收", maintenance)
        self.assertIn("只有用户当轮明确要求时才生成", maintenance)
        self.assertIn("验证日志、validator 成功和测试通过只能作为证据", maintenance)
        self.assertIn("只有用户明确确认当前成果无误并同意提交", maintenance)
        self.assertIn("成果审阅只属于新建 skill 或用户明确要求的维护任务", maintenance)
        self.assertIn("不得只写进当轮说明、临时提示词或审阅文档", maintenance)
        self.assertIn("可作为其它 skill 的候选方法", maintenance)
        self.assertIn("只迁移确有帮助的原则", maintenance)
        self.assertIn("不机械复制五段标题、字段、字数、禁止项或完整模板", maintenance)
        self.assertIn("pre-commit review gate", repo_rules)
        self.assertIn("新建 skill 在提交前应附至少两份", readme)
        self.assertIn("修改既有 skill 默认以代表性实跑和回归测试验收", readme)
        self.assertIn("明确确认当前成果前不要 commit、sync 或 doctor", readme)
        self.assertIn("Every request to add, revise, repair, rename or remove a skill", repo_rules)
        self.assertIn("regression-safe optimization workflow", repo_rules)
        self.assertIn("Get-Content -Encoding utf8", repo_rules)
        self.assertIn("Treat mojibake as a failed read", repo_rules)
        self.assertIn("Treat `powershell.exe` as Windows PowerShell 5.1", repo_rules)
        self.assertIn("Use `-LiteralPath` only for cmdlets that support it", repo_rules)
        self.assertIn("Windows 维护遵循全局与根 `AGENTS.md`", maintenance)
        self.assertIn("`powershell.exe` 按 Windows PowerShell 5.1 对待", global_rules)
        self.assertIn("Optimize, Don't Accumulate", creator)
        self.assertIn("remove superseded text in the same edit", creator)
        for maintenance_detail in (
            "Skill 优化不是只增不减",
            "epiagentkit-maintenance",
            "sync --target all",
            "doctor --target all",
        ):
            self.assertNotIn(maintenance_detail, global_rules)

    def test_backup_archive_and_workbench_have_separate_roles(self) -> None:
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
        consulting = (ROOT / "skills/consulting-delivery/SKILL.md").read_text(
            encoding="utf-8"
        )
        archive_script = (
            ROOT / "skills/project-init/scripts/archive_deliverables.py"
        ).read_text(encoding="utf-8")

        for body in (global_rules, repo_rules, hygiene):
            self.assertIn("09_backup/archive/", body)
        for body in (global_rules, repo_rules, hygiene, principles):
            self.assertIn("09_backup/workbench/", body)
        self.assertIn("在 `09_backup/workbench/` 中建立独立的交付测试副本", consulting)
        for fragment in (
            "PLAN.md",
            "FINDINGS.md",
            "TEMP",
            "TMP",
            "TMPDIR",
        ):
            self.assertIn(fragment, hygiene)
        self.assertIn("只索引 `archive/`", hygiene)
        self.assertIn("只引用 `workbench/` 批次", hygiene)
        self.assertIn("根级批次", hygiene)
        self.assertIn("项目 `.gitignore` 忽略整个 `09_backup/`", global_rules)
        self.assertIn("entire `09_backup/` tree is local-only", repo_rules)
        self.assertIn("整个 `09_backup/` 只在本地", hygiene)
        self.assertIn('backup / "archive"', archive_script)
        self.assertIn("do not rewrite a legacy project implicitly", archive_script)
        self.assertIn('"09_backup/archive", "09_backup/workbench"', initializer)
        self.assertIn('"09_backup/workbench"', initializer)
        self.assertIn('"/09_backup/"', initializer)
        self.assertNotIn("09_backup/<YYYY-MM-DD>_<主题>/", principles)
        self.assertNotIn("系统创建的隔离临时目录", consulting)

    def test_global_rules_are_concise_complete_and_single_source(self) -> None:
        global_rules = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        lines = global_rules.splitlines()

        self.assertLessEqual(len(lines), 200)
        self.assertLessEqual(len(global_rules), 12000)
        self.assertLessEqual(max(map(len, lines)), 700)
        for daily_skill in (
            "project-init",
            "evidence-research",
            "biostat-principles",
            "r-biostats",
            "python-biostats",
            "publication-figures",
            "research-visuals",
            "build-web-ui",
            "academic-publishing",
            "manuscript-peer-review",
            "academic-humanizer",
            "report-writing",
            "pptx",
            "consulting-delivery",
            "epi-project-audit",
            "workflow-retrospective",
            "docx",
            "xlsx",
            "pdf",
        ):
            self.assertIn(daily_skill, global_rules, daily_skill)
        for fragment in (
            "把请求拆成实际工作项",
            "一旦某项工作适用某个 skill",
            "规范在制作过程中执行",
            "只有通过本项内容规范和文件检查的工作项才能标为完成",
            "项目 `README.md` 只说明运行方法、输入输出位置和阅读顺序",
            "项目整体阶段与各项工作完成状态只在项目 `CLAUDE.md` 更新",
        ):
            self.assertIn(fragment, global_rules)

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
            "待修改原图为内容核对依据",
        ):
            self.assertNotIn(conditional_detail, global_rules)

    def test_code_and_table_standards_apply_during_creation(self) -> None:
        r_skill = (ROOT / "skills/r-biostats/SKILL.md").read_text(
            encoding="utf-8"
        )
        code_style = (
            ROOT / "skills/r-biostats/references/code-style.md"
        ).read_text(encoding="utf-8")
        package_selection = (
            ROOT / "skills/r-biostats/references/package-selection.md"
        ).read_text(encoding="utf-8")
        descriptive = (
            ROOT / "skills/r-biostats/references/descriptive.md"
        ).read_text(encoding="utf-8")
        regression = (
            ROOT / "skills/r-biostats/references/regression.md"
        ).read_text(encoding="utf-8")
        xlsx = (ROOT / "skills/xlsx/SKILL.md").read_text(encoding="utf-8")
        academic = (ROOT / "skills/academic-publishing/SKILL.md").read_text(
            encoding="utf-8"
        )
        project_init = (ROOT / "skills/project-init/SKILL.md").read_text(
            encoding="utf-8"
        )
        project_hygiene = (
            ROOT / "skills/project-init/references/project-hygiene.md"
        ).read_text(encoding="utf-8")
        pipeline_r = (ROOT / "skills/project-init/assets/run_pipeline.R").read_text(
            encoding="utf-8"
        )
        pipeline_py = (
            ROOT / "skills/project-init/assets/run_pipeline.py"
        ).read_text(encoding="utf-8")

        self.assertIn("必须先读 [代码风格]", r_skill)
        self.assertIn("必须先读 [包选择与复用]", r_skill)
        self.assertIn("在编写过程中按其组织主线", r_skill)
        self.assertIn("多个产物共享变量但口径不同时", r_skill)
        self.assertIn("不为已有明确口径另建清单文件", r_skill)
        self.assertIn("文件与参数预检集中在总运行入口", r_skill)
        self.assertIn("研究对象式命名", r_skill)
        self.assertIn("同一稳定工具在多个主脚本重复出现时", code_style)
        self.assertIn(
            "按 `<对象>_<主题>_<时间>_<阶段>` 组合真正有区分作用的部分",
            code_style,
        )
        self.assertIn("不要在每个脚本重复建立 `required_inputs`", code_style)
        self.assertIn(
            "数据列的逐记录判断使用 `if_else()` 或 `case_when()`",
            code_style,
        )
        self.assertIn(
            "稳定科学不变量被破坏而无法产生有效结果",
            code_style,
        )
        self.assertIn(
            "不要仅为证明一致而同时读取同一结果的两套重复来源",
            code_style,
        )
        self.assertIn("`run_pipeline.R`、命令行入口或确定性构建器", code_style)
        self.assertIn("一个成品可以按需要读取不同结果对象", code_style)
        self.assertIn("孤立的 `[1] 0`", code_style)
        self.assertIn("不把整篇论文或长篇报告写成数百行", code_style)
        self.assertIn("不得仅因脚本成功执行而把代码工作项标为完成", code_style)
        self.assertIn("默认只设置一个说明列", descriptive)
        self.assertIn("不增加独立“分层”“水平”列", descriptive)
        self.assertIn("单元格的真实缩进属性", descriptive)
        self.assertIn("暴露组（N=...）", descriptive)
        self.assertIn("Apply the content structure while building", xlsx)
        self.assertIn("Use the cell alignment's real indent setting", xlsx)
        self.assertIn("start the worksheet at row 1 with column headers", xlsx)
        self.assertIn("Do not add white borders", xlsx)
        self.assertIn("tidyverse 是正式研究代码的整体默认表达方式", code_style)
        self.assertIn("不要用长篇自定义函数重复", code_style)
        self.assertIn("先查成熟包，再写最小适配", package_selection)
        self.assertIn("tidyverse 官方博客", package_selection)
        self.assertIn("`bruceR`", package_selection)
        self.assertIn("`compareGroups`", package_selection)
        self.assertIn("不得调用或复制未导出的内部函数", package_selection)
        self.assertIn("兼容场景的首选", descriptive)
        self.assertIn("`compareGroups()` → `createTable()`", descriptive)
        self.assertIn("不得从模型使用多重插补推断 Table 1", descriptive)
        self.assertIn("显式设置 `var.equal`", descriptive)
        self.assertIn("`export2xls()`", descriptive)
        self.assertIn("`export2word()`", descriptive)
        self.assertIn("`forcats::fct_na_value_to_level()`", descriptive)
        self.assertIn("`nmax = TRUE`", descriptive)
        self.assertIn("`gtsummary::tbl_svysummary()`", descriptive)
        self.assertIn("只有两种文件都通过", descriptive)
        self.assertIn("第一条可运行方案", package_selection)
        self.assertIn("`mice()` → `with()` → `pool()`", regression)
        self.assertIn("不预先增加辅助包、自定义预测矩阵", regression)
        self.assertIn("不因出现记录事件就自动改预测矩阵", regression)
        self.assertIn("不使用脱离情境的 VIF 固定阈值", regression)
        self.assertNotIn("vif(model)  # < 5", regression)
        self.assertNotIn("library(pROC)", regression)
        self.assertIn("`02_code/` 只保存正式数据处理", code_style)
        self.assertIn("与正文来源放在 `paper/`", academic)
        self.assertIn("不进入 `run_pipeline.R|py`", academic)
        self.assertIn("仅在用户明确要求提纲", academic)
        self.assertIn("即进入本模式，不另等用户补充“完整”二字", academic)
        self.assertIn("不得擅自降级为提纲、短版骨架", academic)
        self.assertIn("先按实际职责决定位置", project_init)
        self.assertIn("一个 `02_code/00_setup.R|py`", project_init)
        self.assertIn("总运行脚本使用明确的脚本清单", project_init)
        self.assertIn("目录由文件对研究结果的实际作用决定", project_hygiene)
        self.assertIn("本次产物验收", project_hygiene)
        self.assertIn('scripts <- c(', pipeline_r)
        self.assertNotIn("list.files(\"02_code\"", pipeline_r)
        self.assertIn("scripts = [", pipeline_py)
        self.assertNotIn('.glob("[0-9][0-9]_*.py")', pipeline_py)

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
            "每项规则只在一处维护",
            "验证采用最低充分层级",
            "直接覆盖受影响组件或合同的测试模块",
            "其余提交、push、提交后同步和 doctor",
            "普通研究项目的数据分析、写作或项目初始化不触发本 skill",
            "review/INDEX.md",
            "未获同意时保持未提交",
        ):
            self.assertIn(fragment, maintenance)
        self.assertIn("maintain_epiagentkit_contracts", routing)
        cases = {case["id"]: case for case in json.loads(routing)["cases"]}
        self.assertIn("epiagentkit-maintenance", cases["new_empty_project"]["excluded"])
        self.assertIn(
            "epiagentkit-maintenance",
            cases["existing_project_analysis"]["excluded"],
        )

    def test_workflow_retrospective_handoff_contract(self) -> None:
        global_rules = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        retrospective = (
            ROOT / "skills" / "workflow-retrospective" / "SKILL.md"
        ).read_text(encoding="utf-8")
        maintenance = (
            ROOT / "skills" / "epiagentkit-maintenance" / "SKILL.md"
        ).read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        cases = {
            case["id"]: case
            for case in json.loads(
                (ROOT / "scripts" / "skill_routing_cases.json").read_text(
                    encoding="utf-8"
                )
            )["cases"]
        }

        for fragment in (
            "当前工作目录生成或更新 `workflow.txt`",
            "为什么现有流程没有阻止",
            "不得声称知道模型未公开的思维过程",
            "用户确认",
            "直接观察",
            "可复核推断",
            "待核验",
            "不直接决定修改文件",
            "根规则、skill、reference、模板、脚本、hook、同步器、测试和 README",
            "假设接收者无法查看当前会话",
            "谁依据什么材料，对什么对象执行什么动作",
            "不查看原会话也能确定每条记录的对象、条件、动作、证据、完成标准和边界",
            "除 `workflow.txt` 外没有因本项复盘产生正式项目改动",
        ):
            self.assertIn(fragment, retrospective)
        self.assertIn("workflow-retrospective", global_rules)
        self.assertIn("接收其它项目的 `workflow.txt`", maintenance)
        self.assertIn("不预先排除能够可靠实现目标的组件", maintenance)
        self.assertIn("不替报告作者补全含义", maintenance)
        self.assertIn("从其它项目交接工作流问题", readme)
        self.assertIn("保证脱离当前会话仍能理解", readme)
        self.assertEqual(
            cases["session_workflow_retrospective"]["primary"],
            "workflow-retrospective",
        )
        self.assertIn(
            "epiagentkit-maintenance",
            cases["session_workflow_retrospective"]["excluded"],
        )
        self.assertEqual(
            cases["maintain_from_workflow_report"]["primary"],
            "epiagentkit-maintenance",
        )
        self.assertIn(
            "workflow-retrospective",
            cases["maintain_from_workflow_report"]["excluded"],
        )
        self.assertIn(
            "workflow-retrospective",
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
            "do not install one silently",
            "`python-docx` or R `officer`",
            "Do not use hidden Word COM automation as an automatic fallback",
            "If any Word process is already running",
            "a new application object does not guarantee process isolation",
        ):
            self.assertIn(fragment, docx)
        for fragment in (
            "Neutral Default Formatting",
            "Do not automatically add dark header bands",
        ):
            self.assertIn(fragment, xlsx)
        self.assertIn("实际 `.docx` 操作调用 `docx`", report)
        self.assertIn("不在本 skill 固定某个转换工具或视觉模板", report)
        self.assertNotIn("无填充、白底黑字", report)

    def test_presentation_template_source_is_routed_before_creation(self) -> None:
        global_rules = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        academic = (ROOT / "skills/academic-ppt/SKILL.md").read_text(
            encoding="utf-8"
        )
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

        self.assertIn("先判模板来源，再用 `academic-ppt`", global_rules)
        self.assertNotIn("sysu-ppt", global_rules)
        self.assertIn("组会、文献分享、方法讲解、开题、中期和答辩", academic)
        self.assertIn("用户提供的 `.pptx` / `.potx`", academic)
        self.assertIn("meeting-and-journal-club.md", academic)
        self.assertIn("proposal-and-defense.md", academic)
        self.assertIn("Template Routing Gate", pptx)
        self.assertIn("中大官方模板、其他学校/机构或特定汇报类型", pptx)
        self.assertIn("load `academic-ppt` as the content workflow", pptx)
        self.assertIn("Use the template-editing workflow, not the from-scratch workflow", pptx)
        self.assertIn("prefer Microsoft PowerPoint", pptx)
        self.assertIn("LibreOffice (`soffice`) is an optional renderer only", pptx)
        self.assertIn("不得把未说明学校的通用 PPT 自动套成中大模板", sysu)
        self.assertIn("绕过 `sysu_init()`", sysu)
        self.assertEqual(
            cases["generic_presentation_template_unspecified"]["primary"],
            "academic-ppt",
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
        self.assertEqual(
            cases["existing_presentation_bounded_edit"]["primary"],
            "pptx",
        )
        self.assertIn(
            "academic-ppt",
            cases["existing_presentation_bounded_edit"]["excluded"],
        )

    def test_academic_ppt_genres_keep_distinct_structures(self) -> None:
        meeting = (
            ROOT / "skills/academic-ppt/references/meeting-and-journal-club.md"
        ).read_text(encoding="utf-8")
        defense = (
            ROOT / "skills/academic-ppt/references/proposal-and-defense.md"
        ).read_text(encoding="utf-8")
        for fragment in (
            "封面后直接进入第一张实质内容页",
            "不生成目录、Agenda",
            "已完成",
            "需要讨论",
        ):
            self.assertIn(fragment, meeting)
        for fragment in (
            "开题",
            "中期",
            "预答辩/答辩",
            "开题稿不生成未存在的前期结果",
            "正式汇报可在时长、模板或评审要求确有需要时使用目录",
        ):
            self.assertIn(fragment, defense)

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
            "结构由研究问题、研究设计、estimand、证据关系、表图和真实篇幅决定",
            "完整初稿",
            "目标期刊未定时生成内容完整、格式中性的学术稿",
            "英文稿：[英文写作]",
            "[英文功能表达与证据约束]",
            "所有完整稿或论文级结构性重写：写作前用 `evidence-research`",
            "已有核验记录时先检查来源身份、版本、适用性和时效",
            "不是跳过适用的内容规范",
            "不得用一两句或几十字的短段代替方法细节",
            "连续单栏写作",
            "不为模拟期刊出版外观自动使用双栏",
            "目标期刊明确要求初投使用双栏",
            "排版终稿或 camera-ready 文件",
            "仍保持文档正文顺序连续",
            "所有单元格保持白底",
            "只保留表顶线、表头下分隔线和表底线",
            "不得为模拟出版外观添加彩色表头、隔行底色或卡片式表格",
        ):
            self.assertIn(fragment, publishing)
        for fragment in (
            "本文件不提供固定段数",
            "不要以固定“总判断",
            "不得通过措辞隐藏",
            "不要求固定五块、七段",
            "完整稿的正文段落应构成完整论证单元",
        ):
            self.assertIn(fragment, playbook)
        self.assertIn("不要求恰好四段", chinese_paper)
        self.assertIn("约 180–450 个中文字符", chinese_paper)
        self.assertIn("不作为凑字数指标", chinese_paper)
        self.assertIn(
            "少于约 150 个中文字符或只有一两句的段落必须逐段复核",
            chinese_paper,
        )
        self.assertIn("数据表使用白底三线表", chinese_paper)
        self.assertIn("不设置通用页数、字数、章节数", chinese_thesis)
        self.assertIn("do not require four paragraphs", english)
        self.assertIn("Do not begin from a stock sentence", phrasebank)
        self.assertIn("内容功能、论证结构、段落节奏", humanizer)
        self.assertIn("不把原有句法、段落习惯或措辞质量作为标准", humanizer)
        self.assertIn("优先符合学科通行写法", humanizer)
        for text in (publishing, humanizer, report):
            self.assertIn("Times New Roman", text)
            self.assertIn("拉丁统计符号", text)
            self.assertIn("`P`", text)
        self.assertIn("可迁移性测试", editorial)
        self.assertIn("结构与长度由任务复杂度决定", report)
        self.assertIn("不强制背景—方法—结果—结论模板", report)
        self.assertIn(
            "academic-humanizer", cases["report_prose_only"]["companions"]
        )
        self.assertEqual(
            cases["english_full_manuscript_with_evidence"]["primary"],
            "academic-publishing",
        )
        for case_id in (
            "paper_from_scratch_word",
            "english_full_manuscript_with_evidence",
            "existing_manuscript_structural_rewrite",
        ):
            self.assertIn("evidence-research", cases[case_id]["companions"])
        self.assertTrue(
            {
                "academic-publishing",
                "biostat-principles",
                "evidence-research",
                "academic-humanizer",
            }.issubset(expand_dependencies({"academic-publishing"}))
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
        self.assertIn(
            "manuscript-peer-review",
            cases["reviewer_response_closure"]["excluded"],
        )
        self.assertEqual(
            cases["single_revision_question_answer_only"]["expected_action"],
            "answer_current_issue_without_creating_files",
        )
        self.assertEqual(
            cases["formal_project_local_word_revision"]["expected_action"],
            "validate_single_artifact_without_project_audit_or_new_state",
        )
        self.assertIn(
            "epi-project-audit",
            cases["formal_project_local_word_revision"]["excluded"],
        )

    def test_shared_academic_language_and_section_matrix_contract(self) -> None:
        humanizer = (
            ROOT / "skills/academic-humanizer/references/chinese-academic-style.md"
        ).read_text(encoding="utf-8")
        opening = (ROOT / "skills/graduate-opening-report/SKILL.md").read_text(
            encoding="utf-8"
        )
        opening_blueprint = (
            ROOT
            / "skills/graduate-opening-report/references/full-report-blueprint.md"
        ).read_text(encoding="utf-8")
        publishing = (ROOT / "skills/academic-publishing/SKILL.md").read_text(
            encoding="utf-8"
        )
        playbook = (
            ROOT / "skills/academic-publishing/references/section-content-playbook.md"
        ).read_text(encoding="utf-8")
        docx = (ROOT / "skills/docx/SKILL.md").read_text(encoding="utf-8")
        scoped_docx = (
            ROOT / "skills/docx/references/scoped-revision.md"
        ).read_text(encoding="utf-8")

        for fragment in (
            "论文、学位论文、开题报告、基金申请书和正式研究报告的正文共用",
            "结构元话语",
            "全局免责声明",
            "防御性转折",
            "审稿回复、rebuttal、cover letter",
        ):
            self.assertIn(fragment, humanizer)
        for fragment in (
            "逐部分生成的控制表",
            "按行逐部分生成并逐项验收",
            "单层“研究目的”",
            "零假设表不是通用组成",
            "正文方法—流程节点—图件/表格—DOCX 位置",
        ):
            self.assertIn(fragment, opening)
        for fragment in (
            "每一行都是一个独立生成单元",
            "登记依据 → 生成本部分 → 核对事实和语言",
            "未关闭的行不得进入最终装配",
        ):
            self.assertIn(fragment, opening_blueprint)
        for fragment in (
            "建立逐部分内容矩阵",
            "关闭一行后再进入下一行",
            "局部润色不因该矩阵扩大范围",
        ):
            self.assertIn(fragment, publishing)
        self.assertIn("按行生成完整内容", playbook)
        for fragment in (
            "academic display tables use three-line rules",
            "Independent list blocks restart explicitly",
        ):
            self.assertIn(fragment, docx)
        for fragment in (
            "first classify the target as an academic display table",
            "official forms, preserve the approved complete borders",
            "each independent list block has an explicit numbering reference",
        ):
            self.assertIn(fragment, scoped_docx)

    def test_scoped_workflow_uses_proportionate_records_and_validation(self) -> None:
        global_rules = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        revision = (
            ROOT / "skills/academic-humanizer/references/revision-workflow.md"
        ).read_text(encoding="utf-8")
        hygiene = (
            ROOT / "skills/project-init/references/project-hygiene.md"
        ).read_text(encoding="utf-8")
        audit = (ROOT / "skills/epi-project-audit/SKILL.md").read_text(
            encoding="utf-8"
        )
        editorial = (
            ROOT / "skills/academic-humanizer/references/patterns-and-preservation.md"
        ).read_text(encoding="utf-8")

        for fragment in (
            "Q 问答",
            "只回复，不创建项目文件",
            "L 局部产物",
            "不补建结果数据文件、修订记录文件或项目记录文件",
            "范围外差异为零",
        ):
            self.assertIn(fragment, global_rules)
        for fragment in (
            "单个引用序号",
            "不创建修订记录文件或项目记录文件",
            "不要只为保存这些要求而创建 JSON",
        ):
            self.assertIn(fragment, revision)
        self.assertIn("Q/L 不迁移用户目录、不补建记录文件或归档", hygiene)
        self.assertIn("批次内文件不进入 layout", hygiene)
        self.assertIn("L 局部产物只检查本次修改影响的部分", audit)
        for section in ("方法", "结果", "讨论", "局限", "结论"):
            self.assertIn(f"| {section} |", editorial)

    def test_peer_review_is_evidence_traced_and_separate_from_author_revision(self) -> None:
        skill = (ROOT / "skills/manuscript-peer-review/SKILL.md").read_text(
            encoding="utf-8"
        )
        criteria = (
            ROOT / "skills/manuscript-peer-review/references/review-criteria.md"
        ).read_text(encoding="utf-8")
        report = (
            ROOT / "skills/manuscript-peer-review/references/report-template.md"
        ).read_text(encoding="utf-8")
        cases = {
            case["id"]: case
            for case in json.loads(
                (ROOT / "scripts/skill_routing_cases.json").read_text(
                    encoding="utf-8"
                )
            )["cases"]
        }

        for fragment in (
            "期刊保密投稿",
            "reporting gap",
            "没有原始数据时不得写",
            "ethics/editor-only",
            "不用于替编辑作最终录用决定",
        ):
            self.assertIn(fragment, skill)
        for fragment in ("样本和分母", "研究设计与偏倚", "统计方法", "语言、结构与参考文献"):
            self.assertIn(fragment, criteria)
        for fragment in ("Major comments", "Coverage matrix", "Reviewer limitations and disclosures"):
            self.assertIn(fragment, report)
        self.assertEqual(
            cases["journal_manuscript_peer_review"]["primary"],
            "manuscript-peer-review",
        )
        self.assertEqual(
            cases["manuscript_only_data_boundary"]["expected_action"],
            "limit_data_claims_to_manuscript_internal_checks",
        )
        self.assertIn(
            "manuscript-peer-review", cases["full_project_audit"]["excluded"]
        )
        self.assertTrue(
            {
                "manuscript-peer-review",
                "biostat-principles",
                "evidence-research",
                "academic-humanizer",
            }.issubset(expand_dependencies({"manuscript-peer-review"}))
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
            "发生了什么、证据位置、影响、已做检查和待决定事项",
            "异常可能改变分析集",
        ):
            self.assertIn(fragment, principles)

    def test_optional_model_diagnostics_are_not_default_validation(self) -> None:
        principles = (ROOT / "skills/biostat-principles/SKILL.md").read_text(
            encoding="utf-8"
        )

        for fragment in (
            "SHAP、特征重要性、替代模型、额外校准",
            "用户明确要求、PROTOCOL/SAP 预设",
            "不得把它们当作普通描述、回归、代码修复或模型复现的默认防御性检查",
            "未生成这些不适用产物不构成缺项",
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
        self.assertNotIn(name, public_skills(ROOT))
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
            self.assertEqual(public_skills(repo), ["alpha", "private-skill"])
            self.assertEqual(available_skills(repo), ["alpha"])
            self.assertEqual(set(source_skills(repo, set())), {"alpha"})

    def test_machine_local_rule_flag_preserves_global_rules(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            repo = base / "repo"
            home = base / "home"
            (repo / "skills").mkdir(parents=True)
            (repo / "hooks").mkdir()
            (repo / "CLAUDE.md").write_text("public rules\n", encoding="utf-8")
            (repo / LOCAL_RULES_PRESERVE_FILE).write_text("\n", encoding="utf-8")
            global_rules = home / ".claude" / "CLAUDE.md"
            global_rules.parent.mkdir(parents=True)
            global_rules.write_text("personal sysu rules\n", encoding="utf-8")

            self.assertTrue(preserve_global_rules(repo))
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/sync_user_configs.py"),
                    "--target",
                    "claude",
                    "--repo-root",
                    str(repo),
                    "--home",
                    str(home),
                    "--components",
                    "rules",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertEqual(
                global_rules.read_text(encoding="utf-8"), "personal sysu rules\n"
            )
            manifest = json.loads(
                (home / ".claude" / ".epiagentkit-install.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertNotIn("rules", manifest["components"])

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
        self.assertIn("docs/showcase/composites/publication-figures.png", body)
        self.assertIn(
            "docs/demo/output/academic-publishing/manuscript-preview-zh.docx",
            body,
        )
        self.assertIn("docs/showcase/composites/manuscripts.png", body)
        self.assertIn("docs/assets/research-workflow.webp", body)
        self.assertIn("docs/showcase/composites/academic-ppt.png", body)
        self.assertIn("docs/showcase/composites/content-skill-illustrations.png", body)
        self.assertIn("docs/showcase/composites/document-skills.png", body)
        self.assertIn(
            "docs/demo/output/document-skills/epi-study-design/home-bp-monitoring-protocol-sap.docx",
            body,
        )
        self.assertIn(
            "docs/demo/output/document-skills/report-writing/fixed-cohort-survival-report.docx",
            body,
        )
        self.assertIn(
            "docs/demo/output/document-skills/report-writing/fixed-cohort-reproducibility-memo.docx",
            body,
        )
        self.assertIn(
            "docs/demo/output/document-skills/manuscript-peer-review/cohort-manuscript-review-report.docx",
            body,
        )
        self.assertIn(
            "docs/demo/output/document-skills/workflow-retrospective/workflow.txt",
            body,
        )
        self.assertIn("欢迎一起参与共建", body)
        self.assertIn("<summary><strong>academic-ppt · 通用学术汇报", body)
        self.assertIn("## 从命令到输出", body)
        self.assertIn("docs/showcase/command-to-output.md", body)
        self.assertNotIn("sysu-ppt", body)
        self.assertNotIn("中大", body)
        self.assertGreaterEqual(body.count("<details>"), 8)
        self.assertNotIn("一次性生成全文", body)
        self.assertNotIn('审查只看代码即可通过', body)
        self.assertNotIn("forest-plot", body)

    def test_manuscript_showcases_use_clean_three_line_tables(self) -> None:
        generator = (
            ROOT / "docs" / "demo" / "generate_manuscript_preview.py"
        ).read_text(encoding="utf-8")
        self.assertIn("set_three_line_table_borders", generator)
        self.assertNotIn('table.style = "Table Grid"', generator)
        self.assertNotIn("shade_cell", generator)

        namespace = {
            "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
        }
        for name in ("manuscript-preview-zh.docx", "manuscript-preview-en.docx"):
            path = (
                ROOT
                / "docs"
                / "demo"
                / "output"
                / "academic-publishing"
                / name
            )
            with zipfile.ZipFile(path) as package:
                document = ET.fromstring(package.read("word/document.xml"))
            tables = document.findall(".//w:tbl", namespace)
            self.assertTrue(tables, name)
            for table in tables:
                rows = table.findall("./w:tr", namespace)
                self.assertGreaterEqual(len(rows), 2, name)
                for row_index, row in enumerate(rows):
                    for cell in row.findall("./w:tc", namespace):
                        shading = cell.find("./w:tcPr/w:shd", namespace)
                        if shading is not None:
                            fill = shading.get(
                                f"{{{namespace['w']}}}fill", "auto"
                            )
                            self.assertIn(fill.upper(), {"AUTO", "FFFFFF"}, name)
                        borders = cell.find(
                            "./w:tcPr/w:tcBorders", namespace
                        )
                        self.assertIsNotNone(borders, name)
                        values = {
                            edge: borders.find(
                                f"./w:{edge}", namespace
                            ).get(f"{{{namespace['w']}}}val")
                            for edge in (
                                "top",
                                "bottom",
                                "left",
                                "right",
                                "insideH",
                                "insideV",
                            )
                        }
                        self.assertEqual(values["left"], "nil", name)
                        self.assertEqual(values["right"], "nil", name)
                        self.assertEqual(values["insideH"], "nil", name)
                        self.assertEqual(values["insideV"], "nil", name)
                        expected_top = "single" if row_index == 0 else "nil"
                        self.assertEqual(values["top"], expected_top, name)
                        expected_bottom = (
                            "single"
                            if row_index in {0, len(rows) - 1}
                            else "nil"
                        )
                        self.assertEqual(
                            values["bottom"], expected_bottom, name
                        )

    def test_document_skill_showcases_use_times_and_clean_tables(self) -> None:
        generator = (
            ROOT / "docs" / "demo" / "generate_document_skill_showcase.py"
        ).read_text(encoding="utf-8")
        self.assertIn('EN_FONT = "Times New Roman"', generator)
        self.assertIn("add_three_line_table", generator)
        self.assertNotIn('table.style = "Table Grid"', generator)

        paths = (
            ROOT
            / "docs/demo/output/document-skills/epi-study-design/home-bp-monitoring-protocol-sap.docx",
            ROOT
            / "docs/demo/output/document-skills/report-writing/fixed-cohort-survival-report.docx",
            ROOT
            / "docs/demo/output/document-skills/report-writing/fixed-cohort-reproducibility-memo.docx",
            ROOT
            / "docs/demo/output/document-skills/manuscript-peer-review/cohort-manuscript-review-report.docx",
            ROOT
            / "docs/demo/output/document-skills/workflow-retrospective/workflow-retrospective-display.docx",
        )
        namespace = {
            "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
        }
        p_formatted_documents = 0
        for path in paths:
            self.assertTrue(path.is_file(), path)
            with zipfile.ZipFile(path) as package:
                document_xml = package.read("word/document.xml")
                styles_xml = package.read("word/styles.xml")
            self.assertIn(b"Times New Roman", document_xml)
            self.assertIn(b"Times New Roman", styles_xml)
            document = ET.fromstring(document_xml)

            found_formatted_p = False
            for run in document.findall(".//w:r", namespace):
                text = "".join(
                    node.text or "" for node in run.findall("./w:t", namespace)
                )
                if text == "P":
                    properties = run.find("./w:rPr", namespace)
                    if (
                        properties is not None
                        and properties.find("./w:b", namespace) is not None
                        and properties.find("./w:i", namespace) is not None
                    ):
                        found_formatted_p = True
            if found_formatted_p:
                p_formatted_documents += 1

            for table in document.findall(".//w:tbl", namespace):
                rows = table.findall("./w:tr", namespace)
                self.assertGreaterEqual(len(rows), 2, path.name)
                for row_index, row in enumerate(rows):
                    for cell in row.findall("./w:tc", namespace):
                        shading = cell.find("./w:tcPr/w:shd", namespace)
                        if shading is not None:
                            fill = shading.get(
                                f"{{{namespace['w']}}}fill", "auto"
                            )
                            self.assertIn(fill.upper(), {"AUTO", "FFFFFF"}, path.name)
                        borders = cell.find("./w:tcPr/w:tcBorders", namespace)
                        self.assertIsNotNone(borders, path.name)
                        for edge in ("left", "right", "insideH", "insideV"):
                            node = borders.find(f"./w:{edge}", namespace)
                            self.assertIsNotNone(node, path.name)
                            self.assertEqual(
                                node.get(f"{{{namespace['w']}}}val"),
                                "nil",
                                path.name,
                            )
                        top = borders.find("./w:top", namespace)
                        bottom = borders.find("./w:bottom", namespace)
                        expected_top = "single" if row_index == 0 else "nil"
                        expected_bottom = (
                            "single"
                            if row_index in {0, len(rows) - 1}
                            else "nil"
                        )
                        self.assertEqual(
                            top.get(f"{{{namespace['w']}}}val"),
                            expected_top,
                            path.name,
                        )
                        self.assertEqual(
                            bottom.get(f"{{{namespace['w']}}}val"),
                            expected_bottom,
                            path.name,
                        )
        self.assertGreaterEqual(p_formatted_documents, 3)
        workflow = (
            ROOT
            / "docs/demo/output/document-skills/workflow-retrospective/workflow.txt"
        )
        self.assertIn("问题 WF-001", workflow.read_text(encoding="utf-8"))

    def test_release_bundle_keeps_source_archive_and_runtime_separate(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        usage = (ROOT / "docs" / "release-1.1-usage.md").read_text(
            encoding="utf-8"
        )
        notice = (ROOT / "docs" / "release-notice.md").read_text(
            encoding="utf-8"
        )
        builder = (ROOT / "scripts" / "build_release.py").read_text(
            encoding="utf-8"
        )

        for fragment in (
            "请把 EpiAgentKit 安装到当前 Claude Code",
            "请把 EpiAgentKit 安装到当前 Codex",
            "releases/tag/v1.1",
            "保留我现有的个人配置",
            "只在明确需要自己操作时查看命令行方式",
            "python scripts/build_release.py",
            "$skill-creator",
            "实际问题：",
            "必须保留：",
            "audit_workflow_contracts.py",
        ):
            self.assertIn(fragment, readme)
        for fragment in (
            "推荐交给当前 Agent 安装",
            "请把这个 EpiAgentKit release 安装到当前 Claude Code",
            "请把这个 EpiAgentKit release 安装到当前 Codex",
            "Agent 无法代为安装时的人工备用命令",
            "源仓库、release 和实际安装目录应彼此分开",
            "SKILLS_INCLUDED.txt",
            "~/.claude/CLAUDE.md",
            "~/.codex/AGENTS.md",
            "~/.agents/skills/",
            "安装到 Claude Code",
            "安装到 Codex",
            "更新与回退",
        ):
            self.assertIn(fragment, usage)
        self.assertNotIn("SHA-256", usage)
        self.assertNotIn("Get-FileHash", usage)
        for fragment in (
            "docx",
            "academic-ppt",
            "sysu-ppt",
            "epiagentkit-maintenance",
            "recipes_common_50",
            "imagegen",
            "不构成公开再分发授权",
        ):
            self.assertIn(fragment, notice)
        for fragment in (
            "INCLUDED_SKILLS",
            "PUBLICATION_FIGURE_FILES",
            "--allow-dirty",
            "--force",
            "FIXED_ZIP_TIME",
            "SHA256SUMS",
        ):
            self.assertIn(fragment, builder)

    def test_publication_figures_trigger_is_statistical(self) -> None:
        body = (ROOT / "skills" / "publication-figures" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("发表级统计图、数据图", body)
        self.assertIn(
            "流程、病例筛选、机制、架构、技术路线与图形摘要转 `research-visuals`",
            body,
        )
        self.assertIn("作图前确认", body)
        self.assertIn("默认一次只生成一张独立统计图", body)
        self.assertIn("不得为了展示能力主动拼合不同图型", body)
        self.assertIn("风险集表、置信区间和该图必需的图例属于单图组成部分", body)
        self.assertIn("`results/results.yaml`", body)
        self.assertNotIn("用户要求出图、画图、做图、生成 Fig", body)

    def test_publication_figures_preserves_visual_grammar_and_redesigns_when_requested(
        self,
    ) -> None:
        body = (ROOT / "skills" / "publication-figures" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("只修改一张指定的图或一个格式问题", body)
        self.assertIn("其余布局、图形元素和视觉表达保持不变", body)
        self.assertIn("用户明确对样式不满", body)
        self.assertIn("再进行重新设计", body)
        self.assertIn("同一项目", body)
        self.assertIn("不得检索近期论文只为模仿风格", body)
        self.assertIn("期刊未指定白色背景时，不把白色背景当作通用投稿要求", body)
        self.assertNotIn("无 3D / 默认灰底 / 彩虹色 / 单独 JPEG", body)

    def test_publication_figures_separates_manuscript_figure_from_caption(self) -> None:
        skill = (ROOT / "skills" / "publication-figures" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        layout = (
            ROOT
            / "skills"
            / "publication-figures"
            / "references"
            / "manuscript-layout.md"
        ).read_text(encoding="utf-8")
        self.assertIn("读取 [论文统计图版式](references/manuscript-layout.md)", skill)
        self.assertIn("只保留一个居中短标题", skill)
        self.assertIn("PPT 的信息层级带进图内", skill)
        self.assertIn("总样本量、总事件数、分析集和随访概况", layout)
        self.assertIn("仪表板卡片、顶部指标栏", layout)
        self.assertIn("风险集表、纳入流程、分母比较", layout)
        self.assertIn("默认分别生成和审查每张图", layout)
        self.assertIn("不能为了展示方法数量", layout)
        self.assertIn("以整张导出画布为参照", layout)
        self.assertIn("字号按最终物理尺寸设置和核对", layout)
        self.assertIn("Times New Roman", skill)
        self.assertIn("拉丁统计符号", skill)
        self.assertIn("粗斜体", skill)
        self.assertIn("Times New Roman 粗斜体", layout)
        self.assertIn("其它拉丁统计符号", layout)
        self.assertIn("图内标题 10–12 pt、轴标题 8–10 pt", layout)
        self.assertIn("图题通常只用简短名词短语", layout)
        self.assertIn("不把方法段或读图说明自动接在图题后", layout)
        self.assertIn("必要图注只补充正文和图本身无法清楚承担的信息", layout)

        fig_setup = (
            ROOT / "skills" / "publication-figures" / "scripts" / "fig_setup.R"
        ).read_text(encoding="utf-8")
        self.assertIn('PLOT_FAMILY_EN <- .register_en_font()', fig_setup)
        self.assertIn('fallback <- "Times New Roman"', fig_setup)
        self.assertIn('"C:/Windows/Fonts/times.ttf"', fig_setup)
        self.assertIn('language = c("mixed", "english", "chinese")', fig_setup)
        self.assertIn('identical(language, "english")', fig_setup)

        manuscript_demo = (
            ROOT / "docs" / "demo" / "generate_manuscript_preview.py"
        ).read_text(encoding="utf-8")
        self.assertIn("图 1　两种治疗方案的调整后无事件生存曲线", manuscript_demo)
        self.assertNotIn("曲线由多变量 Cox 比例风险模型估计", manuscript_demo)
        self.assertNotIn("科研工作流", manuscript_demo)

    def test_results_machine_source_is_not_the_derived_markdown(self) -> None:
        body = (
            ROOT
            / "skills"
            / "academic-publishing"
            / "references"
            / "chinese-thesis.md"
        ).read_text(encoding="utf-8")
        self.assertIn("新项目统一从 `results/results.yaml` 读取数字", body)
        self.assertIn("旧项目可读取 `07_paper/results.yaml`", body)
        self.assertNotIn("结果变 → 回写 `0_result_summaries.md`", body)

    def test_audit_continues_all_layers_but_blocks_signoff(self) -> None:
        body = (ROOT / "skills" / "epi-project-audit" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("每层都继续审查，不因前层失败而停止", body)
        self.assertIn("| ERROR | 可能改变科学结论", body)
        self.assertIn("结构偏好一般是 WARN/INFO", body)
        self.assertIn("只审查模式严格只读", body)
        self.assertNotIn("不通过不进入下一层", body)
        self.assertNotIn("### 自动修复动作", body)

        checklist = (
            ROOT
            / "skills"
            / "epi-project-audit"
            / "references"
            / "audit-checklist.md"
        ).read_text(encoding="utf-8")
        self.assertIn("新项目使用 `results/results.yaml`", checklist)
        self.assertIn("`result_summaries.md` 如存在", checklist)
        self.assertIn("明确标注不可编辑", checklist)
        self.assertIn("小于 1 通常表示预测过于极端", checklist)


if __name__ == "__main__":
    unittest.main()
