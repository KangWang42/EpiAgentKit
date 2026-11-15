from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from lxml import etree


ROOT = Path(__file__).resolve().parents[2]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CONTRACT_VALIDATOR = load_module(
    "manuscript_contract_validator",
    ROOT
    / "skills"
    / "academic-publishing"
    / "scripts"
    / "validate_manuscript_contract.py",
)
TABLE_RECONCILER = load_module(
    "table_field_reconciler",
    ROOT
    / "skills"
    / "academic-publishing"
    / "scripts"
    / "reconcile_table_fields.py",
)
DOCX_AUDITOR = load_module(
    "docx_delivery_auditor",
    ROOT / "skills" / "docx" / "scripts" / "audit_docx.py",
)


def base_contract() -> dict:
    return {
        "schema_version": 1,
        "mode": "complete_manuscript",
        "status": "complete",
        "artifacts": [
            {
                "id": "manuscript",
                "audience": "journal readers",
                "purpose": "report the verified study",
                "output": "paper/manuscript.docx",
                "allowed_information": ["final scientific methods", "verified results"],
                "forbidden_information": ["debug history", "internal paths"],
            }
        ],
        "modules": [
            {
                "id": "cohort",
                "kind": "design",
                "source": ["PROTOCOL.md"],
                "manuscript_locations": ["methods", "results"],
                "required_fields": ["time zero", "follow-up", "censoring"],
            },
            {
                "id": "survival",
                "kind": "method",
                "source": ["SAP.md"],
                "manuscript_locations": ["methods", "results"],
                "required_fields": ["time scale", "events", "risk set", "HR and CI"],
            },
        ],
        "sections": [
            {
                "id": "methods",
                "function": "define the cohort and survival analysis",
                "evidence_sources": ["PROTOCOL.md", "SAP.md"],
                "modules": ["cohort", "survival"],
                "output": "Methods",
                "content_check": "passed",
            },
            {
                "id": "results",
                "function": "report follow-up and survival estimates",
                "evidence_sources": ["results/results.yaml"],
                "modules": ["cohort", "survival"],
                "output": "Results",
                "content_check": "passed",
            },
        ],
        "tables": [
            {
                "id": "association-table",
                "role": "report adjusted associations",
                "source": "results/results.yaml",
                "placement": "body",
                "caption": "Adjusted associations",
                "columns": [
                    {"field_id": "term", "label": "Term", "source_field": "term"},
                    {"field_id": "estimate", "label": "HR (95% CI)", "source_field": "estimate_display"},
                    {"field_id": "model_p", "label": "P value", "source_field": "p_display"},
                ],
            }
        ],
        "figures": [
            {
                "id": "survival-curve",
                "role": "show disease-free survival",
                "source": "04_figures/survival.png",
                "placement": "body",
                "caption": "Disease-free survival",
            }
        ],
        "checks": {
            "content": "passed",
            "field_reconciliation": "passed",
            "file_display": "passed",
        },
    }


def signed_contract() -> dict:
    contract = base_contract()
    for module in contract["modules"]:
        module["status"] = "passed"
    contract["manuscript_lock"] = {
        "selected_input": "paper/manuscript.docx",
        "input_hash": "sha256:verified-final-hash",
        "round": "initial",
        "anonymity": "not_required",
    }
    contract["fact_locks"] = [
        {
            "id": "study-design",
            "topic": "study design",
            "value": "prospective cohort",
            "sources": ["PROTOCOL.md"],
            "manuscript_locations": ["methods"],
            "status": "confirmed",
        }
    ]
    contract["analysis_items"] = [
        {
            "id": "primary-survival-analysis",
            "tier": "primary",
            "purpose": "estimate the primary survival association",
            "method_module": "survival",
            "analysis_set": "confirmed primary analysis set",
            "result_source": "results/results.yaml#results.primary_survival",
            "manuscript_locations": ["methods", "results"],
            "status": "passed",
        }
    ]
    contract["release"] = {
        "target": "submission",
        "journal_requirements_source": "verified official author instructions",
        "checks": [
            {"id": check_id, "status": "passed", "evidence": [f"evidence:{check_id}"]}
            for check_id in sorted(CONTRACT_VALIDATOR.REQUIRED_RELEASE_CHECKS)
        ],
        "blocking_items": [],
    }
    return contract


class ManuscriptWorkflowContractTests(unittest.TestCase):
    def test_cohort_survival_contract_passes_without_cross_sectional_template(self) -> None:
        errors = CONTRACT_VALIDATOR.validate_contract(base_contract())

        self.assertEqual(errors, [])

    def test_cross_sectional_survey_mediation_requirements_compose(self) -> None:
        contract = base_contract()
        contract["modules"] = [
            {
                "id": "cross-sectional",
                "kind": "design",
                "source": ["PROTOCOL.md"],
                "manuscript_locations": ["methods", "results"],
                "required_fields": ["same time window", "analysis denominator"],
            },
            {
                "id": "survey-weighting",
                "kind": "method",
                "source": ["SAP.md"],
                "manuscript_locations": ["methods", "results"],
                "required_fields": ["weights", "strata", "clusters", "variance estimation"],
            },
            {
                "id": "mediation",
                "kind": "method",
                "source": ["SAP.md", "AGReMA"],
                "manuscript_locations": ["methods", "results"],
                "required_fields": ["effect definition", "scale", "uncertainty", "interpretation boundary"],
            },
        ]
        for section in contract["sections"]:
            section["modules"] = [
                "cross-sectional",
                "survey-weighting",
                "mediation",
            ]

        errors = CONTRACT_VALIDATOR.validate_contract(contract)

        self.assertEqual(errors, [])

    def test_duplicate_visible_labels_pass_but_duplicate_field_ids_fail(self) -> None:
        contract = base_contract()
        columns = contract["tables"][0]["columns"]
        columns.extend(
            [
                {"field_id": "offline_p", "label": "P value", "source_field": "offline_p"},
                {"field_id": "online_p", "label": "P value", "source_field": "online_p"},
            ]
        )
        self.assertEqual(CONTRACT_VALIDATOR.validate_contract(contract), [])

        columns[-1]["field_id"] = "offline_p"
        errors = CONTRACT_VALIDATOR.validate_contract(contract)

        self.assertTrue(any("field_id 必须唯一" in error for error in errors))

    def test_complete_status_requires_all_three_checks(self) -> None:
        contract = base_contract()
        contract["checks"]["file_display"] = "blocked"

        errors = CONTRACT_VALIDATOR.validate_contract(contract)

        self.assertTrue(any("三项检查必须全部为 passed" in error for error in errors))

    def test_formal_signoff_passes_only_with_closed_author_side_evidence(self) -> None:
        contract = signed_contract()

        self.assertEqual(
            CONTRACT_VALIDATOR.validate_contract(contract, signoff=True), []
        )

        contract["fact_locks"][0]["status"] = "pending"
        errors = CONTRACT_VALIDATOR.validate_contract(contract, signoff=True)
        self.assertTrue(any("研究事实" in error and "confirmed" in error for error in errors))

        contract = signed_contract()
        contract["fact_locks"][0]["manuscript_locations"] = ["unknown-section"]
        errors = CONTRACT_VALIDATOR.validate_contract(contract, signoff=True)
        self.assertTrue(any("未声明的稿件位置" in error for error in errors))

        contract = signed_contract()
        contract["analysis_items"][0]["result_source"] = ""
        errors = CONTRACT_VALIDATOR.validate_contract(contract, signoff=True)
        self.assertTrue(any("result_source 不能为空" in error for error in errors))

        contract = signed_contract()
        contract["release"]["checks"] = [
            item
            for item in contract["release"]["checks"]
            if item["id"] != "disclosures"
        ]
        errors = CONTRACT_VALIDATOR.validate_contract(contract, signoff=True)
        self.assertTrue(any("缺少必要检查：disclosures" in error for error in errors))

    def test_revision_signoff_requires_one_revision_state_and_closed_comments(self) -> None:
        contract = signed_contract()
        contract["release"]["target"] = "revision_resubmission"

        errors = CONTRACT_VALIDATOR.validate_contract(contract, signoff=True)
        self.assertTrue(any("唯一 revision_state" in error for error in errors))
        self.assertTrue(any("revision_closure" in error for error in errors))

        contract["release"]["revision_state"] = "paper/revision-state.json"
        contract["release"]["checks"].append(
            {
                "id": "revision_closure",
                "status": "passed",
                "evidence": ["validate_revision_state.py --signoff"],
            }
        )
        self.assertEqual(
            CONTRACT_VALIDATOR.validate_contract(contract, signoff=True), []
        )

    def test_signoff_cli_blocks_recorded_submission_issues(self) -> None:
        script = (
            ROOT
            / "skills"
            / "academic-publishing"
            / "scripts"
            / "validate_manuscript_contract.py"
        )
        with tempfile.TemporaryDirectory() as directory:
            contract_path = Path(directory) / "manuscript-contract.json"
            contract = signed_contract()
            environment = dict(os.environ)
            environment["PYTHONIOENCODING"] = "utf-8"
            contract_path.write_text(
                json.dumps(contract, ensure_ascii=False), encoding="utf-8"
            )
            passed = subprocess.run(
                [sys.executable, str(script), str(contract_path), "--signoff", "--json"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                env=environment,
                check=False,
            )
            self.assertEqual(passed.returncode, 0, passed.stdout + passed.stderr)
            self.assertEqual(json.loads(passed.stdout)["status"], "PASS")

            contract["release"]["blocking_items"] = ["ethics approval pending"]
            contract_path.write_text(
                json.dumps(contract, ensure_ascii=False), encoding="utf-8"
            )
            blocked = subprocess.run(
                [sys.executable, str(script), str(contract_path), "--signoff", "--json"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                env=environment,
                check=False,
            )
            self.assertEqual(blocked.returncode, 1, blocked.stdout + blocked.stderr)
            self.assertTrue(
                any(
                    "blocking_items" in error
                    for error in json.loads(blocked.stdout)["errors"]
                )
            )

    def test_method_specific_references_are_loaded_only_when_used(self) -> None:
        signoff = (
            ROOT / "skills/academic-publishing/references/submission-signoff.md"
        ).read_text(encoding="utf-8")
        reporting = (
            ROOT / "skills/academic-publishing/references/statistical-reporting.md"
        ).read_text(encoding="utf-8")
        publishing = (ROOT / "skills/academic-publishing/SKILL.md").read_text(
            encoding="utf-8"
        )
        review_killers = (
            ROOT / "skills/academic-publishing/references/review-killers.md"
        ).read_text(encoding="utf-8")
        method_references = {
            "MCA 与 PCA": ROOT
            / "skills/academic-publishing/references/method-dimension-reduction.md",
            "交互作用与亚组": ROOT
            / "skills/academic-publishing/references/method-interaction-subgroup.md",
            "Bootstrap 与重抽样": ROOT
            / "skills/academic-publishing/references/method-resampling.md",
            "分位数回归": ROOT
            / "skills/academic-publishing/references/method-quantile-regression.md",
            "预后模型与风险分层": ROOT
            / "skills/academic-publishing/references/method-prognostic-models.md",
        }

        for fragment in (
            "局部修改只核对指定内容",
            "不得为“再保险”重复运行同一检查",
            "多个合理当前稿并存时由用户指定",
            "只能由作者或权威原始文件确认",
            "声称实施的方法必须有非空结果",
            "不复制第二份意见矩阵",
        ):
            self.assertIn(fragment, signoff)
        for fragment in (
            "每种实际采用的方法建立一行",
            "没有对应本地 reference 时",
            "未采用的方法不读取专项 reference、不检查相应字段、不补做分析",
            "不得套用名称相近但 estimand、数据结构或假设不同的方法分支",
        ):
            self.assertIn(fragment, reporting)
        for method_name in ("MCA", "Bootstrap", "分位数回归", "交互和亚组"):
            self.assertNotIn(method_name, reporting)
            self.assertNotIn(method_name, signoff)
        for label, path in method_references.items():
            body = path.read_text(encoding="utf-8")
            self.assertIn("只在稿件实际", body, label)
            self.assertIn("方法、结果、表图和讨论", body, label)
            self.assertIn(path.name, publishing)
        self.assertIn("未采用时不读取、不检查，也不补做", publishing)
        self.assertIn("采用其它专项方法", publishing)
        self.assertIn("不得选择名称相近的上述分支代替", publishing)
        self.assertIn("含量化估计、统计模型或定量证据综合的稿件", publishing)
        self.assertIn("纯质性研究、叙述性综述或不含量化结果的论文不读取", publishing)
        self.assertNotIn(
            "所有完整稿：[内容与章节功能](references/section-content-playbook.md) 和 [统计报告]",
            publishing,
        )
        self.assertIn("纯质性研究或不含量化结果的论文不加载本文件", reporting)
        self.assertIn("只检查稿件实际采用的专项方法", review_killers)
        for project_specific_example in (
            "FactoMineR",
            "quantreg",
            "ADL",
            "Barthel",
            "49 份文本",
            "24.1±10.3",
            "审稿人必抓",
        ):
            self.assertNotIn(project_specific_example, review_killers)
        self.assertNotIn("bootstrap", review_killers.casefold())
        self.assertIn("局部润色、单项修正和纯版式修改不触发", publishing)
        all_method_text = "".join(
            path.read_text(encoding="utf-8") for path in method_references.values()
        )
        self.assertNotIn("18 项 ZBI", signoff + reporting + all_method_text)
        self.assertNotIn("0–72", signoff + reporting + all_method_text)

    def test_table_reconciliation_uses_position_for_repeated_visible_headers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.csv"
            display = root / "display.csv"
            source.write_text(
                "term,offline_p,online_p,overall_p\nCognition,0.112,,0.021\n",
                encoding="utf-8",
            )
            display.write_text(
                "变量,P值,P值,P值\nCognition,0.112,,0.021\n",
                encoding="utf-8",
            )
            spec = {
                "schema_version": 1,
                "row_keys": [{"source_column": "term", "display_column": 0}],
                "fields": [
                    {"field_id": "offline_p", "source_column": "offline_p", "display_column": 1},
                    {"field_id": "online_p", "source_column": "online_p", "display_column": 2},
                    {"field_id": "overall_p", "source_column": "overall_p", "display_column": 3},
                ],
            }

            passed = TABLE_RECONCILER.reconcile(source, display, spec)
            self.assertEqual(passed["status"], "PASS")

            display.write_text(
                "变量,P值,P值,P值\nCognition,0.021,,0.021\n",
                encoding="utf-8",
            )
            failed = TABLE_RECONCILER.reconcile(source, display, spec)

            self.assertEqual(failed["status"], "FAIL")
            self.assertEqual(failed["mismatches"][0]["field_id"], "offline_p")
            self.assertEqual(failed["mismatches"][0]["source_value"], "0.112")
            self.assertEqual(failed["mismatches"][0]["display_value"], "0.021")

    def test_workflow_keeps_full_manuscript_contract_out_of_local_edits(self) -> None:
        publishing = (
            ROOT / "skills/academic-publishing/SKILL.md"
        ).read_text(encoding="utf-8")
        contract = (
            ROOT / "skills/academic-publishing/references/manuscript-contract.md"
        ).read_text(encoding="utf-8")
        report = (
            ROOT / "skills/report-writing/references/epidemiology-report-blueprint.md"
        ).read_text(encoding="utf-8")
        principles = (
            ROOT / "skills/biostat-principles/SKILL.md"
        ).read_text(encoding="utf-8")

        self.assertIn("局部部件不因此建立整篇约定", publishing)
        self.assertIn("局部部件只锁定该部件及其直接关系", contract)
        self.assertIn("不规定固定章节数、表图数", contract)
        self.assertIn("含问卷变量不等于自动采用 CROSS", contract)
        self.assertIn("不把论文删短后改名为报告", report)
        self.assertIn("不为此给普通项目增加锁文件、PID 文件或新的状态机制", principles)

    def test_review_and_background_parts_exclude_author_unpublished_methods(self) -> None:
        # 回归：叙述性综述第5章曾把作者未发表的方法写成“改进方向”，而数字、引文和样式检查全部通过。
        editorial = (
            ROOT / "skills/academic-humanizer/references/patterns-and-preservation.md"
        ).read_text(encoding="utf-8")
        style = (
            ROOT / "skills/academic-humanizer/references/chinese-academic-style.md"
        ).read_text(encoding="utf-8")
        callers = {
            path: (ROOT / path).read_text(encoding="utf-8")
            for path in (
                "skills/academic-publishing/SKILL.md",
                "skills/academic-humanizer/SKILL.md",
                "skills/academic-humanizer/references/chinese-academic-style.md",
            )
        }
        meeting = (
            ROOT / "skills/academic-ppt/references/meeting-and-journal-club.md"
        ).read_text(encoding="utf-8")
        global_rules = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")

        self.assertNotIn("支持研究思路", editorial)
        self.assertIn("### 内容来源与材料取舍", editorial)
        self.assertIn("作者本人未发表的方法设计、参数、流程、结果和拟采用方案", editorial)
        self.assertIn("开题报告的研究内容、技术路线、可行性与预期结果", editorial)
        self.assertIn("写到“现有研究尚未……”这一问题层面", editorial)
        for path, text in callers.items():
            self.assertNotIn("材料取舍与作者反馈", text, path)
            self.assertIn("内容来源与材料取舍", text, path)
        self.assertIn("各段依据是否属于该部件允许的内容来源", style)
        self.assertIn("与本研究的关系放在明确标为本研究的页面或答问中", meeting)
        self.assertIn("科研文本逐段核对依据来源是否属于所在部件", global_rules)

    def test_structure_follows_template_then_same_type_exemplars(self) -> None:
        # 回归：综述单设“局限与展望”章并以“结语”收束，同类范文实际以“总结（与展望）”收束；审查未读范文即判断结构。
        style = (
            ROOT / "skills/academic-humanizer/references/chinese-academic-style.md"
        ).read_text(encoding="utf-8")
        humanizer = (ROOT / "skills/academic-humanizer/SKILL.md").read_text(encoding="utf-8")
        publishing = (ROOT / "skills/academic-publishing/SKILL.md").read_text(encoding="utf-8")

        self.assertIn("逐篇列出其实际章节标题、顺序、各章功能", style)
        self.assertIn("不得用自行概括的框架代替范文的实际章节", style)
        self.assertIn("比对前须实际读取模板或范文，不凭印象判断", humanizer)
        self.assertNotIn("用户提供参考论文时只学习信息密度、部件功能", humanizer)
        self.assertIn("- **叙述性综述**", publishing)
        self.assertIn("以“总结”或“总结与展望”收束", publishing)
        self.assertIn("不另设“不足”或“局限”章", publishing)
        self.assertIn("不套用原始研究的 estimand、统计报告和报告规范约定", publishing)

    def test_compression_has_baseline_floor_and_corrections_trigger_full_review(self) -> None:
        # 回归：综述多轮“删重复”后仅为同类范文篇幅的六成，研究只剩名称；作者需逐处指出问题。
        style = (
            ROOT / "skills/academic-humanizer/references/chinese-academic-style.md"
        ).read_text(encoding="utf-8")
        humanizer = (ROOT / "skills/academic-humanizer/SKILL.md").read_text(encoding="utf-8")

        self.assertIn("各章篇幅比例和代表研究的写法", style)
        self.assertIn("压缩后各章篇幅和研究描述是否仍不低于结构基线", style)
        self.assertIn("删除表图时，其承载的必要结果是否已转入正文", style)
        self.assertIn("以及作者纠正结构、内容来源或篇幅之后", humanizer)
        self.assertIn("一次报告全部偏离，不等作者逐处指出", humanizer)

    def test_outlook_is_grounded_and_not_a_restated_plan(self) -> None:
        # 回归：展望写成与问题一一对应的清单，三条恰为作者方法的组成部分，关键词扫描未发现。
        editorial = (
            ROOT / "skills/academic-humanizer/references/patterns-and-preservation.md"
        ).read_text(encoding="utf-8")
        style = (
            ROOT / "skills/academic-humanizer/references/chinese-academic-style.md"
        ).read_text(encoding="utf-8")

        self.assertIn("展望随对应问题写出已有文献提供的方法基础和尚存缺口", editorial)
        self.assertIn("不另列与问题一一对应、只换说法的方向清单", editorial)
        self.assertIn("作者方案换了措辞仍属同一内容，不以关键词扫描代替", editorial)
        self.assertIn("不规范写法不随结构照搬", style)

    def test_full_manuscripts_are_written_from_journal_exemplars(self) -> None:
        # 回归：目标期刊须知超时后按通用规范成稿，回归表、单因素检验、附表和 STROBE 声明均不合该刊惯例；
        # 作者要求列出题名由其下载全文，写作必须有参考论文，正文详略够用即可。
        contract = (
            ROOT / "skills/academic-publishing/references/manuscript-contract.md"
        ).read_text(encoding="utf-8")
        publishing = (ROOT / "skills/academic-publishing/SKILL.md").read_text(encoding="utf-8")
        playbook = (
            ROOT / "skills/academic-publishing/references/section-content-playbook.md"
        ).read_text(encoding="utf-8")
        style = (
            ROOT / "skills/academic-humanizer/references/chinese-academic-style.md"
        ).read_text(encoding="utf-8")
        evidence = (ROOT / "skills/evidence-research/SKILL.md").read_text(encoding="utf-8")

        self.assertIn("完整论文和论文级结构性重写必须以同类已发表论文为参考写作", contract)
        self.assertIn("从期刊官网或数据库自行取得全文；取不到时把题名、期刊、年卷期和 DOI 列给用户", contract)
        self.assertIn("取得全文之前，只做不依赖范文的准备工作", contract)
        self.assertIn("官方投稿须知取不到时同样执行", contract)
        self.assertIn("结果正文报告哪些统计量而哪些只放表中", contract)
        self.assertIn("正文详略以同类论文为准，写到读者需要的程度即可", contract)
        self.assertIn("不得为迎合惯例写成“以单因素分析有统计学意义的变量为自变量”", contract)
        self.assertIn("正文是否写“参照某规范报告”、是否附核对表", contract)
        self.assertIn("取得之前不起草正文", publishing)
        self.assertIn("官方须知取不到时不跳过同类论文", publishing)
        self.assertIn("分析请求产生的全部输出不等于论文的报告范围", playbook)
        self.assertIn("未确认前不写入稿件", playbook)
        self.assertIn("详略以同类论文为准，够用即可", playbook)
        self.assertIn("第6节由执行者取得同类文章", style)
        self.assertIn("需要全文时先自行从期刊官网、数据库或开放获取来源取得", evidence)
        self.assertIn("以摘要核验即可，不要求全文", evidence)

    def test_missing_and_adverse_facts_require_source_search_and_author_confirmation(self) -> None:
        # 回归：作者既往稿件和原始数据已载明的方法事实被写成整段待核验；
        # 依据英文版得出的条目“差异”被写成与中文版不同，作者确认实际一致。
        publishing = (ROOT / "skills/academic-publishing/SKILL.md").read_text(encoding="utf-8")

        self.assertIn("使用前先查作者既往稿件、原始数据字段与问卷原文", publishing)
        self.assertIn("须以所比较的同一语言版本原文为依据，并经作者确认后才写入正文", publishing)

    def test_user_material_list_claim_subjects_and_two_way_length_check(self) -> None:
        # 回归：候选文献摘要中的“自评健康”实指被照护者；引言写成范文两倍长、参考文献明显少于范文均未被发现；
        # 作者表示需要的材料可以提供，要求以可发表论文为目的一次说明所需材料。
        publishing = (ROOT / "skills/academic-publishing/SKILL.md").read_text(encoding="utf-8")
        contract = (
            ROOT / "skills/academic-publishing/references/manuscript-contract.md"
        ).read_text(encoding="utf-8")
        evidence = (ROOT / "skills/evidence-research/SKILL.md").read_text(encoding="utf-8")

        self.assertIn("写作以形成符合目标期刊发表要求的论文为目的", publishing)
        self.assertIn("一次性列出需要用户提供的材料清单", publishing)
        self.assertIn("同类论文、待引文献和期刊要求先由执行者自行检索取得", publishing)
        self.assertIn("逐项写明内容（题名、期刊、年卷期、DOI 或待确认的具体事实）、用途和当前核验状态", publishing)
        self.assertIn("核对论断所指的对象、人群、测量和比较与引用处一致", evidence)
        self.assertIn("摘要无法确定时以全文为准", evidence)
        self.assertIn("参考文献数量与中外文构成", contract)
        self.assertIn("超出部分承载本研究新发现时向作者说明篇幅差异，由作者决定是否保留", contract)
        self.assertIn("明显短于范文的部分据实补足", contract)

    def test_discussion_interprets_variables_by_measurement(self) -> None:
        # 回归：被照护者累计接受照护的时间在讨论中被解释为照护者本人的照护年限；
        # 说明该差异的句子在“够用即可”的压缩中被删除。
        playbook = (
            ROOT / "skills/academic-publishing/references/section-content-playbook.md"
        ).read_text(encoding="utf-8")
        contract = (
            ROOT / "skills/academic-publishing/references/manuscript-contract.md"
        ).read_text(encoding="utf-8")

        self.assertIn("解释每个变量时与其测量定义一致", playbook)
        self.assertIn("不写成研究对象本人的特征或经历", playbook)
        self.assertIn("说明变量实际测量含义且决定主要结果解释的句子", contract)

    def test_docx_inventory_rejects_duplicate_internal_field_ids(self) -> None:
        document_xml = f"""
        <w:document xmlns:w="{DOCX_AUDITOR.W_NS}">
          <w:body>
            <w:p><w:pPr><w:jc w:val="left"/></w:pPr><w:r><w:t>表1 关联结果</w:t></w:r></w:p>
            <w:tbl>
              <w:tr><w:tc><w:p><w:r><w:t>变量</w:t></w:r></w:p></w:tc>
              <w:tc><w:p><w:r><w:t>P 值</w:t></w:r></w:p></w:tc>
              <w:tc><w:p><w:r><w:t>P 值</w:t></w:r></w:p></w:tc></w:tr>
            </w:tbl>
          </w:body>
        </w:document>
        """.encode("utf-8")
        parts = {"word/document.xml": document_xml}
        document = etree.fromstring(document_xml)
        requirements = {
            "schema_version": 1,
            "tables": [
                {
                    "id": "table-1",
                    "role": "report associations",
                    "source": "display-source.csv",
                    "placement": "body",
                    "caption": "表1 关联结果",
                    "alignment": "left",
                    "references": [],
                    "columns": [
                        {"field_id": "term", "label": "变量", "source_field": "term", "column_index": 0},
                        {"field_id": "model_p", "label": "P 值", "source_field": "offline_p", "column_index": 1},
                        {"field_id": "model_p", "label": "P 值", "source_field": "overall_p", "column_index": 2},
                    ],
                    "reconciliation_evidence": "checks/table-1.json",
                }
            ],
            "figures": [],
        }

        findings = DOCX_AUDITOR.audit_delivery_requirements(
            parts, document, requirements
        )

        self.assertTrue(
            any(item["rule"] == "requirements.table_field_id" for item in findings)
        )


    def test_fit_to_exemplar_elements_over_defensive_completeness(self) -> None:
        # 回归：统计学方法写入“强制进入法”、异方差检验与 HC3 辩护句和节间回指，表注冗长；
        # 质性主题与联合展示却明显薄于范文；方法偏离期刊惯例；纠正后只改点名处并以附和开头。
        root_rules = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        principles = (ROOT / "skills/biostat-principles/SKILL.md").read_text(encoding="utf-8")
        contract = (
            ROOT / "skills/academic-publishing/references/manuscript-contract.md"
        ).read_text(encoding="utf-8")
        playbook = (
            ROOT / "skills/academic-publishing/references/section-content-playbook.md"
        ).read_text(encoding="utf-8")

        self.assertIn("成品以“适合”而非“无可指摘”为目标", root_rules)
        self.assertIn("同类成品写得充实的分析、阐释和整合也不能写薄", root_rules)
        self.assertIn("先找出导致错误的判断", root_rules)
        self.assertIn("答复不以“您说得对”、道歉或复述要求开头", root_rules)
        self.assertIn("主要分析默认采用研究领域和目标期刊同类研究的常规方法", principles)
        self.assertIn("`部件 | 范文要素与形式 | 当前研究对应内容", contract)
        self.assertIn("本稿有而范文没有的要素直接删除", contract)
        self.assertNotIn("因异方差改用稳健标准误", contract)
        self.assertNotIn("放表注、补充材料或不写", playbook)
        self.assertIn("新旧要求冲突时，在决定该行为的环节调整或重构并删去被取代的内容", root_rules)
        self.assertIn("以更广的科研视野检查设计、时间线、口径与结论是否自洽", root_rules)
        self.assertIn("段内句子数量与长短、句子的组成方式和常用词", contract)
        self.assertIn("不为效果采用刻意复杂的做法", contract)

if __name__ == "__main__":
    unittest.main()
