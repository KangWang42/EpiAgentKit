from __future__ import annotations

import importlib.util
import json
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
                producer="02_code/03_main.py",
                source="model_main.params",
                input="01_data/rawdata/cohort.csv",
                analysis_set="primary_complete_case",
                run_id="20260802T121500+0800_ab12cd34",
                consumers=["03_tables/Table2_main.xlsx"],
                label="暴露与结局的关联",
                est=1.45,
                ci_low=1.12,
                ci_high=1.87,
                p=0.004,
            )
            self.assertEqual(rendered, "1.45（95% CI：1.12，1.87），P = 0.004")
            self.assertEqual(helper.val(yaml_path, "exposure_hr"), rendered)
            helper.render_summary_md(yaml_path, md_path)
            self.assertIn("暴露与结局的关联", md_path.read_text(encoding="utf-8"))
            payload = helper.yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["meta"]["schema_version"], 2)
            provenance = payload["results"]["exposure_hr"]["provenance"]
            self.assertEqual(provenance["producer"], "02_code/03_main.py")
            self.assertEqual(provenance["analysis_set"], "primary_complete_case")
            self.assertNotIn("interp", payload["results"]["exposure_hr"])

            with self.assertRaisesRegex(ValueError, "missing result provenance"):
                helper.add_result(
                    base / "invalid.yaml",
                    "missing_source",
                    producer="",
                    source="",
                    analysis_set="",
                    run_id="",
                )

            legacy = base / "legacy.yaml"
            legacy.write_text(
                "meta:\n  schema_version: 1\nresults:\n  old:\n    rendered:\n"
                "      full: legacy result\n",
                encoding="utf-8",
            )
            self.assertEqual(helper.val(legacy, "old"), "legacy result")
            with self.assertRaisesRegex(ValueError, "read-only"):
                helper.add_result(
                    legacy,
                    "new",
                    producer="02_code/new.py",
                    source="fit.params",
                    input_hash="sha256:test",
                    analysis_set="primary",
                    run_id="run-1",
                    consumers="03_tables/Table1.xlsx",
                )

    def test_project_initializer_supports_r_and_python_without_default_git(self) -> None:
        script = ROOT / "skills/project-init/scripts/init_project.R"
        body = script.read_text(encoding="utf-8")
        self.assertIn('language = c("r", "python")', body)
        self.assertIn("git = FALSE", body)
        self.assertIn('find_skill_file("python-biostats", "scripts/emit_summary.py")', body)
        self.assertIn('profile = c("analysis", "paper", "consulting", "teaching", "oneoff")', body)
        self.assertIn('"09_backup/archive", "09_backup/workbench"', body)
        self.assertIn('"/09_backup/"', body)

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
                        f'init_project("r_demo", root="{root}", profile="analysis", language="r", git=FALSE)',
                        f'init_project("py_demo", root="{root}", profile="paper", language="python", git=FALSE)',
                        f'init_project("consult_demo", root="{root}", profile="consulting", language="r", git=FALSE)',
                        f'init_project("teaching_demo", root="{root}", profile="teaching", language="r", git=FALSE)',
                        f'init_project("oneoff_demo", root="{root}", profile="oneoff", language="r", git=FALSE)',
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
            self.assertTrue((r_project / "02_code/00_setup.R").is_file())
            self.assertFalse((r_project / "02_code/00_setup").exists())
            self.assertFalse((r_project / "02_code/config.R").exists())
            self.assertFalse((r_project / "02_code/conventions.R").exists())
            self.assertFalse((r_project / "02_code/utils.R").exists())
            self.assertTrue((r_project / "02_code/vendored/emit_summary.R").is_file())
            self.assertTrue((r_project / "r_demo.Rproj").is_file())
            self.assertTrue((py_project / "02_code/00_setup.py").is_file())
            self.assertFalse((py_project / "02_code/00_setup").exists())
            self.assertFalse((py_project / "02_code/config.py").exists())
            self.assertFalse((py_project / "02_code/conventions.py").exists())
            self.assertFalse((py_project / "02_code/utils.py").exists())
            self.assertTrue((py_project / "02_code/vendored/emit_summary.py").is_file())
            self.assertTrue((py_project / "02_code/01_data_cleaning.py").is_file())
            self.assertTrue((py_project / "paper").is_dir())
            self.assertTrue((Path(directory) / "consult_demo/05_reports").is_dir())
            self.assertFalse((r_project / "paper").exists())
            self.assertFalse((py_project / "py_demo.Rproj").exists())
            self.assertFalse((r_project / ".git").exists())
            self.assertFalse((py_project / ".git").exists())
            for project in (r_project, py_project):
                manifest = json.loads(
                    (project / ".epiagentkit-layout.json").read_text(encoding="utf-8")
                )
                self.assertEqual(manifest["schema_version"], 2)
                self.assertEqual(manifest["policy"], "directory-and-artifact-types")
                declared = {entry["path"] for entry in manifest["categories"]}
                self.assertTrue({"01_data", "02_code", "results", "09_backup"}.issubset(declared))
                self.assertTrue((project / "09_backup/archive").is_dir())
                self.assertTrue((project / "09_backup/workbench").is_dir())
                self.assertFalse((project / "09_backup/archive/.gitkeep").exists())
                self.assertFalse((project / "09_backup/workbench/.gitkeep").exists())
                self.assertIn(
                    "/09_backup/",
                    (project / ".gitignore").read_text(encoding="utf-8").splitlines(),
                )
                self.assertFalse((project / "results/results.yaml").exists())
                self.assertFalse((project / "SESSION_LOG.md").exists())
                self.assertFalse((project / "EXPERIMENTS.md").exists())
                checked = subprocess.run(
                    [
                        sys.executable,
                        str(ROOT / "hooks/final_project_check.py"),
                        str(project),
                        "--json",
                    ],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
                check_payload = json.loads(checked.stdout)
                self.assertFalse(
                    any(
                        item["check"].startswith("layout.")
                        for item in check_payload["findings"]
                    ),
                    check_payload["findings"],
                )
                self.assertFalse(
                    any(
                        item["check"] == "code.numbering_gap"
                        for item in check_payload["findings"]
                    ),
                    check_payload["findings"],
                )
            self.assertFalse((Path(directory) / "teaching_demo/.epiagentkit-layout.json").exists())
            self.assertFalse((Path(directory) / "oneoff_demo/09_backup").exists())

    def test_project_initializer_keeps_backup_out_of_git(self) -> None:
        rscript = shutil.which("Rscript")
        git = shutil.which("git")
        if rscript is None or git is None:
            self.skipTest("Rscript and Git are required for the Git ignore integration test")

        script = ROOT / "skills/project-init/scripts/init_project.R"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).as_posix()
            source = script.as_posix()
            test_script = Path(directory) / "test_backup_gitignore.R"
            test_script.write_text(
                "\n".join(
                    [
                        f'source("{source}", encoding="UTF-8")',
                        f'init_project("git_demo", root="{root}", profile="analysis", language="r", git=TRUE)',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            environment = dict(os.environ)
            environment["EPIAGENTKIT_SKILLS"] = str(ROOT / "skills")
            initialized = subprocess.run(
                [rscript, str(test_script)],
                cwd=ROOT,
                env=environment,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            self.assertEqual(
                initialized.returncode,
                0,
                initialized.stdout + initialized.stderr,
            )

            project = Path(directory) / "git_demo"
            archive_file = project / "09_backup/archive/old-report.docx"
            workbench_file = project / "09_backup/workbench/check/output.log"
            archive_file.write_text("archived\n", encoding="utf-8")
            workbench_file.parent.mkdir(parents=True)
            workbench_file.write_text("diagnostic\n", encoding="utf-8")

            for path in (archive_file, workbench_file):
                ignored = subprocess.run(
                    [git, "-C", str(project), "check-ignore", "-q", str(path)],
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(ignored.returncode, 0, path)

            status = subprocess.run(
                [git, "-C", str(project), "status", "--porcelain", "--untracked-files=all"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            self.assertEqual(status.returncode, 0, status.stdout + status.stderr)
            self.assertNotIn("09_backup", status.stdout.replace("\\", "/"))

    def test_global_writing_contract_and_r_first_default_are_preserved(self) -> None:
        rules = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        for fragment in (
            "研究者“我做了 X”的视角",
            "不使用助手口吻",
            "游戏化隐喻",
            "英文缩写首次出现给出全称",
            "流行病学与生物统计分析以 R 为主要语言",
            "用户未指定且项目没有既定分析语言时直接使用 R",
            "Python 不是标准研究工作流的前置条件",
            "先说明用途、安装范围和风险并询问是否安装",
            "经核验等价实现",
            "不要求迁移可工作的 R 主流程",
            "交付说明无套话",
            "使用临床研究、流行病学与生物统计的准确术语",
            "调用条件、检查要求、停止条件和是否需要单独运行",
            "没有稳定译名时保留原词",
            "禁止按英文词形逐字硬译",
            "不把软件设计或行政管理中的隐喻移植成科研术语",
        ):
            self.assertIn(fragment, rules)
        for inappropriate_term in ("\u95e8\u7981", "\u6273\u673a"):
            self.assertNotIn(inappropriate_term, rules)
        project_init = (ROOT / "skills/project-init/SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("默认使用 R", project_init)
        self.assertIn("只有用户明确选择或现有主流程为 Python", project_init)
        self.assertIn("选择能够完成当前任务的最小类型", project_init)

        r_skill = (ROOT / "skills/r-biostats/SKILL.md").read_text(encoding="utf-8")
        python_skill = (ROOT / "skills/python-biostats/SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("用户未指定且项目没有既定分析语言时也使用", r_skill)
        self.assertIn("普通 R 包缺失时", r_skill)
        self.assertIn("项目隔离环境补齐", r_skill)
        self.assertIn("仅用于用户明确要求 Python", python_skill)
        self.assertIn("未指定语言的普通统计分析", python_skill)
        self.assertIn("Python 运行时缺失时先询问是否安装", python_skill)
        self.assertIn("现有 R 环境中的经核验等价实现", python_skill)

    def test_shared_result_schema_separates_numbers_from_interpretation(self) -> None:
        schema = (
            ROOT / "skills/biostat-principles/references/result-summary-schema.md"
        ).read_text(encoding="utf-8")
        for fragment in (
            "schema_version: 2",
            "producer",
            "source",
            "input_hash",
            "analysis_set",
            "run_id",
            "consumers",
            'which="full"',
            "不保存解释、因果判断、显著性结论或跨结果总结",
            "旧版的 `raw` / `rendered` 字段",
        ):
            self.assertIn(fragment, schema)
        for removed in ("stale_interps", "confirm_interp", "set_conclusion"):
            self.assertNotIn(removed, schema)
        self.assertIn("面向研究者说明时写“结果使用位置”", schema)
        self.assertIn("不得把该字段译为“消费者”", schema)
        self.assertIn("原始数据或专业分类中确实表示人的 `consumer`", schema)
        report_helper = (
            ROOT / "skills/report-writing/references/build_report.py"
        ).read_text(encoding="utf-8")
        ppt_helper = (
            ROOT / "skills/sysu-ppt/scripts/sysu_toolkit.R"
        ).read_text(encoding="utf-8")
        self.assertIn('res.get("display")', report_helper)
        self.assertIn("item$display", ppt_helper)
        self.assertIn('legacy_names <- c(estimate = "est"', ppt_helper)

    def test_language_neutral_workflows_remain_coordinated(self) -> None:
        principles = (ROOT / "skills/biostat-principles/SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("R 多行代码写入脚本后用 `Rscript`", principles)
        self.assertIn("Python 使用项目现有且版本兼容的 Python", principles)

        publishing = (ROOT / "skills/academic-publishing/SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("第 2 版结构的 `results/results.yaml`", publishing)
        self.assertIn("已验证的正式表格、图件或统计输出", publishing)
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
        project_init = (ROOT / "skills/project-init/SKILL.md").read_text(
            encoding="utf-8"
        )
        figures = (ROOT / "skills/publication-figures/SKILL.md").read_text(
            encoding="utf-8"
        )
        report = (ROOT / "skills/report-writing/SKILL.md").read_text(
            encoding="utf-8"
        )
        for body in (publishing, project_init, figures):
            self.assertIn("全局 `CLAUDE.md`", body)
        self.assertNotIn("加载本 skill 不扩大范围", report)
        self.assertIn("references/project-hygiene.md", project_init)
        self.assertIn("references/chart-gallery.md", figures)

    def test_global_scope_contract_is_not_repeated_in_skills(self) -> None:
        repeated = []
        for skill_file in (ROOT / "skills").glob("*/SKILL.md"):
            if "加载本 skill 不扩大范围" in skill_file.read_text(encoding="utf-8"):
                repeated.append(skill_file.parent.name)
        self.assertEqual([], repeated)

    def test_publication_figures_has_correct_calibration_and_neutral_output(self) -> None:
        body = (ROOT / "skills/publication-figures/SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("slope < 1：预测通常过于极端", body)
        self.assertIn("slope > 1：预测分布过窄、不够极端", body)
        self.assertIn("无目标期刊时生成中性工作稿", body)
        self.assertIn("期刊当前官方说明", body)
        self.assertNotIn("slope > 1 表示预测过于极端", body)

    def test_delivery_preserves_true_provenance(self) -> None:
        body = (ROOT / "skills/consulting-delivery/SKILL.md").read_text(
            encoding="utf-8"
        )
        humanizer = (ROOT / "skills/academic-humanizer/SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "从主项目实际生成结果的分析脚本和最近一次成功运行的记录整理交付内容",
            body,
        )
        self.assertIn("不得只改外发包而不回写主项目", body)
        self.assertIn("执行其成品视角与真实披露边界", body)
        self.assertIn("期刊、机构、伦理、合同或法规明确要求的真实披露必须保留", humanizer)
        self.assertIn("没有明确数据分享授权时默认 `reference`", body)
        self.assertNotIn("`AI_assisted` → `研究者`", body)

    def test_r_delivery_pack_propagates_run_id_portably(self) -> None:
        rscript = shutil.which("Rscript")
        if rscript is None:
            self.skipTest("Rscript is unavailable")
        scaffold = ROOT / "skills/consulting-delivery/scripts/consulting_scaffold.R"
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            driver = base / "verify_delivery.R"
            driver.write_text(
                "\n".join(
                    [
                        f'source("{scaffold.as_posix()}", encoding="UTF-8")',
                        f'pack <- create_delivery_pack("r_reference", root="{base.as_posix()}", language="R", data_policy="reference")',
                        'writeLines(c("run_id <- Sys.getenv(\\\"EPI_RUN_ID\\\")", "stopifnot(nzchar(run_id))", "dir.create(\\\"outputs\\\", showWarnings = FALSE)", "writeLines(run_id, \\\"outputs/run_id.txt\\\")"), file.path(pack, "code/verify.R"), useBytes = TRUE)',
                        'writeLines("RUN_ORDER <- c(\\\"code/verify.R\\\")", file.path(pack, "code/run_order.R"), useBytes = TRUE)',
                        "verify_reproducibility(pack)",
                        'stopifnot(file.exists(file.path(pack, "outputs/run_id.txt")))',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            completed = subprocess.run(
                [rscript, "--vanilla", str(driver)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_r_project_pipeline_propagates_run_id_portably(self) -> None:
        rscript = shutil.which("Rscript")
        if rscript is None:
            self.skipTest("Rscript is unavailable")
        pipeline = ROOT / "skills/project-init/assets/run_pipeline.R"
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "02_code").mkdir()
            (project / "results/derived").mkdir(parents=True)
            shutil.copy2(pipeline, project / "run_pipeline.R")
            (project / "02_code/01_data_cleaning.R").write_text(
                "\n".join(
                    [
                        'run_id <- Sys.getenv("EPI_RUN_ID")',
                        "stopifnot(nzchar(run_id))",
                        'writeLines(run_id, "results/derived/run_id.txt")',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            completed = subprocess.run(
                [rscript, "--vanilla", "run_pipeline.R"],
                cwd=project,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            record = json.loads(
                (project / "results/runs/latest.json").read_text(encoding="utf-8")
            )
            recorded = (project / "results/derived/run_id.txt").read_text(
                encoding="utf-8"
            ).strip()
            self.assertEqual(record["status"], "success")
            self.assertEqual(recorded, record["run_id"])

    def test_audit_uses_design_specific_scientific_judgment(self) -> None:
        body = (ROOT / "skills/epi-project-audit/SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("| ERROR | 可能改变科学结论", body)
        self.assertIn("结构偏好一般是 WARN/INFO", body)
        self.assertIn("自动检查只是证据之一", body)
        self.assertNotIn("事件数 ≥ 10×协变量数", body)
        self.assertNotIn("Reviewer: Agent", body)

    def test_workflow_regressions_have_executable_boundaries(self) -> None:
        principles = (ROOT / "skills/biostat-principles/SKILL.md").read_text(
            encoding="utf-8"
        )
        audit = (
            ROOT / "skills/epi-project-audit/references/audit-checklist.md"
        ).read_text(encoding="utf-8")
        publishing = (ROOT / "skills/academic-publishing/SKILL.md").read_text(
            encoding="utf-8"
        )

        for fragment in (
            "改动—影响—验证对应关系",
            "从最早受影响步骤重跑",
            "不因检查脚本、状态说明、README、审计配置或文件格式变化重复重建",
            "不得直接改写历史运行记录",
        ):
            self.assertIn(fragment, principles)

        for fragment in (
            "逐项记录其实际输入、写出的正式产物或统计估计",
            "只读取既有产物并给出通过/失败结论",
            "生成脚本内与该产物直接相关的科学不变量检查可以保留",
            "不构成再次完整重跑的理由",
        ):
            self.assertIn(fragment, audit)

        for fragment in (
            "明确文件交付要求",
            "正文唯一来源格式",
            "实际交付文件清单",
            "不得默认推断为 Word",
            "实际交付文件与已确认的文件交付要求逐项一致",
        ):
            self.assertIn(fragment, publishing)
        self.assertIn("文件交付要求未选择 Word", publishing)

    def test_file_skills_do_not_force_unrequested_artifacts_or_edits(self) -> None:
        report = (ROOT / "skills/report-writing/SKILL.md").read_text(encoding="utf-8")
        pptx = (ROOT / "skills/pptx/SKILL.md").read_text(encoding="utf-8")
        xlsx = (ROOT / "skills/xlsx/SKILL.md").read_text(encoding="utf-8")
        docx = (ROOT / "skills/docx/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("只生成用户指定格式的文件，不擅自附加另一种格式", report)
        self.assertIn("用户只要正文时直接返回净稿，不创建文件", report)
        self.assertIn("without making a gratuitous edit", pptx)
        self.assertIn("Verified statistical result or archival export", xlsx)
        self.assertIn("neutral value `Reviewer`", docx)
        self.assertNotIn('Use "Claude" as the author', docx)

    def test_bounded_tasks_use_scope_proportionate_validation(self) -> None:
        academic_humanizer = (
            ROOT / "skills/academic-humanizer/SKILL.md"
        ).read_text(encoding="utf-8")
        docx = (ROOT / "skills/docx/SKILL.md").read_text(encoding="utf-8")
        docx_revision = (
            ROOT / "skills/docx/references/scoped-revision.md"
        ).read_text(encoding="utf-8")
        pptx = (ROOT / "skills/pptx/SKILL.md").read_text(encoding="utf-8")
        pptx_editing = (ROOT / "skills/pptx/editing.md").read_text(
            encoding="utf-8"
        )
        xlsx = (ROOT / "skills/xlsx/SKILL.md").read_text(encoding="utf-8")
        peer_review = (
            ROOT / "skills/manuscript-peer-review/SKILL.md"
        ).read_text(encoding="utf-8")
        study_design = (ROOT / "skills/epi-study-design/SKILL.md").read_text(
            encoding="utf-8"
        )
        ecg = (ROOT / "skills/python-ecg-analysis/SKILL.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("受影响页面的显示", academic_humanizer)
        self.assertIn(
            "Read `references/scoped-revision.md` completely", docx
        )
        self.assertIn("For an L revision", docx_revision)
        self.assertIn(
            "Inspect every page only for a newly created", docx_revision
        )

        self.assertIn("L bounded edit", pptx)
        self.assertIn("does not trigger template remapping", pptx)
        self.assertIn("zero observed issues is valid evidence", pptx)
        self.assertIn("For an L bounded edit", pptx_editing)
        self.assertIn("Do not run template selection", pptx_editing)
        self.assertNotIn(
            "If you found zero issues on first inspection, you weren't looking hard enough.",
            pptx,
        )

        self.assertIn("text-, comment- or format-only L edit", xlsx)
        self.assertIn("zero new unintended formula errors", xlsx)
        self.assertIn("L 局部审查", peer_review)
        self.assertIn("明确未审范围", peer_review)
        self.assertIn("Q：直接回答当前设计或方法问题", study_design)
        self.assertIn("L：只完成用户点名的", study_design)
        self.assertIn("Q 只读取回答当前问题", ecg)
        self.assertIn("L 读取项目规则、目标脚本/配置", ecg)
        self.assertIn("不为 L 重跑无关脚本", ecg)


if __name__ == "__main__":
    unittest.main()
