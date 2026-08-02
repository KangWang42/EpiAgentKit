#!/usr/bin/env python3
"""Audit cross-skill workflow contracts that are easy to regress."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import string
import subprocess
import sys
import tempfile
from pathlib import Path

from config_core import (
    LEGACY_HOOK_MANIFEST,
    LEGACY_INSTALL_MANIFEST,
    LEGACY_SKILL_MANIFEST,
    local_skill_excludes,
)
from sync_user_configs import (
    HOOK_DEFINITIONS,
    MANAGED_HOOK_SCRIPTS,
    REGISTERED_HOOK_SCRIPTS,
    SKILL_MANIFEST,
    hook_command,
    mirror_tree,
    sync_hook_config,
    sync_skills,
)


ROOT = Path(__file__).resolve().parents[1]
LINE_BUDGET = 200
RESEARCH_TERMINOLOGY = (
    "契约",
    "真源",
    "单源",
    "闭环",
    "路由",
    "签发",
    "声纹",
    "证据指针",
    "来源指针",
    "设计契约",
    "账本",
    "运行凭证",
    "稳定键",
    "历史配方",
    "官方机制",
    "兼容解释器",
    "多面板",
    "内容拓扑",
    "信息拓扑",
    "母图",
    "调用线",
    "锚点",
    "锚定",
    "治理与报告",
    "项目卫生",
    "发布前卫生",
    "当前项目映射",
    "来源章节映射",
    "主题映射",
    "闭合到",
)
RESEARCH_TEXT_SUFFIXES = {".md", ".py", ".R", ".json", ".txt"}
RESEARCH_TEXT_EXCLUDED_PREFIXES = (
    "skills/research-visuals/references/external/academic-figure-skill/",
    "skills/research-visuals/references/external/academic-figure-generator/",
)
RESEARCH_TERM_ALLOWLIST: dict[tuple[str, str], tuple[str, ...]] = {}


def configure_utf8_output() -> None:
    """Keep Windows diagnostics printable even when the active code page is GBK."""
    os.environ["PYTHONIOENCODING"] = "utf-8"
    os.environ["PYTHONUTF8"] = "1"
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="replace")


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def research_term_violations(relative: str, line: str) -> tuple[str, ...]:
    """Find high-confidence wording clues; contextual Chinese review remains required."""
    checked = line
    for term in RESEARCH_TERMINOLOGY:
        for allowed in RESEARCH_TERM_ALLOWLIST.get((relative, term), ()):
            checked = checked.replace(allowed, "")
    return tuple(term for term in RESEARCH_TERMINOLOGY if term in checked)


def research_text_files() -> list[Path]:
    candidates = [ROOT / name for name in ("CLAUDE.md", "AGENTS.md", "README.md")]
    docs = ROOT / "docs"
    if docs.exists():
        candidates.extend(
            path
            for path in docs.rglob("*")
            if path.is_file() and path.suffix in RESEARCH_TEXT_SUFFIXES
        )
    local_excludes = local_skill_excludes(ROOT)
    for skill_dir in (ROOT / "skills").iterdir():
        if not skill_dir.is_dir() or skill_dir.name in local_excludes:
            continue
        candidates.extend(
            path
            for path in skill_dir.rglob("*")
            if path.is_file() and path.suffix in RESEARCH_TEXT_SUFFIXES
        )
    return sorted(set(candidates))


def audit_research_terminology() -> list[str]:
    """Audit researcher-facing rules, skills, templates and helper messages."""
    findings: list[str] = []
    for path in research_text_files():
        relative = path.relative_to(ROOT).as_posix()
        if relative.startswith(RESEARCH_TEXT_EXCLUDED_PREFIXES):
            continue
        for line_number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            terms = research_term_violations(relative, line)
            if terms:
                findings.append(
                    f"{relative}:{line_number}: researcher-facing terminology uses "
                    + ", ".join(terms)
                )
    return findings


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def snapshot_tree(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file()
    }


def run_epiagentkit(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts/epiagentkit.py"), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def run_hook_script(
    script: Path,
    cwd: Path,
    payload: str = "{}",
    environment: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if environment:
        env.update(environment)
    if os.name == "nt":
        wrapper = ROOT / "hooks" / "run_hook.cmd"
        command: str | list[str] = (
            f'cmd.exe /d /s /c call "{wrapper}" "{script}" "claude"'
        )
    else:
        command = ["bash", str(script)]
        env["EPIAGENTKIT_HOOK_CLIENT"] = "claude"
    return subprocess.run(
        command,
        cwd=cwd,
        input=payload,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )


def main() -> int:
    problems: list[str] = []

    if "Stop" in HOOK_DEFINITIONS:
        problems.append(
            "default hook config must not auto-continue from Stop; support is not "
            "verified consistently across both clients"
        )

    for relative in ("CLAUDE.md", "AGENTS.md"):
        count = len(read(relative).splitlines())
        if count > LINE_BUDGET:
            problems.append(f"{relative}: {count} lines exceeds {LINE_BUDGET}")

    problems.extend(audit_research_terminology())

    validator = ROOT / "skills/skill-creator/scripts/quick_validate.py"
    skill_names = {
        item.name
        for item in (ROOT / "skills").iterdir()
        if item.is_dir() and (item / "SKILL.md").is_file()
    }
    for skill_dir in sorted((ROOT / "skills").iterdir()):
        if not skill_dir.is_dir() or not (skill_dir / "SKILL.md").exists():
            continue
        result = subprocess.run(
            [sys.executable, str(validator), str(skill_dir)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode:
            detail = (result.stdout + result.stderr).strip()
            problems.append(f"{skill_dir.name}: quick_validate failed: {detail}")

    evidence_tests = subprocess.run(
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            "skills/evidence-research/tests",
            "-p",
            "test_*.py",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if evidence_tests.returncode:
        problems.append(
            "evidence-research offline tests failed: "
            + (evidence_tests.stdout + evidence_tests.stderr).strip()
        )

    installer_tests = subprocess.run(
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            "scripts/tests",
            "-p",
            "test_*.py",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if installer_tests.returncode:
        problems.append(
            "installer conflict tests failed: "
            + (installer_tests.stdout + installer_tests.stderr).strip()
        )

    routing_path = ROOT / "scripts/skill_routing_cases.json"
    try:
        routing_contract = json.loads(routing_path.read_text(encoding="utf-8"))
        cases = routing_contract.get("cases", [])
        if "do not simulate model semantic routing" not in routing_contract.get("scope", ""):
            problems.append("routing cases must state their metadata-only validation scope")
        if not cases:
            problems.append("routing cases are empty")
        for case in cases:
            identity = case.get("id", "<missing>")
            routed = {
                case.get("primary"),
                *case.get("companions", []),
                *case.get("excluded", []),
            }
            unknown = {name for name in routed if name and name not in skill_names}
            if not case.get("prompt") or not case.get("primary"):
                problems.append(f"routing case {identity}: missing prompt or primary skill")
            if unknown:
                problems.append(
                    f"routing case {identity}: unknown skills: {', '.join(sorted(unknown))}"
                )
            expected = {case.get("primary"), *case.get("companions", [])}
            overlap = expected & set(case.get("excluded", []))
            if overlap:
                problems.append(
                    f"routing case {identity}: expected and excluded overlap: "
                    + ", ".join(sorted(overlap))
                )
        if not any(case.get("companions") for case in cases):
            problems.append("routing cases lack multi-skill composition examples")
        if not any(case.get("excluded") for case in cases):
            problems.append("routing cases lack negative examples")
    except (OSError, json.JSONDecodeError, TypeError) as error:
        problems.append(f"routing cases could not be validated: {error}")

    required = {
        ".gitattributes": (
            "academic-figure-skill/** binary",
            "academic-figure-generator/** binary",
        ),
        "CLAUDE.md": (
            "主流程 skill",
            "只负责载体操作，不取代内容主流程",
            "evidence-research",
            "非统计视觉先走 `research-visuals` → `imagegen`",
            "按载体、读者、证据属性、信息功能和实际显示尺寸设计",
            "真实界面、终端、文档与分析产物用实际渲染截图",
            "真实统计图走 `publication-figures`",
            "科研原始图像不得生成式重绘",
            "SVG 只按 `research-visuals` 与 `svg-diagrams` 的明确条件使用",
            "功能与读者匹配",
            "事实和数字准确",
            "层级清楚",
            "结构紧凑",
            "术语一致",
            "版式克制",
            "最终尺寸可读",
            "未指定风格时采用对应 skill 的中性默认",
            "不把条件细节复制回本文件",
            "同时承担执行与监测职责",
            "主动向用户报告",
            "停在安全点等待确认",
            "不静默修补后继续",
            "Git 只在命令可用且当前目录为仓库时使用",
            "不安装 Git，也不隐式初始化仓库",
            "只有用户在 `project-init` 中明确启用 Git 时",
            "只有用户当轮明确要求 push 时才推送",
            "唯一优先级",
            "凭证的完整内容",
            "轻量任务",
            "不自动初始化目录",
            "只回复，不创建项目文件",
            "局部产物",
            "不补建结果数据文件、修订记录文件或项目记录文件",
            "仅在 R 范围运行",
            "日常 P 任务只运行与改动风险相称的验证",
            ".epiagentkit-layout.json",
            "不自行安装或升级 R、Python",
            "普通 R/Python 分析包",
            "官方来源安装到项目隔离环境",
            "不改用户级、全局或 Codex/插件共享环境",
            "非官方来源安装前必须先征得用户同意",
            "不得静默改用非等价包、方法或分析语言",
            "研究者“我做了 X”的视角",
            "不使用助手口吻",
            "游戏化隐喻",
            "使用临床研究、流行病学与生物统计的准确术语",
            "调用条件、检查要求、停止条件和是否需要单独运行",
            "没有稳定译名时保留原词",
            "禁止按英文词形逐字硬译",
            "流行病学与生物统计分析以 R 为主要语言",
            "用户未指定且项目没有既定分析语言时直接使用 R",
            "Python 不是标准研究工作流的前置条件",
            "只读检查发现所需运行时缺失时",
            "普通 R/Python 分析包缺失时",
            "09_backup/workbench/",
            "点名处仅为同类问题样例",
            "扫描工作流",
            "不只修点名处",
            "保留合法用法",
        ),
        "AGENTS.md": (
            "Treat skill improvement as regression-safe optimization",
            "keep, rewrite, merge, move, script, or delete",
            "Prefer the smaller change when two designs pass the same evaluations",
            "Do not trade away existing behavior",
            "Use `epiagentkit-maintenance`",
            "do not initialize a repository or install Git",
            "09_backup/workbench/YYYY-MM-DD_HHMM_<topic>_<purpose>/",
            "Get-Content -Encoding utf8",
            "Treat mojibake as a failed read",
            "representative case",
            "Do not stop at a literal replacement or the named file",
        ),
        "skills/epiagentkit-maintenance/SKILL.md": (
            "观察到的缺口",
            "必须保留的行为",
            "最小变更集",
            "代表性验证",
            "每项规则只在一处维护",
            "CLAUDE.md",
            "AGENTS.md",
            "hooks",
            "不执行 `git init`",
            "不安装 Git",
            "sync --target all",
            "doctor --target all",
            "普通研究项目的数据分析、写作或项目初始化不触发本 skill",
            "用户无需重复声明",
            "09_backup/workbench/YYYY-MM-DD_HHMM_<主题>_maintenance/",
            "Get-Content -Encoding utf8",
            "同类问题边界",
            "中文修改按全局中文终审要求逐句检查",
        ),
        "skills/skill-creator/SKILL.md": (
            "Optimize, Don't Accumulate",
            "keep / rewrite / merge / move / script / delete",
            "prefer the smaller and easier-to-navigate version",
            "representative old and new evaluations",
            "remove superseded text in the same edit",
        ),
        "skills/skill-creator/scripts/quick_validate.py": (
            "Name cannot be empty",
            "Description cannot be empty",
            "disable-model-invocation",
            "SKILL.md body is too long",
            "Keep it under 500 lines",
        ),
        "skills/project-init/references/project-hygiene.md": (
            "只适用于 P 项目执行和 R 正式发布",
            "`categories`",
            "`artifact_classes`",
            "同一类文件不逐项登记",
            "旧项目逐文件登记的第 1 版格式仍可读取",
            "09_backup/archive/YYYY-MM-DD_HHMM_<主题>_<阶段>/",
            "只索引 `archive/`，不登记 workbench",
            "09_backup/workbench/YYYY-MM-DD_HHMM_<主题>_<用途>/",
            "E0：通常不建批次",
            "E1：一个批次保存 `PLAN.md` 和 `FINDINGS.md`",
            "E2：在 E1 基础上使用项目 `EXPERIMENTS.md`",
            "TEMP、TMP、TMPDIR",
            "不建立人工 `SESSION_LOG.md`",
            "不单独阻止发布",
        ),
        "skills/biostat-principles/references/result-summary-schema.md": (
            "meta:",
            "schema_version: 2",
            "每项结果使用固定英文名称",
            "`producer` 填写实际生成或导入该结果的脚本",
            "`source` 填写脚本中提取结果的对象、查询",
            "`consumers` 只列出实际读取这项结果的文件",
            "不保存解释、因果判断、显著性结论或跨结果总结",
            "render_summary_md()",
            "旧版的 `raw` / `rendered` 字段",
        ),
        "skills/biostat-principles/references/runtime-dependencies.md": (
            "只有普通分析包进入自动安装",
            "不得写入用户级、系统级、全局 site-library",
            "不为追求最新版升级无关包",
            "安装失败时，停下并报告",
            "未经同意不得改用功能相近的包",
        ),
        "skills/evidence-research/SKILL.md": (
            "Rapid verification",
            "Formal evidence review",
            "跨领域可迁移性",
            "无法取得全文或无法核对关键结论时标记“未核验”",
            "文献只能说明合理范围或核查方向",
            "scripts/verify_sources.py",
        ),
        "skills/evidence-research/references/source-routing.md": (
            "搜索结果片段",
            "PubMed CommentsCorrections",
            "Crossref relation",
            "注册平台",
        ),
        "skills/evidence-research/references/evidence-matrix.md": (
            "evidence_id",
            "来源标识",
            "核验状态",
            "当前项目适用性",
        ),
        "skills/evidence-research/scripts/verify_sources.py": (
            '"metadata_verified"',
            '"full_text_status"',
            '"claim_verified"',
            '"retrieved_at"',
            'checks["query_identity"]',
            "PubMed E-utilities and Crossref",
        ),
        "skills/evidence-research/tests/test_verify_sources.py": (
            "FakeTransport",
            "test_network_failure_is_explicit",
            "test_single_source_title_must_match_the_query",
            "test_title_conflict_remains_unverified",
        ),
        "skills/manuscript-peer-review/SKILL.md": (
            "期刊保密投稿",
            "reporting gap",
            "没有原始数据时不得写",
            "ethics/editor-only",
            "references/report-template.md",
        ),
        "skills/manuscript-peer-review/references/review-criteria.md": (
            "样本和分母",
            "研究设计与偏倚",
            "统计方法",
            "语言、结构与参考文献",
        ),
        "skills/manuscript-peer-review/references/report-template.md": (
            "Major comments",
            "Coverage matrix",
            "Reviewer limitations and disclosures",
        ),
        "skills/project-init/scripts/init_project.R": (
            '"PROTOCOL.md"',
            '"SAP.md"',
            '"09_backup/archive"',
            '"09_backup/workbench"',
            '"02_code/config.R"',
            '"02_code/conventions.R"',
            '"02_code/vendored"',
            '".epiagentkit-raw-roots"',
            '"results/runs"',
            '"result_data_file"',
            '"run_record"',
            '"directory-and-artifact-types"',
            'Sys.which("git")',
            'git_state <- "unavailable"',
            "Git：",
        ),
        "skills/r-biostats/SKILL.md": (
            "scripts/emit_summary.R",
            "PROTOCOL",
            "SAP",
            "不因加载本 skill 自动创建正式项目目录或额外记录文件",
            "普通 R 包缺失时",
            "项目隔离环境补齐",
            "失败不得静默换包、换方法或改用 Python",
            "用户未指定且项目没有既定分析语言时也使用",
            "run_pipeline.R",
            "Rscript --vanilla",
            "局部任务只交付已经确认的产物",
        ),
        "skills/python-biostats/SKILL.md": (
            "仅用于用户明确要求 Python",
            "既有项目已经以 Python 为主流程",
            "未指定语言的普通统计分析",
            "R 环境或依赖缺失",
            "普通 Python 包缺失时",
            "项目隔离环境补齐",
            "Python 运行时缺失时先询问是否安装",
            "现有 R 环境中的经核验等价实现",
            "run_pipeline.py",
        ),
        "skills/biostat-principles/SKILL.md": (
            "09_backup/workbench/<YYYY-MM-DD_HHMM>_<主题>_experiment/",
            "PLAN.md",
            "FINDINGS.md",
            "规则冲突只使用全局",
            "轻量任务",
            "不扩大任务范围",
            "执行者也是监测者",
            "报告发生了什么、证据位置、影响、已做检查和待决定事项",
            "R 多行代码写入脚本后用 `Rscript`",
            "Python 使用项目现有且版本兼容的 Python",
            "新的非交互进程实跑",
            "E0 快速核验",
            "E1 决策实验",
            "E2 正式比较",
            "不创建或补写 `SESSION_LOG.md`",
        ),
        "skills/consulting-delivery/SKILL.md": (
            "R 或 Python 分析",
            "DELIVERY_CONTENTS.md",
            "run_pipeline.R|py",
            "run_records/",
            "没有明确数据分享授权时默认 `reference`",
            "只有 `data_policy=\"include\"` 且提供 `data_authority` 时才创建 `data/`",
            "从主项目实际生成结果的分析脚本和最近一次成功运行的记录整理交付内容",
            "此阶段不现场安装或升级依赖",
            "法规、合同、伦理或机构明确要求的真实披露必须保留",
            "结构偏好、文件是否编号或报告长短本身不阻止发布",
        ),
        "skills/consulting-delivery/scripts/consulting_scaffold.R": (
            'subdirs <- c("code", "outputs", "run_records"',
            "RUN_ORDER <- character()",
            'language = c("R", "python")',
            'file.path(pack, "run_pipeline.py")',
            'file.path(pack, "DELIVERY_CONTENTS.md")',
            "data_policy='include' 必须提供 data_authority",
            "使用 `DELIVERY_CONTENTS.md` 中注明的 R 或 Python 版本及依赖",
            "run_records",
        ),
        "scripts/sync_user_configs.py": (
            "def atomic_copy_file(",
            "def mirror_tree(",
            "def sync_hook_config(",
            'hooks_dir / "run_hook.cmd"',
            "mirror_tree(skill, destination)",
            "include: set[str] | None",
            "prune_stale: bool = True",
            "def update_install_manifest(",
            "scan_skill_conflicts(",
            "remove_skill_conflicts(",
            "remove_tree(resolved)",
            'LEGACY_SKILL_ALIASES = {"image-diagrams": "research-visuals"}',
            "effective_excludes = exclude | SYNC_EXCLUDES | local_skill_excludes(root)",
            "Local-only skills are not distributable",
        ),
        "scripts/skill_conflicts.py": (
            "CONFLICT_DOMAINS",
            'kind="semantic_overlap"',
            '"skill-conflict-reports"',
            "shutil.rmtree",
            "matched_terms",
            "def remove_tree(",
            "deferred_empty_directory",
            '"research-visuals"',
            '"academic diagram prompt"',
        ),
        "scripts/config_core.py": (
            'PROJECT_NAME = "EpiAgentKit"',
            'INSTALL_MANIFEST = ".epiagentkit-install.json"',
            "def resolve_codex_skill_dirs(",
            'layout == "both"',
            "Installation-time bundle closure only",
            '"evidence-research"',
            '"manuscript-peer-review"',
            '"research-visuals"',
            '"project-init": {',
            '"epi-study-design"',
            '"python-biostats"',
            '"epiagentkit-maintenance": {"skill-creator"}',
            'LOCAL_SKILL_EXCLUDES_FILE = ".epiagentkit-local-skills"',
            'SYNC_EXCLUDES = {"python-ecg-analysis"}',
            "def local_skill_excludes(root: Path)",
            "item.name not in excludes",
        ),
        "scripts/skill_routing_cases.json": (
            "readme_content_diagram",
            "readme_real_artifact_screenshot",
            "template_adaptive_presentation",
            "maintain_epiagentkit_contracts",
            "r_dependency_missing_no_language_switch",
            "journal_manuscript_peer_review",
            "manuscript_only_data_boundary",
        ),
        "skills/project-init/SKILL.md": (
            "已有项目分析不触发",
            "简单作业、快速核验",
            "选择能够完成当前任务的最小类型",
            "不预建空模块",
            "默认使用 R",
            "Git 已存在时初始化",
            "不安装 Git",
            "不创建空的 `results/results.yaml`",
            "不创建 `SESSION_LOG.md`",
            "所选项目类型之外的目录和占位文件未创建",
        ),
        "skills/academic-publishing/SKILL.md": (
            "已有文本的局部润色或压缩只用 academic-humanizer",
            "单部件或局部产物",
            "不创建修订记录文件、章节目录或项目记录文件",
            "用户明确要求时可一次生成完整稿",
            "不得因通用流程强制拆成多轮审批",
            "不因期刊未定阻断写作",
            "审稿回复逐条直接回答审稿人提出的问题",
        ),
        "skills/academic-humanizer/references/revision-workflow.md": (
            "单个引用序号",
            "不创建修订记录文件或项目记录文件",
            "不要只为保存这些要求而创建 JSON",
            "interaction_contract",
            "净稿、标注稿和回复需要由同一组修改记录生成",
        ),
        "skills/academic-humanizer/references/patterns-and-preservation.md": (
            "章节功能控制",
            "| 方法 |",
            "| 结果 |",
            "| 讨论 |",
            "| 局限 |",
            "| 结论 |",
        ),
        "skills/academic-publishing/references/chinese-thesis.md": (
            "新项目统一从 `results/results.yaml` 读取数字",
            "旧项目可读取 `07_paper/results.yaml`",
            "自动生成的文字摘要只用于核对",
        ),
        "skills/docx/SKILL.md": (
            "only when a Word file is an input or deliverable",
            "Do not use for prose-only requests",
            "report the missing prerequisite without installing it",
            "Neutral Default Formatting",
            "Keep every table cell white by default",
            "preserve its existing styles and layout",
            "w14:paraId",
            "--allow-insert-after",
            "single local DOCX change does not require",
        ),
        "skills/pptx/SKILL.md": (
            "only when a presentation file is an input or deliverable",
            "Do not trigger for discussion of a talk without file work",
            "If any item is unavailable, explain the missing prerequisite",
            "do not install or upgrade it",
        ),
        "skills/pptx/pptxgenjs.md": (
            "Prerequisites:",
            "explain the user's next setup step",
            "do not install it",
        ),
        "skills/pdf/SKILL.md": (
            "Requires pytesseract and pdf2image",
            "If missing, explain the user's next setup step",
            "do not install them",
        ),
        "skills/report-writing/SKILL.md": (
            "用户只要正文时直接返回净稿",
            "只要正文时不调用 docx",
            "L：单段、单节、备忘或一个指定文件",
            "先完整回答读者最关心的问题",
            "短报告可以简洁，但不能省略理解结论所必需的内容",
            "正式成品不出现助手口吻、生成过程、主动工具归因",
            "L 范围外差异为零",
        ),
        "skills/python-ecg-analysis/SKILL.md": (
            "只有确认 `--help` 会在业务逻辑前退出且不会写文件时",
            "无法确认某个程序在显示帮助信息前不会写文件时，不执行该命令",
            "上游依赖：开工前对齐 biostat-principles",
        ),
        "skills/publication-figures/SKILL.md": (
            "发表级统计图、数据图",
            "流程、机制、架构、技术路线与图形摘要转 `research-visuals`",
            "只修改一张指定的图或一个格式问题",
            "修改已有图时，先确认允许改变的数值、术语、标签、精度、注释或格式项",
            "其余布局、图形元素和视觉表达保持不变",
            "用户明确对样式不满",
            "再进行重新设计",
            "不把白色背景当作通用投稿要求",
            "由多个子图组成时，只保留具有独立信息作用的子图",
            "绘图示例代码和说明资料尚未完成来源",
            "不得把它们作为方法或样式依据",
            "普通包缺失按依赖分流",
            "用户不安装时优先验证现有 R 环境中的等价实现",
        ),
        "scripts/configure_user.py": (
            "CODEX_COMPATIBILITY_WARNING,",
            '"doctor"',
            '"--skip-doctor"',
            "只安装 EpiAgentKit 文件",
            "不安装或升级 R、Python 及其它运行环境或依赖",
        ),
        "scripts/epiagentkit.py": (
            "def tree_matches(",
            "def run_doctor(",
            "def run_check_project(",
            'command == "install"',
            'command == "sync"',
            'command == "check-project"',
        ),
        "scripts/epiclaude.py": ("from epiagentkit import main",),
        "hooks/_emit_notice.py": (
            '"hookEventName": "PostToolUse"',
            '"additionalContext": message',
            '"systemMessage": message',
        ),
        "hooks/protect_rawdata.sh": (
            "_path_guard.py",
            "不解析任意 shell/Python/PowerShell 代码",
        ),
        "hooks/scan_ai_trace.sh": (
            "_scan_text.py",
            "科研符号 → ↔ ↑ ↓ ± × ≥ ≤ ℃ 允许",
        ),
        "hooks/fig_selfcheck.sh": (
            "_file_state.py",
            "--kind figures",
            "当前平台的视觉检查工具",
            '_emit_notice.py"',
        ),
        "hooks/check_results_rds.sh": (
            "_file_state.py",
            "--kind results_rds",
            '_emit_notice.py"',
        ),
        "hooks/_file_state.py": (
            "project_key = hashlib.sha256",
            "old.get(\"size\") == stat.st_size",
            "if not baseline and old_fingerprint != fingerprint",
        ),
        "hooks/final_project_check.py": (
            "DEFAULT_CONTRACT",
            "project.not_directory",
            "rawdata.worktree_modified",
            "numbering_gap",
            "provenance.hash_mismatch",
            "provenance.run_not_successful",
            "provenance.run_status_missing",
            "results.source_mtime_older_than_outputs",
            "logs.abnormal_term",
            "secrets.high_entropy",
            "benign_named_credential",
            "os.walk(project, topdown=True",
            'workbench = (backup / "workbench").resolve(strict=False)',
            '"directory-and-artifact-types"',
            '"category-contract"',
        ),
        "skills/epi-project-audit/SKILL.md": (
            "scripts/run_check_project.py",
            "日常检查",
            "正式发布检查",
            "每层都继续审查，不因前层失败而停止",
            "ERROR",
            "阻止正式发布",
            "根目录文件数量、脚本是否连续编号",
            "实际生成结果的脚本",
            "实际使用该结果的文件",
            "自动文本匹配只能发现可能的差异",
            "不得用 `interp_review` 或人工清除标记代替作者判断",
            "单个 Word、表格、图片、PDF 或一段文字",
            "只审查模式严格只读",
            "有明确限制地通过",
            "每个问题应记录",
        ),
        "skills/epi-project-audit/references/audit-checklist.md": (
            "`results/results.yaml`",
            "`result_summaries.md` 如存在",
            "明确标注不可编辑",
            "`run_id` 对应一次成功的自动运行记录",
        ),
        "skills/epi-project-audit/scripts/run_check_project.py": (
            "def source_from_manifest(",
            "def resolve_cli(",
            'home / ".codex" / INSTALL_MANIFEST',
            'home / ".claude" / INSTALL_MANIFEST',
            '"check-project"',
            "subprocess.run(command, check=False)",
        ),
        "hooks/post_edit_checks.sh": (
            'run_check "check_r_syntax.sh"',
            'run_check "scan_ai_trace.sh"',
        ),
        "hooks/post_bash_checks.sh": (
            'collect_notice "fig_selfcheck.sh"',
            'collect_notice "check_results_rds.sh"',
            '_emit_notice.py"',
        ),
        "skills/svg-diagrams/SKILL.md": (
            "改用 SVG 的条件",
            "当前可见 skills 清单没有 `research-visuals`",
            "HTTP 524 按 `research-visuals` 保留原图并停止",
            "连续两次 HTTP 524",
            "已经提供有用参考图但尚未尝试",
            "对待修改原图完成必要的定向修改、使用已经提供且确有帮助的可选参考图",
            "序号与标题第一行垂直居中对齐",
            "包含关系图",
            "SVG XML 有效",
            "README 与技术文档",
            "模板必须保留的比例、品牌、字体、色彩、安全区",
            "改用 SVG 的具体原因",
        ),
        "skills/research-visuals/SKILL.md": (
            "Codex 使用当前会话提供的内置 `imagegen` 技能和 `image_gen` 工具",
            "PPT、论文、标书、报告或网页章节",
            "README、技术文档、项目主页、教程、skill 示例",
            "网页 hero、登录页和章节氛围图",
            "证据型原始图像",
            "写图件要求",
            "按原始尺寸和最终显示尺寸检查",
            "根据原图定向修改",
            "最多连续修改两轮",
            "不降质要求",
            "事实与语义忠实度",
            "必须保持的文字、数字、公式",
            "可以调整的版式、间距",
            "不得添加、删除、纠正、推断或合并的内容",
            "可选参考图",
            "不存在有用参考图时直接省略",
            "SVG 仅在明确要求矢量图、当前没有可用图像生成工具",
            "不计入两轮内容修改",
            "科研感必须来自真实主题和关系",
            "网页、README 和技术文档图片已检查窄屏显示",
            "不得用 Python、PPT 文本框、Word 文本框或 SVG 覆盖层",
            "触发本技能不等于每页都要生成图片",
            "research-figure-patterns.md",
            "figure-planning.md",
            "references/external/SOURCE.md",
            "制定图件计划",
            "逐项写明每张候选图的来源、独立作用和采用理由",
            "所有需要附带的图片均有本地路径时使用 `referenced_image_paths`",
            "最小 `num_last_images_to_include`",
            "diagram-iconography.md",
            "不得从中推断正式图号",
            "项目专属的正式图号",
            "references/scenario-playbook.md",
            "正文内容图/真实截图/氛围插图",
            "真实界面与成果截图",
            "模板迫使流程变成卡片墙",
            "不得把“网页图默认无字”泛化到正文内容图",
            "删除后会造成对象、关系、条件、关键状态或核心结论误读",
            "不得给每个节点机械添加副标题",
            "根据实际来源材料核对对象名称、关系、数字和结论",
            "目标宽高比来自实际图位而非参考图",
            "中文字形、圆形和方形保持自然比例",
        ),
        "skills/research-visuals/references/figure-planning.md": (
            "图件计划表",
            "图前说明",
            "参考图解构与编辑目标",
            "根据原图修改的要求",
            "| 待修改原图 |",
            "第一次 HTTP 524",
            "四轮终检",
            "TingxiYu/academic-figure-skill",
            "LigphiDonk/academic-figure-generator",
            "不按章节机械配图",
            "不预先指定一个占据最大面积的主要子图",
            "external/SOURCE.md",
            "未引入原项目的执行脚本、示例图片或第三方 API 配置",
            "不可替代的用户原图不得重新生成后冒充原图修改",
            "确定载体中的待修改图件",
            "图在载体中的位置",
            "项目专属事实只进入本次任务记录",
            "信息与文字作用",
            "模板适配",
            "真实 UI、终端、代码、文档和成果示例",
            "删除测试",
            "由多个子图组成的图件",
        ),
        "skills/research-visuals/references/external/SOURCE.md": (
            "只读上游快照",
            "主 `SKILL.md` 始终优先",
            "1df9940dd01ac939f072b12fe28d6353b79b90f9",
            "0a2bec6bb56d6b47143a81909f8d818716bdcbab",
            "f67fab86c84069368988cf49b699b901758bc04dbc98a69d22fd62ee3e3692c6",
            "6d84103d20c43dbf46c97f0aea99867bd7675599885901390860da35a9033e47",
            "不执行固定配色确认",
            "附带全部且仅必要的待修改图片",
        ),
        "skills/research-visuals/references/external/academic-figure-skill/figure-contract.md": (
            "The Five-Point Contract",
        ),
        "skills/research-visuals/references/external/academic-figure-skill/multipanel-layout.md": (
            "Anti-Redundancy",
        ),
        "skills/research-visuals/references/external/academic-figure-skill/LICENSE": (
            "Apache License",
        ),
        "skills/research-visuals/references/external/academic-figure-generator/academic-figure-prompt-upstream.md": (
            "Academic Figure Prompt",
        ),
        "skills/research-visuals/references/external/academic-figure-generator/LICENSE": (
            "MIT License",
        ),
        "skills/research-visuals/references/visual-strategy.md": (
            "从信息功能出发",
            "先判定信息角色与文字",
            "模板服从内容",
            "正文内容图",
            "真实截图",
            "系列一致性",
            "生成式痕迹审查",
            "https://platform.openai.com/docs/guides/image-generation",
            "https://www.w3.org/WAI/tutorials/images/",
        ),
        "skills/research-visuals/references/carrier-specs.md": (
            "PPT",
            "技术路线占标题以下 70%–90%",
            "diagram-iconography.md",
            "论文与图形摘要",
            "基金标书",
            "网页",
            "响应式图片资源",
            "README 与技术文档",
            "Skill 示例至少回答",
            "实际运行或渲染结果",
            "宽于 16:9 的比例必须有真实横幅或整行图位依据",
            "禁止非等比缩放",
        ),
        "skills/research-visuals/references/prompt-recipes.md": (
            "通用图件要求",
            "PPT 主视觉或章节配图",
            "标书立项、创新或影响配图",
            "网页 hero 或登录侧栏",
            "最多连续修改两轮",
            "Question-method pairs",
            "Source material",
            "Type-specific constraints",
            "不设固定字数",
            "external/SOURCE.md",
            "Edit the attached target image",
            "每个最终提示词只保留三条永久约束",
            "相同约束只出现一次",
            "图类专属质量指标",
            "Use the attached target image to verify the edit",
            "Optional reference image: use only when it has already been provided",
            "已经提供且确有帮助的参考图应在改用 SVG 前尝试",
            "Use case: high-fidelity scientific-figure edit",
            "Structure inventory",
            "merges or branches",
            "ambiguous source text must be copied, never guessed",
            "100% critical-text accuracy",
            "100% node and edge preservation",
            "First HTTP 524",
            "Second HTTP 524",
            "do not silently downgrade the model or switch to SVG/API",
            "人物或临床场景",
            "网页视觉",
            "科学教育插图",
            "封面与章节图",
            "Target identity:",
            "Confirmed edit target:",
            "Instance-only facts:",
            "Carrier-managed text:",
            "README 或技术文档正文内容图",
            "真实截图与成果预览",
            "Template requirements:",
            "Text selection:",
            "do not give every node a subtitle",
            "textless decorative illustration",
            "Geometry and typography:",
            "regular-width CJK typography",
            "canvas aspect ratio",
        ),
        "skills/research-visuals/references/scenario-playbook.md": (
            "六项场景判定",
            "正文内容图",
            "真实截图",
            "氛围插图",
            "场景选择矩阵",
            "模板适配要求",
            "根据信息关系确定表现形式",
            "Skill 功能示例",
            "实际生成并渲染后截图",
            "不要把所有示例都做成同构卡片",
            "逐条删除测试",
            "4–12 字",
            "本地操作性启发式",
            "W3C WAI Complex Images",
            "文字选择先于排版，但晚于内容核验",
            "evidence-research",
            "Ten Simple Rules for Designing Graphical Abstracts",
        ),
        "skills/research-visuals/references/diagram-iconography.md": (
            "W3C G207",
            "Microsoft Fluent 2 Iconography",
            "IBM Pictogram Usage",
            "GOV.UK Design System",
            "全图最多 4 个",
            "通常 2–4 个，不逐节点配图",
            "全图 0–3 个",
            "本地操作性启发式",
            "必要图标与相邻背景至少 3:1",
        ),
        "skills/research-visuals/references/research-figure-patterns.md": (
            "好的科研图回答一个问题",
            "先判定证据属性",
            "概念框架",
            "机制示意",
            "研究设计与数据流",
            "研究对象/数据源 → 采集与整合",
            "研究问题与对应方法",
            "连续讲解复杂方法时复用同一总体图",
            "禁止图库水印、低清截图、缺图占位符",
            "组合图已逐对检查重复",
            "与真实输入、变换或输出对应",
            "diagram-iconography.md",
            "5–7 个阶段通常只保留 2–4 个",
            "单行出现 6 个及以上有字节点",
            "横向容量已按最长标签自然字宽核对",
        ),
        "skills/sysu-ppt/SKILL.md": (
            "不要把“每页有图”当目标",
            "research-figure-patterns.md",
            "技术路线至少按项目实际覆盖",
            "总体技术路线占标题以下正文区 70%–90%",
            "封面主视觉、纯背景图和章节氛围图不编号",
            "模板适配（两类通用）",
            "不得为套用模板牺牲科学表达与可读性",
            "正文内容图直接包含理解所需的标签与关系",
            "默认模板的标题横线与左侧两块绿色矩形底边共线",
            ".TPL_REG[[...]]$header",
            "不能让两套模板共享同一纵向坐标",
            "一页一条主信息",
            "任意连续 4 张实质内容页至少使用 2 种主构图",
            "slide-design-practice.md",
            "纯装饰图、剪贴画、无语义图标",
            "页数服从内容",
            "不得为了靠近参考规模补页",
            "补真实内容 → 与相邻页合并 → 改段落/双栏/表格/主视觉/卡片",
            "正文 16pt 只作为信息密集页的下限",
            "单行 3 卡通常占正文区约 35%–50%",
            "近白绿灰底 `#F7FAF8`",
        ),
        "skills/sysu-ppt/references/slide-design-practice.md": (
            "主信息 + 最强证据或结构 + 必要解释或边界",
            "左右图文换边不算新的信息结构",
            "正文与背景对比度至少 4.5:1",
            "Harvard Catalyst: Slides",
            "Harvard T.H. Chan School of Public Health",
            "MIT NSE Communication Lab",
            "UC San Diego",
            "不能用来补页",
            "上方几行字、下方整片空白",
            "80%–90% 的白色或近白中性区域",
        ),
        "skills/sysu-ppt/references/deck_skeleton.R": (
            '"1.3 关键证据与现存缺口"',
            '"3.3 适用条件与失效情形"',
            '"4.2 核心结论与实践含义"',
            "页数不是要求",
        ),
        "skills/sysu-ppt/references/defense_blueprint.R": (
            "页数由用户要求、答辩时长、研究设计和证据量决定",
            "不是固定逐页清单",
            "仅在本任务需要章节分隔页时保留",
        ),
        "skills/academic-publishing/references/submission-materials.md": (
            "built via `research-visuals`",
            "target-journal dimensions",
        ),
        "skills/report-writing/references/build_report.py": (
            "白底黑字三线表",
            "保持白底，不加色块",
            'res.get("display")',
        ),
        "skills/xlsx/SKILL.md": (
            "Neutral Default Formatting",
            "Do not automatically add dark header bands",
            "Default to white cells with black text and light borders",
            "Use `scripts/recalc.py` only when a compatible LibreOffice installation is already available",
            "If `soffice` is unavailable",
            "do not install it",
        ),
        "skills/epi-project-audit/scripts/check_consistency.py": (
            "请先选择要使用的 Python 环境和安装方式",
            "本检查器不会自动安装或升级依赖",
        ),
        "README.md": (
            "从一句话到真实产物",
            "固定合成数据",
            "项目能做到什么",
            "工作流怎样随任务变化",
            "30 秒安装",
            "安全边界",
            "`research-visuals`",
            "论文、PPT、标书、报告、README 和技术文档",
            "制作发表级统计图",
            "写论文与投稿材料",
            "全项目质量审查",
            "epiagentkit-maintenance",
            "不会初始化仓库或安装 Git",
            "TingxiYu/academic-figure-skill",
            "LigphiDonk/academic-figure-generator",
            "external/SOURCE.md",
            "没有引入其正式运行脚本、示例图片或第三方 API 配置",
            "docs/assets/epiagentkit-hero.webp",
            "docs/assets/platform-architecture.webp",
            "docs/demo/output/forest-plot.png",
            "docs/demo/output/forest-plot-mobile.png",
            "docs/demo/output/forest-plot.pdf",
            "docs/demo/generate_forest_demo.R",
            "docs/demo/forest-demo-data.csv",
        ),
        "skills/git-commit-helper/SKILL.md": (
            "create the commit automatically",
            "Git is already available",
            "Do not install Git",
            "do not run `git init`",
            "Push only when the user explicitly requests push in the current turn",
            "otherwise stop after commit without prompting about push",
        ),
        "skills/sysu-ppt/scripts/sysu_toolkit.R": (
            "item$display",
            'legacy_names <- c(estimate = "est"',
            'default = list(file = "template.pptx"',
            'public_health = list(file = "template-公卫学院.pptx"',
            "anchor_bottom = 0.8101",
            "top = 0.2351",
            "top = 0.7701",
            "anchor_bottom = 1.0749",
            "top = 1.0349",
            ".validate_header <- function(header)",
            ".header_location <- function(part)",
            'assign("header",      reg$header,      .ACT)',
            ".code_ft <- function(code_lines, width, height)",
            '.CARD_BG   <- "#F7FAF8"',
            "code_w <- min(11.60",
            ".svg_aspect <- function(path)",
            ".validate_meeting_deck <- function(ppt)",
            'genre = c("meeting", "formal")',
            "组会 PPT 禁止目录页",
            "组会 PPT 禁止章节分隔/过渡页",
            "on.exit(unlink(td, recursive = TRUE, force = TRUE), add = TRUE)",
        ),
    }
    for relative, fragments in required.items():
        body = read(relative)
        for fragment in fragments:
            if fragment not in body:
                problems.append(f"{relative}: missing workflow contract {fragment!r}")

    forbidden = {
        "AGENTS.md": ("commit and normally push",),
        "CLAUDE.md": (
            "提交并正常推送",
            "<EpiAgentKit仓库>/scripts/epiagentkit.py check-project",
            "\u95e8\u7981",
            "\u6273\u673a",
            "Skill 优化不是只增不减",
            "epiagentkit-maintenance",
            "sync --target all",
            "doctor --target all",
            "一次性隔离子代理",
            "data URL",
            "base64",
            "修改会话 JSONL",
        ),
        "README.md": (
            '审查只看代码即可通过',
        ),
        "skills/project-init/references/project-hygiene.md": (
            "<EpiAgentKit仓库>/scripts/epiagentkit.py check-project",
        ),
        "skills/research-visuals/SKILL.md": (
            "优先生成无文字视觉层",
            "加确定性文字覆盖",
            "minimum 500 words",
            "User Confirms",
            "Copy the ENTIRE script",
            "新图与重生成使用纯文本调用",
            "最多连续两次纯文本重生成",
            "参考图条件生成超时不能据此判定 imagegen 不可用",
            "单一修改 / 必须保持 / 允许变化 / 禁止变化",
        ),
        "skills/research-visuals/references/prompt-recipes.md": (
            "minimum 500 words",
            "等待用户选择后",
            "Do not use or condition on any reference image",
            "最多连续两次纯文本整图重生成",
            "Preserve exactly:",
            "No watermark, logo, pseudo-text, random interface copy, decorative formulas",
        ),
        "skills/research-visuals/references/figure-planning.md": (
            "禁止为全新生成、根据参考图重绘或失败后重生成设置",
            "不随新图或重生成的 imagegen 调用上传",
        ),
        "skills/sysu-ppt/SKILL.md": (
            "优先生成无文字视觉层",
            "再在 PPT 中用原生文本框和连接线叠加",
        ),
        "skills/project-init/scripts/init_project.R": (
            'system2("git", c("add"',
            'c("commit", "-m"',
            "Table0_flowchart",
            "有远端才正常 push",
        ),
        "skills/project-init/SKILL.md": (
            "开始新的数据分析任务",
            "自动 commit + push",
            "有远端才正常 push",
        ),
        "skills/git-commit-helper/SKILL.md": (
            "commit and push without asking again",
        ),
        "skills/r-biostats/SKILL.md": ('source("../skills/',),
        "skills/biostat-principles/SKILL.md": (
            "CLAUDE.md 的 CRITICAL 条款",
            "所有执行 skill 冲突时，本文件优先级更高",
            "提交前征询用户",
            "09_backup/<YYYY-MM-DD>_<主题>/",
        ),
        "skills/academic-publishing/SKILL.md": (
            "生成或润色任一部件",
            "批准→下一部件",
            "09_backup/<日期>_scripts_oneoff/",
        ),
        "skills/academic-publishing/references/chinese-thesis.md": (
            "数字唯一来源 = `0_result_summaries.md`",
            "结果变 → 回写 `0_result_summaries.md`",
        ),
        "skills/publication-figures/SKILL.md": (
            "用户要求出图、画图、做图、生成 Fig",
            "多结局图含全部结局",
        ),
        "skills/epi-project-audit/SKILL.md": (
            "python <EpiAgentKit仓库>/scripts/epiagentkit.py check-project",
            "不通过不进入下一层",
            "文件命名不规范（重命名）",
            "散落临时文件（移入对应目录）",
            "### 自动修复动作",
        ),
        "hooks/final_project_check.py": (
            "results.source_older_than_outputs",
        ),
        "skills/python-ecg-analysis/SKILL.md": (
            "对拟运行入口执行 `python <script> --help`",
        ),
        "skills/biostat-principles/references/result-summary-schema.md": (
            'source("../skills/',
        ),
        "skills/consulting-delivery/scripts/consulting_scaffold.R": (
            '"06_results"',
        ),
        "skills/consulting-delivery/references/templates.md": (
            'write_xlsx(tbl, "tables/Table1',
        ),
        "skills/consulting-delivery/SKILL.md": (
            "每个新版本用新日期建新包",
            "旧包移 `09_backup/` 或保留原位",
            "系统创建的隔离临时目录",
        ),
        "skills/docx/SKILL.md": ("Install: `npm install -g docx`",),
        "skills/pptx/SKILL.md": (
            '`pip install "markitdown[pptx]"`',
            "`pip install Pillow`",
            "`npm install -g pptxgenjs`",
        ),
        "skills/pptx/pptxgenjs.md": (
            "Install: `npm install -g react-icons react react-dom sharp`",
        ),
        "skills/pdf/SKILL.md": ("# Requires: pip install pytesseract pdf2image",),
        "skills/xlsx/SKILL.md": ("You can assume LibreOffice is installed",),
        "skills/epi-project-audit/scripts/check_consistency.py": (
            "pip install pyyaml",
        ),
        "scripts/sync_user_configs.py": (
            "safe_remove(destination, target, dry_run)",
            "shutil.copytree(skill, destination)",
        ),
        "hooks/fig_selfcheck.sh": ("-newermt",),
        "hooks/check_results_rds.sh": ("-newermt",),
        "scripts/configure_user.py": (
            "PRESETS = {",
            "DEPENDENCIES = {",
            "def csv_values(",
        ),
        "skills/sysu-ppt/references/figure_snippets.R": (
            "flow_box <- function",
            "make_decision <- function",
        ),
        "skills/sysu-ppt/references/deck_skeleton.R": (
            'ppt <- sysu_add_section(',
            'sysu_add_text(ppt, "目录"',
            'genre = "formal"',
        ),
    }
    for relative, fragments in forbidden.items():
        body = read(relative)
        for fragment in fragments:
            if fragment in body:
                problems.append(f"{relative}: forbidden workflow fragment {fragment!r}")

    with tempfile.TemporaryDirectory(prefix="epiagentkit_sync_audit_") as directory:
        test_root = Path(directory)
        source = test_root / "source"
        target = test_root / "target"
        (source / "assets").mkdir(parents=True)
        (target / "assets").mkdir(parents=True)
        (source / "SKILL.md").write_text("new skill\n", encoding="utf-8")
        (source / "assets/template.pptx").write_bytes(b"new asset")
        (target / "SKILL.md").write_text("old skill\n", encoding="utf-8")
        old_asset = target / "assets/template.pptx"
        old_asset.write_bytes(b"old asset")
        old_asset.chmod(0o444)
        (target / "stale.txt").write_text("stale\n", encoding="utf-8")
        try:
            mirror_tree(source, target)
            if (target / "SKILL.md").read_text(encoding="utf-8") != "new skill\n":
                problems.append("sync mirror self-test: SKILL.md was not replaced")
            if old_asset.read_bytes() != b"new asset":
                problems.append("sync mirror self-test: read-only asset was not replaced")
            if (target / "stale.txt").exists():
                problems.append("sync mirror self-test: stale file was not removed")
            if list(target.rglob(".epi-*.tmp")):
                problems.append("sync mirror self-test: temporary files remain")
        except OSError as error:
            problems.append(f"sync mirror self-test failed: {error}")

    with tempfile.TemporaryDirectory(prefix="epiagentkit_partial_sync_") as directory:
        test_root = Path(directory)
        repo = test_root / "repo"
        target = test_root / "target"
        for name in ("alpha", "beta"):
            skill = repo / "skills" / name
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                f"---\nname: {name}\ndescription: test\n---\n", encoding="utf-8"
            )
        target.mkdir(parents=True)
        (target / "alpha").mkdir()
        (target / "alpha" / "SKILL.md").write_text("existing\n", encoding="utf-8")
        (target / LEGACY_SKILL_MANIFEST).write_text(
            '{"managed": ["alpha"]}\n', encoding="utf-8"
        )
        try:
            sync_skills(
                repo,
                target,
                exclude=set(),
                dry_run=False,
                include={"beta"},
                prune_stale=False,
            )
            managed = set(
                json.loads(
                    (target / SKILL_MANIFEST).read_text(encoding="utf-8")
                )["managed"]
            )
            if managed != {"alpha", "beta"}:
                problems.append("partial sync self-test: managed manifest was not merged")
            if (target / LEGACY_SKILL_MANIFEST).exists():
                problems.append("partial sync self-test: legacy manifest was not migrated")
            if not (target / "alpha" / "SKILL.md").is_file():
                problems.append("partial sync self-test: existing managed skill was removed")
        except OSError as error:
            problems.append(f"partial sync self-test failed: {error}")

    with tempfile.TemporaryDirectory(prefix="epiagentkit_hook_sync_") as directory:
        test_root = Path(directory)
        hooks_dir = test_root / ".claude" / "hooks"
        config_path = test_root / ".claude" / "settings.json"
        hooks_dir.mkdir(parents=True)
        original = {
            "model": "custom-model",
            "hooks": {
                "PostToolUse": [
                    {
                        "matcher": "Bash",
                        "hooks": [
                            {
                                "type": "command",
                                "command": "custom-quality-check",
                            },
                            {
                                "type": "command",
                                "command": "bash ~/.claude/hooks/fig_selfcheck.sh",
                            },
                        ],
                    }
                ]
            },
        }
        config_path.write_text(
            json.dumps(original, ensure_ascii=False), encoding="utf-8"
        )
        try:
            sync_hook_config(
                "claude", config_path, hooks_dir, dry_run=False, windows=True
            )
            first = json.loads(config_path.read_text(encoding="utf-8"))
            sync_hook_config(
                "claude", config_path, hooks_dir, dry_run=False, windows=True
            )
            second = json.loads(config_path.read_text(encoding="utf-8"))
            commands = [
                hook.get("command", "")
                for groups in second.get("hooks", {}).values()
                for group in groups
                if isinstance(group, dict)
                for hook in group.get("hooks", [])
                if isinstance(hook, dict)
            ]
            managed = [
                command
                for command in commands
                if any(name in command for name in MANAGED_HOOK_SCRIPTS)
            ]
            registered = [
                command
                for command in commands
                if any(name in command for name in REGISTERED_HOOK_SCRIPTS)
            ]
            legacy = MANAGED_HOOK_SCRIPTS - REGISTERED_HOOK_SCRIPTS
            if first != second:
                problems.append("hook sync self-test: repeated install is not idempotent")
            if second.get("model") != "custom-model" or "custom-quality-check" not in commands:
                problems.append("hook sync self-test: unrelated settings were not preserved")
            if len(managed) != len(REGISTERED_HOOK_SCRIPTS):
                problems.append("hook sync self-test: managed hook count is incorrect")
            if len(registered) != len(REGISTERED_HOOK_SCRIPTS):
                problems.append("hook sync self-test: registered hook count is incorrect")
            if any(any(name in command for name in legacy) for command in commands):
                problems.append("hook sync self-test: legacy checks remain separately registered")
            if any("run_hook.cmd" not in command for command in managed):
                problems.append("hook sync self-test: Windows hook bypasses run_hook.cmd")
            if any(not command.startswith("cmd.exe /d /s /c call ") for command in managed):
                problems.append("hook sync self-test: Windows hook is shell-dependent")
            if any('"claude"' not in command for command in managed):
                problems.append("hook sync self-test: client identity is not forwarded")
            if not config_path.with_name("settings.json.epiagentkit.bak").is_file():
                problems.append("hook sync self-test: config backup was not created")
            if not hook_command(hooks_dir, "fig_selfcheck.sh", windows=False).startswith(
                "EPIAGENTKIT_HOOK_CLIENT=claude bash "
            ):
                problems.append("hook sync self-test: POSIX command does not use bash")
        except (OSError, ValueError) as error:
            problems.append(f"hook sync self-test failed: {error}")

    with tempfile.TemporaryDirectory(prefix="epiagentkit_install_audit_") as directory:
        home = Path(directory)
        (home / ".epiclaude").mkdir()
        (home / ".epiclaude/state").write_text("legacy\n", encoding="utf-8")
        for platform, config_name in ((".claude", "settings.json"), (".codex", "hooks.json")):
            platform_home = home / platform
            (platform_home / "hooks").mkdir(parents=True)
            config_path = platform_home / config_name
            config_path.write_text(
                json.dumps({"model": "personal-model"}), encoding="utf-8"
            )
            config_path.with_name(f"{config_name}.epiclaude.bak").write_text(
                "legacy backup\n", encoding="utf-8"
            )
            (platform_home / "hooks" / "custom.sh").write_text(
                "#!/usr/bin/env bash\n", encoding="utf-8"
            )
            (platform_home / LEGACY_INSTALL_MANIFEST).write_text(
                '{"components": [], "skills": [], "skill_dirs": []}\n',
                encoding="utf-8",
            )
            (platform_home / "hooks" / LEGACY_HOOK_MANIFEST).write_text(
                '{"managed": []}\n', encoding="utf-8"
            )

        inline_conflict = home / ".codex/hooks/legacy_r_check.py"
        inline_conflict.write_text("Rscript -e 'parse(file=x)'\n", encoding="utf-8")
        codex_inline = home / ".codex/config.toml"
        codex_inline.write_text(
            "model = 'personal-model'\n\n"
            "[[hooks.PostToolUse]]\n"
            "matcher = 'apply_patch'\n"
            "[[hooks.PostToolUse.hooks]]\n"
            "type = 'command'\n"
            f"command = 'python \"{inline_conflict}\"'\n"
            "[[hooks.PostToolUse.hooks]]\n"
            "type = 'command'\n"
            "command = 'custom-quality-check'\n",
            encoding="utf-8",
        )

        compatibility = home / ".codex/skills"
        managed_duplicate = compatibility / "academic-humanizer"
        mirror_tree(ROOT / "skills/academic-humanizer", managed_duplicate)
        (compatibility / SKILL_MANIFEST).write_text(
            '{"managed": ["academic-humanizer"]}\n', encoding="utf-8"
        )
        personal_skill = compatibility / "personal-skill/SKILL.md"
        personal_skill.parent.mkdir(parents=True)
        personal_skill.write_text("personal skill\n", encoding="utf-8")
        system_skill = compatibility / ".system/system-skill/SKILL.md"
        system_skill.parent.mkdir(parents=True)
        system_skill.write_text("system skill\n", encoding="utf-8")

        install = [
            "install",
            "--target",
            "all",
            "--preset",
            "custom",
            "--skills",
            "academic-humanizer",
            "--with-rules",
            "--with-hooks",
            "--yes",
            "--home",
            str(home),
        ]

        before_dry_run = snapshot_tree(home)
        dry_run = run_epiagentkit([*install, "--dry-run"])
        if dry_run.returncode:
            problems.append(
                "Codex compatibility migration dry-run failed: "
                + (dry_run.stdout + dry_run.stderr).strip()
            )
        elif snapshot_tree(home) != before_dry_run:
            problems.append("Codex compatibility migration dry-run changed files")
        elif "MIGRATE Codex compatibility skills: academic-humanizer" not in dry_run.stdout:
            problems.append("Codex compatibility migration dry-run omitted the managed skill name")

        compatibility_mode = run_epiagentkit(
            [
                "sync",
                "--target",
                "codex",
                "--components",
                "skills",
                "--home",
                str(home),
                "--codex-layout",
                "both",
                "--dry-run",
            ]
        )
        if (
            compatibility_mode.returncode
            or "compatibility mode" not in compatibility_mode.stdout
        ):
            problems.append("Codex compatibility layout did not emit a warning")

        first = run_epiagentkit(install)
        if first.returncode:
            problems.append(
                "dual-platform install self-test failed: "
                + (first.stdout + first.stderr).strip()
            )
        else:
            expected_paths = (
                home / ".claude/CLAUDE.md",
                home / ".codex/AGENTS.md",
                home / ".claude/skills/academic-humanizer/SKILL.md",
                home / ".agents/skills/academic-humanizer/SKILL.md",
                home / ".claude/.epiagentkit-install.json",
                home / ".codex/.epiagentkit-install.json",
                home / ".epiagentkit/state",
                home / ".claude/settings.json.epiagentkit.bak",
                home / ".codex/hooks.json.epiagentkit.bak",
                home / ".codex/config.toml.epiagentkit.bak",
            )
            missing = [str(path) for path in expected_paths if not path.is_file()]
            if missing:
                problems.append(
                    "dual-platform install self-test: missing files: " + ", ".join(missing)
                )
            if managed_duplicate.exists() or (compatibility / SKILL_MANIFEST).exists():
                problems.append(
                    "Codex compatibility migration left a verified managed duplicate"
                )
            if not personal_skill.is_file() or not system_skill.is_file():
                problems.append(
                    "Codex compatibility migration removed unmanaged or .system content"
                )
            legacy = [
                path
                for platform in (home / ".claude", home / ".codex")
                for path in (
                    platform / LEGACY_INSTALL_MANIFEST,
                    platform / "hooks" / LEGACY_HOOK_MANIFEST,
                )
                if path.exists()
            ]
            legacy.extend(home.glob("*/**/*.epiclaude.bak"))
            if (home / ".epiclaude").exists():
                legacy.append(home / ".epiclaude")
            if legacy:
                problems.append(
                    "dual-platform install self-test: legacy manifests remain: "
                    + ", ".join(map(str, legacy))
                )

            for config_path in (home / ".claude/settings.json", home / ".codex/hooks.json"):
                config = json.loads(config_path.read_text(encoding="utf-8"))
                if config.get("model") != "personal-model":
                    problems.append(
                        f"dual-platform install self-test: personal config changed: {config_path}"
                    )
            codex_hooks = json.loads(
                (home / ".codex/hooks.json").read_text(encoding="utf-8")
            )
            codex_commands = [
                handler.get("command", "")
                for groups in codex_hooks.get("hooks", {}).values()
                for group in groups
                for handler in group.get("hooks", [])
                if isinstance(handler, dict)
            ]
            if inline_conflict.exists() or "custom-quality-check" not in codex_commands:
                problems.append(
                    "hook conflict self-test: conflict was not deleted or custom hook was lost"
                )
            if "[[hooks." in codex_inline.read_text(encoding="utf-8"):
                problems.append("hook conflict self-test: Codex inline hooks were not migrated")
            reports = list((home / ".epiagentkit/hook-conflict-reports").glob("*/manifest.json"))
            if len(reports) != 1:
                problems.append("hook conflict self-test: deletion report count is incorrect")

            before = snapshot_tree(home)
            second = run_epiagentkit(install)
            if second.returncode:
                problems.append(
                    "dual-platform reinstall self-test failed: "
                    + (second.stdout + second.stderr).strip()
                )
            elif snapshot_tree(home) != before:
                problems.append("dual-platform reinstall self-test: install is not idempotent")

            doctor = run_epiagentkit(
                [
                    "doctor",
                    "--target",
                    "all",
                    "--home",
                    str(home),
                    "--json",
                ]
            )
            try:
                doctor_payload = json.loads(doctor.stdout)
            except json.JSONDecodeError:
                doctor_payload = {}
            if doctor.returncode or not doctor_payload.get("ok"):
                problems.append(
                    "dual-platform doctor self-test failed: "
                    + (doctor.stdout + doctor.stderr).strip()
                )
            runtime_checks = {
                check.get("item")
                for check in doctor_payload.get("checks", [])
                if check.get("status") == "PASS"
            }
            if not {"claude.hook_runtime", "codex.hook_runtime"} <= runtime_checks:
                problems.append(
                    "dual-platform doctor self-test did not execute both Windows hook launchers"
                )

            mirror_tree(
                ROOT / "skills/academic-humanizer",
                compatibility / "academic-humanizer",
            )
            duplicate_doctor = run_epiagentkit(
                ["doctor", "--target", "codex", "--home", str(home), "--json"]
            )
            try:
                duplicate_payload = json.loads(duplicate_doctor.stdout)
            except json.JSONDecodeError:
                duplicate_payload = {}
            duplicate_checks = duplicate_payload.get("checks", [])
            if duplicate_doctor.returncode != 1 or not any(
                check.get("item") == "codex.skills.duplicate_roots"
                and check.get("status") == "FAIL"
                for check in duplicate_checks
            ):
                problems.append("Codex duplicate-root doctor self-test did not fail")

    with tempfile.TemporaryDirectory(prefix="epiagentkit_python_delivery_") as directory:
        delivery_root = Path(directory) / "reports"
        driver = Path(directory) / "create_python_delivery.R"
        scaffold = (ROOT / "skills/consulting-delivery/scripts/consulting_scaffold.R").as_posix()
        root_value = delivery_root.as_posix()
        driver.write_text(
            f'source("{scaffold}", encoding = "UTF-8")\n'
            f'create_delivery_pack("分析结果包", root = "{root_value}", '
            'language = "python")\n',
            encoding="utf-8",
        )
        delivery = subprocess.run(
            ["Rscript", str(driver)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        pack = delivery_root / "分析结果包"
        expected_python_pack = (
            pack / "run_pipeline.py",
            pack / "code/run_order.py",
            pack / "README.md",
            pack / "DELIVERY_CONTENTS.md",
        )
        expected_python_dirs = (pack / "outputs", pack / "run_records")
        if (
            delivery.returncode
            or not all(path.is_file() for path in expected_python_pack)
            or not all(path.is_dir() for path in expected_python_dirs)
        ):
            problems.append(
                "Python consulting scaffold self-test failed: "
                + (delivery.stdout + delivery.stderr).strip()
            )
        if (pack / "run_pipeline.R").exists():
            problems.append("Python consulting scaffold emitted an R entry point")

    notice_helper = ROOT / "hooks" / "_emit_notice.py"
    for client, expected_key in (("claude", "hookSpecificOutput"), ("codex", "systemMessage")):
        environment = os.environ.copy()
        environment["EPIAGENTKIT_HOOK_CLIENT"] = client
        result = subprocess.run(
            [sys.executable, str(notice_helper)],
            input="quality reminder",
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=environment,
        )
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            payload = {}
        if result.returncode or expected_key not in payload:
            problems.append(f"hook notice self-test: invalid {client} success payload")

    with tempfile.TemporaryDirectory(prefix="epiagentkit_raw_guard_") as directory:
        project = Path(directory) / "project"
        (project / "01_data/rawdata").mkdir(parents=True)
        (project / "外部原始数据").mkdir()
        (project / "folder/供应方 原始导出").mkdir(parents=True)
        (project / "06_results").mkdir()
        (project / ".epiagentkit-raw-roots").write_text(
            "外部原始数据\nfolder/供应方 原始导出\n", encoding="utf-8"
        )
        raw_hook = ROOT / "hooks" / "protect_rawdata.sh"

        def raw_payload(path: str) -> str:
            return json.dumps({"tool_input": {"file_path": path}}, ensure_ascii=False)

        protected_paths = (
            "01_data/rawdata/record.csv",
            r"01_data\rawdata\record.csv",
            "外部原始数据/record.csv",
            r"folder\供应方 原始导出\record.csv",
            "../project/外部原始数据/record.csv",
            "06_results/../01_data/rawdata/record.csv",
            (project / "folder/供应方 原始导出/record.csv").as_posix(),
        )
        for path in protected_paths:
            result = run_hook_script(raw_hook, project, raw_payload(path))
            try:
                decision = json.loads(result.stdout)["hookSpecificOutput"][
                    "permissionDecision"
                ]
            except (json.JSONDecodeError, KeyError, TypeError):
                decision = ""
            if result.returncode or decision != "deny":
                problems.append(f"raw guard self-test did not deny canonical path: {path}")

        patch_payload = json.dumps(
            {
                "tool_input": {
                    "command": "*** Begin Patch\n"
                    "*** Update File: 外部原始数据/record.csv\n"
                    "*** End Patch"
                }
            },
            ensure_ascii=False,
        )
        patch_result = run_hook_script(raw_hook, project, patch_payload)
        if '"permissionDecision":"deny"' not in patch_result.stdout:
            problems.append("raw guard self-test did not inspect apply_patch paths")

        escaped_patch_payload = json.dumps(
            {
                "tool_input": {
                    "command": "*** Begin Patch\n"
                    "*** Update File: 06_results/../01_data/rawdata/record.csv\n"
                    "*** End Patch"
                }
            }
        )
        escaped_patch = run_hook_script(raw_hook, project, escaped_patch_payload)
        if '"permissionDecision":"deny"' not in escaped_patch.stdout:
            problems.append("raw guard self-test missed apply_patch path escape")

        opaque_commands = (
            "Set-Content -LiteralPath '01_data/rawdata/record.csv' -Value x",
            "python -c \"from pathlib import Path; Path('01_data/rawdata/record.csv').write_text('x')\"",
        )
        for command in opaque_commands:
            result = run_hook_script(
                raw_hook,
                project,
                json.dumps({"tool_input": {"command": command}}),
            )
            if result.returncode or result.stdout.strip() or result.stderr.strip():
                problems.append(
                    "raw guard self-test: early validation claimed to parse opaque shell writes"
                )

        for path in (
            "06_results/output.xlsx",
            "外部原始数据/../06_results/output.xlsx",
        ):
            result = run_hook_script(raw_hook, project, raw_payload(path))
            if result.returncode or result.stdout.strip() or result.stderr.strip():
                problems.append(f"raw guard self-test blocked derived path: {path}")

    with tempfile.TemporaryDirectory(prefix="epiagentkit_text_scan_") as directory:
        project = Path(directory)
        allowed = project / "report.md"
        backlog = project / "BACKLOG.md"
        bad_emoji = project / "bad_emoji.md"
        bad_backlog = project / "bad_backlog.md"
        bad_trace = project / "bad_trace.md"
        allowed.write_text("A → B ↔ C ↑ ↓；1±2；2×3；x≥y≤z；37℃\n", encoding="utf-8")
        checkmark = chr(0x2705)
        backlog.write_text(
            "| 待完善内容 | 完善方式 | 重要性 | 状态 |\n"
            f"| 【分析】复核 | 人工 | 建议 | {checkmark} 2026-07-13 |\n",
            encoding="utf-8",
        )
        bad_emoji.write_text("status " + chr(0x1F600) + "\n", encoding="utf-8")
        bad_backlog.write_text(
            "| 待完善内容 | 完善方式 | 重要性 | 状态 |\n"
            f"| {checkmark} 错列 | 人工 | 建议 | 完成 |\n",
            encoding="utf-8",
        )
        bad_trace.write_text("作为" + "AI助手，我为你生成了以下报告。\n", encoding="utf-8")
        scan_hook = ROOT / "hooks" / "scan_ai_trace.sh"
        for path in (allowed, backlog):
            result = run_hook_script(
                scan_hook, project, raw_payload(path.relative_to(project).as_posix())
            )
            if result.returncode or result.stdout.strip() or result.stderr.strip():
                problems.append(f"text scan self-test rejected allowed symbols: {path.name}")
        for path in (bad_emoji, bad_backlog, bad_trace):
            result = run_hook_script(
                scan_hook, project, raw_payload(path.relative_to(project).as_posix())
            )
            if result.returncode != 2:
                problems.append(f"text scan self-test allowed forbidden content: {path.name}")

    file_state = load_module("epiagentkit_file_state", ROOT / "hooks" / "_file_state.py")
    with tempfile.TemporaryDirectory(prefix="epiagentkit_file_state_") as directory:
        invalid_state = Path(directory) / "invalid.json"
        invalid_state.write_text("{}\n", encoding="utf-8")
        invalid_files, invalid_baseline = file_state.load_previous(invalid_state)
        if invalid_files or not invalid_baseline:
            problems.append("file state self-test: incomplete state was not reset to baseline")
        path = Path(directory) / "Fig1_test.png"
        base_ns = 1_700_000_000_000_000_000
        path.write_bytes(b"first")
        os.utime(path, ns=(base_ns, base_ns))
        calls: list[Path] = []

        def counted_digest(target: Path) -> str:
            calls.append(target)
            return hashlib.sha256(target.read_bytes()).hexdigest()

        files = {"04_figures/Fig1_test.png": path}
        first_state, first_changed = file_state.update_fingerprints(
            files, {}, True, counted_digest
        )
        if first_changed or len(calls) != 1:
            problems.append("file state self-test: baseline was not silent and complete")
        calls.clear()
        _, unchanged = file_state.update_fingerprints(
            files, first_state, False, counted_digest
        )
        if unchanged or calls:
            problems.append("file state self-test: unchanged stat triggered hashing")
        path.write_bytes(b"first")
        os.utime(path, ns=(base_ns + 2_000_000_000, base_ns + 2_000_000_000))
        calls.clear()
        second_state, same_content = file_state.update_fingerprints(
            files, first_state, False, counted_digest
        )
        if same_content or len(calls) != 1:
            problems.append("file state self-test: stat candidate was not hash-checked")
        path.write_bytes(b"other")
        os.utime(path, ns=(base_ns + 4_000_000_000, base_ns + 4_000_000_000))
        calls.clear()
        _, content_changed = file_state.update_fingerprints(
            files, second_state, False, counted_digest
        )
        if content_changed != ["04_figures/Fig1_test.png"] or len(calls) != 1:
            problems.append("file state self-test: changed candidate was not reported")

    with tempfile.TemporaryDirectory(prefix="epiagentkit_hook_aggregate_") as directory:
        project = Path(directory) / "project"
        state = Path(directory) / "state"
        code = project / "02_code"
        figures = project / "04_figures"
        results = project / "06_results"
        code.mkdir(parents=True)
        figures.mkdir()
        results.mkdir()
        good_r = code / "01_good.R"
        bad_r = code / "02_bad.R"
        bad_text = project / "report.md"
        good_r.write_text("x <- 1\n", encoding="utf-8")
        bad_r.write_text("x <-\n", encoding="utf-8")
        bad_text.write_text("作为" + "AI助手，我为你生成了以下报告。\n", encoding="utf-8")
        figure = figures / "Fig1_test.png"
        figure.write_bytes(b"png fixture")
        os.utime(figure, (1, 1))
        (results / "model.rds").write_bytes(b"rds fixture")

        edit_hook = ROOT / "hooks" / "post_edit_checks.sh"
        bash_hook = ROOT / "hooks" / "post_bash_checks.sh"

        def edit_payload(path: Path) -> str:
            return json.dumps(
                {"tool_input": {"file_path": path.relative_to(project).as_posix()}}
            )

        good = run_hook_script(edit_hook, project, edit_payload(good_r))
        bad_syntax = run_hook_script(edit_hook, project, edit_payload(bad_r))
        bad_trace = run_hook_script(edit_hook, project, edit_payload(bad_text))
        if good.returncode or good.stdout.strip() or good.stderr.strip():
            problems.append("aggregate edit hook self-test: valid R file did not pass cleanly")
        if bad_syntax.returncode != 2 or "R 语法检查未过" not in bad_syntax.stderr:
            problems.append("aggregate edit hook self-test: R syntax failure was not preserved")
        if bad_trace.returncode != 2 or "助手口吻、过程痕迹或禁止字符" not in bad_trace.stderr:
            problems.append("aggregate edit hook self-test: text trace failure was not preserved")

        hook_env = {"EPIAGENTKIT_STATE_HOME": str(state)}
        baseline = run_hook_script(bash_hook, project, environment=hook_env)
        if baseline.returncode or baseline.stdout.strip() or baseline.stderr.strip():
            problems.append("aggregate Bash hook self-test: first baseline reported old files")

        figure.write_bytes(b"png fixture changed")
        (results / "model.rds").write_bytes(b"rds fixture changed")
        combined = run_hook_script(bash_hook, project, environment=hook_env)
        repeated = run_hook_script(bash_hook, project, environment=hook_env)
        try:
            combined_payload = json.loads(combined.stdout)
            combined_message = combined_payload["hookSpecificOutput"]["additionalContext"]
        except (json.JSONDecodeError, KeyError, TypeError):
            combined_message = ""
        if (
            combined.returncode
            or "检测到新生成/修改的图" not in combined_message
            or "检测到 06_results/ 新写入 .rds" not in combined_message
        ):
            problems.append("aggregate Bash hook self-test: combined notice lost a check")
        if repeated.returncode or repeated.stdout.strip() or repeated.stderr.strip():
            problems.append("aggregate Bash hook self-test: repeated notice was not deduplicated")

        figure.write_bytes(b"changed png content with a different size")
        os.utime(figure, (1, 1))
        changed = run_hook_script(bash_hook, project, environment=hook_env)
        try:
            changed_message = json.loads(changed.stdout)["hookSpecificOutput"][
                "additionalContext"
            ]
        except (json.JSONDecodeError, KeyError, TypeError):
            changed_message = ""
        if changed.returncode or "Fig1_test.png" not in changed_message:
            problems.append(
                "aggregate Bash hook self-test: candidate content change was missed"
            )

        second_project = Path(directory) / "second_project"
        second_figure = second_project / "04_figures/Fig1_test.png"
        second_figure.parent.mkdir(parents=True)
        second_figure.write_bytes(b"png fixture")
        second_baseline = run_hook_script(bash_hook, second_project, environment=hook_env)
        second_figure.write_bytes(b"png fixture changed")
        same_name = run_hook_script(bash_hook, second_project, environment=hook_env)
        same_name_repeat = run_hook_script(bash_hook, second_project, environment=hook_env)
        try:
            same_name_message = json.loads(same_name.stdout)["hookSpecificOutput"][
                "additionalContext"
            ]
        except (json.JSONDecodeError, KeyError, TypeError):
            same_name_message = ""
        if (
            second_baseline.returncode
            or second_baseline.stdout.strip()
            or second_baseline.stderr.strip()
            or same_name.returncode
            or "Fig1_test.png" not in same_name_message
        ):
            problems.append(
                "aggregate Bash hook self-test: project-scoped state collided on same Fig name"
            )
        if (
            same_name_repeat.returncode
            or same_name_repeat.stdout.strip()
            or same_name_repeat.stderr.strip()
        ):
            problems.append(
                "aggregate Bash hook self-test: second project notice was not deduplicated"
            )

    with tempfile.TemporaryDirectory(prefix="epiagentkit_final_check_") as directory:
        root = Path(directory)
        check_command = ROOT / "scripts" / "epiagentkit.py"

        missing_result = run_epiagentkit(
            ["check-project", str(root / "missing"), "--json"]
        )
        try:
            missing_payload = json.loads(missing_result.stdout)
        except json.JSONDecodeError:
            missing_payload = {}
        if missing_result.returncode != 1 or "project.not_directory" not in {
            item.get("check") for item in missing_payload.get("findings", [])
        }:
            problems.append("final project check self-test accepted a missing project root")

        good = root / "good"
        (good / "01_data/rawdata").mkdir(parents=True)
        (good / "02_code").mkdir(parents=True)
        (good / "02_code/vendored").mkdir()
        (good / "02_code/lib").mkdir()
        (good / "03_tables").mkdir()
        (good / "04_figures").mkdir()
        (good / "07_paper").mkdir()
        (good / "09_backup").mkdir()
        (good / "node_modules").mkdir()
        (good / "01_data/rawdata/secret.env").write_text(
            "api_key = should_never_be_scanned\n", encoding="utf-8"
        )
        (good / "09_backup/report_final.md").write_text("old\n", encoding="utf-8")
        (good / "node_modules/cache.log").write_text(
            "WARNING should be pruned\n", encoding="utf-8"
        )
        (good / "02_code/01_clean.R").write_text("x <- 1\n", encoding="utf-8")
        for helper in (
            "config.py",
            "registry.py",
            "conventions.py",
            "lib.py",
            "modelling.py",
            "custom_helper.py",
        ):
            (good / "02_code" / helper).write_text("VALUE = 1\n", encoding="utf-8")
        (good / "02_code/vendored/helper.py").write_text("VALUE = 1\n", encoding="utf-8")
        (good / ".epiagentkit-check.json").write_text(
            json.dumps({"code_helper_files": ["custom_helper.py"]}), encoding="utf-8"
        )
        table = good / "03_tables/Table1_baseline.xlsx"
        chart_png = good / "04_figures/Fig1_flow.png"
        chart_pdf = good / "04_figures/Fig1_flow.pdf"
        source = good / "07_paper/results.yaml"
        summary = good / "07_paper/0_result_summaries.md"
        table.write_bytes(b"xlsx")
        chart_png.write_bytes(b"png")
        chart_pdf.write_bytes(b"pdf")
        source.write_text("schema_version: 1\n", encoding="utf-8")
        summary.write_text("summary\n", encoding="utf-8")
        os.utime(source, (1, 1))
        os.utime(table, (2, 2))
        os.utime(chart_png, (2, 2))
        os.utime(chart_pdf, (2, 2))
        os.utime(summary, (3, 3))
        (good / "identifiers.md").write_text(
            "sha256:" + "a" * 64 + "\n"
            "10.1234/abcdefghijklmnopqrstuvwxyz123456789\n"
            "https://example.org/path/abcdefghijklmnopqrstuvwxyz123456789\n"
            "123e4567-e89b-12d3-a456-426614174000\n",
            encoding="utf-8",
        )
        (good / "settings.py").write_text(
            'api_key = os.getenv("API_KEY")\n'
            'password = "replace_me"\n'
            "this_is_a_long_descriptive_runtime_identifier_without_a_secret = True\n",
            encoding="utf-8",
        )
        (good / "package-lock.json").write_text(
            '{"integrity":"sha512-AbCdEfGhIjKlMnOpQrStUvWxYz0123456789+/="}\n',
            encoding="utf-8",
        )
        good_result = subprocess.run(
            [sys.executable, str(check_command), "check-project", str(good), "--json"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        try:
            good_payload = json.loads(good_result.stdout)
        except json.JSONDecodeError:
            good_payload = {}
        if good_result.returncode or not good_payload.get("ok"):
            problems.append("final project check self-test rejected a valid fixture")
        good_findings = good_payload.get("findings", [])
        good_errors = [item for item in good_findings if item.get("level") == "ERROR"]
        good_checks = {item.get("check") for item in good_findings}
        if good_errors:
            problems.append("final project check self-test emitted errors for legal helpers/formats")
        if "figures.duplicate_number" in good_checks:
            problems.append("final project check self-test rejected PNG/PDF with same Fig stem")
        if not {
            "results.source_mtime_older_than_outputs",
            "provenance.receipt_missing",
        } <= good_checks:
            problems.append("final project check self-test did not downgrade mtime to warnings")
        if {"secrets.named_credential", "secrets.high_entropy", "naming.legacy_version"} & good_checks:
            problems.append("final project check self-test failed pruning or benign-token filters")

        escape = good / ".epiagentkit-check.json"
        escape.write_text(
            json.dumps({"provenance_receipt": "../outside-receipt.json"}),
            encoding="utf-8",
        )
        escape_result = run_epiagentkit(["check-project", str(good), "--json"])
        try:
            escape_payload = json.loads(escape_result.stdout)
        except json.JSONDecodeError:
            escape_payload = {}
        if escape_result.returncode != 1 or "contract.invalid" not in {
            item.get("check") for item in escape_payload.get("findings", [])
        }:
            problems.append("final project check self-test allowed provenance path escape")
        escape.write_text(
            json.dumps({"code_helper_files": ["custom_helper.py"]}),
            encoding="utf-8",
        )

        receipt_bad = root / "receipt_bad"
        (receipt_bad / "07_paper").mkdir(parents=True)
        receipt_source = receipt_bad / "07_paper/results.yaml"
        receipt_summary = receipt_bad / "07_paper/0_result_summaries.md"
        receipt_source.write_text("schema_version: 1\n", encoding="utf-8")
        receipt_summary.write_text("summary\n", encoding="utf-8")
        (receipt_bad / "07_paper/results.provenance.json").write_text(
            json.dumps(
                {
                    "files": {
                        "07_paper/results.yaml": "0" * 64,
                        "07_paper/0_result_summaries.md": hashlib.sha256(
                            receipt_summary.read_bytes()
                        ).hexdigest(),
                    }
                }
            ),
            encoding="utf-8",
        )
        receipt_result = run_epiagentkit(
            ["check-project", str(receipt_bad), "--json"]
        )
        try:
            receipt_payload = json.loads(receipt_result.stdout)
        except json.JSONDecodeError:
            receipt_payload = {}
        if receipt_result.returncode != 1 or "provenance.hash_mismatch" not in {
            item.get("check") for item in receipt_payload.get("findings", [])
        }:
            problems.append("final project check self-test missed provenance hash mismatch")

        bad = root / "bad"
        (bad / "01_data/rawdata").mkdir(parents=True)
        (bad / "02_code").mkdir()
        (bad / "03_tables").mkdir()
        (bad / "04_figures").mkdir()
        (bad / "07_paper").mkdir()
        (bad / "01_data/rawdata/source.csv").write_text("id\n1\n", encoding="utf-8")
        (bad / "02_code/01_clean.R").write_text("x <- 1\n", encoding="utf-8")
        (bad / "02_code/03_model.R").write_text("x <- 2\n", encoding="utf-8")
        (bad / "02_code/unexpected.py").write_text("VALUE = 1\n", encoding="utf-8")
        bad_table = bad / "03_tables/Table1_result.xlsx"
        (bad / "04_figures/Fig1_flow.png").write_bytes(b"png")
        (bad / "04_figures/Fig1_other.pdf").write_bytes(b"pdf")
        bad_source = bad / "07_paper/results.yaml"
        bad_summary = bad / "07_paper/0_result_summaries.md"
        bad_table.write_bytes(b"xlsx")
        bad_source.write_text("schema_version: 1\n", encoding="utf-8")
        bad_summary.write_text("summary\n", encoding="utf-8")
        os.utime(bad_source, (1, 1))
        os.utime(bad_table, (2, 2))
        os.utime(bad_summary, (3, 3))
        (bad / "report_final.md").write_text("report\n", encoding="utf-8")
        (bad / "run.log").write_text("WARNING detected\n", encoding="utf-8")
        alphabet = string.ascii_letters + string.digits
        secret_value = "".join(alphabet[(index * 17) % len(alphabet)] for index in range(48))
        (bad / "config.toml").write_text(
            "api_key = \"" + secret_value + "\"\n", encoding="utf-8"
        )
        subprocess.run(
            ["git", "init", "-q"],
            cwd=bad,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "add", "01_data/rawdata/source.csv"],
            cwd=bad,
            capture_output=True,
            check=True,
        )
        bad_result = subprocess.run(
            [sys.executable, str(check_command), "check-project", str(bad), "--json"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        try:
            bad_payload = json.loads(bad_result.stdout)
        except json.JSONDecodeError:
            bad_payload = {}
        checks = {item.get("check") for item in bad_payload.get("findings", [])}
        required_checks = {
            "rawdata.worktree_modified",
            "code.numbering_gap",
            "code.unnumbered_script",
            "figures.duplicate_number",
            "naming.legacy_version",
            "logs.abnormal_term",
            "secrets.named_credential",
            "secrets.high_entropy",
        }
        if bad_result.returncode != 1 or not required_checks <= checks:
            problems.append("final project check self-test missed a required failure class")
        if secret_value in bad_result.stdout or secret_value in bad_result.stderr:
            problems.append("final project check self-test exposed a credential value")
        named_secret = [
            item
            for item in bad_payload.get("findings", [])
            if item.get("check") == "secrets.named_credential"
        ]
        if not named_secret or not all(
            item.get("path") and item.get("key") and "@" in item["key"]
            for item in named_secret
        ):
            problems.append("final project check self-test omitted secret path/key/line")

    for skill_dir in (ROOT / "skills").iterdir():
        if not skill_dir.is_dir():
            continue
        for directory in (item for item in skill_dir.rglob("*") if item.is_dir()):
            if directory.parent != skill_dir and directory.name == directory.parent.name:
                problems.append(
                    "skill path audit: redundant repeated directory lengthens Windows path: "
                    + str(directory.relative_to(ROOT))
                )

    cmd_bytes = (ROOT / "hooks" / "run_hook.cmd").read_bytes()
    if b"\r\n" not in cmd_bytes or b"\n" in cmd_bytes.replace(b"\r\n", b""):
        problems.append("hook path audit: run_hook.cmd must use CRLF line endings")
    cmd_text = cmd_bytes.decode("utf-8", errors="replace").lower()
    if "where bash.exe" in cmd_text:
        problems.append("hook path audit: run_hook.cmd must not resolve WSL bash.exe")
    if "where git.exe" not in cmd_text:
        problems.append("hook path audit: run_hook.cmd must resolve Git for Windows first")

    if os.name == "nt":
        with tempfile.TemporaryDirectory(prefix="epiagentkit_bash_priority_") as directory:
            fixture = Path(directory)
            wsl_dir = fixture / "Windows WSL"
            git_cmd = fixture / "Portable Git" / "cmd"
            git_bin = fixture / "Portable Git" / "bin"
            wsl_dir.mkdir(parents=True)
            git_cmd.mkdir(parents=True)
            git_bin.mkdir(parents=True)
            system32 = Path(os.environ["SystemRoot"]) / "System32"
            shutil.copy2(system32 / "where.exe", wsl_dir / "bash.exe")
            shutil.copy2(system32 / "where.exe", git_cmd / "git.exe")
            shutil.copy2(system32 / "more.com", git_bin / "bash.exe")
            probe = fixture / "probe.sh"
            probe.write_bytes(b"GIT_BASH_SELECTED\n")
            env = os.environ.copy()
            env["PATH"] = os.pathsep.join((str(wsl_dir), str(git_cmd), str(system32)))
            wrapper = ROOT / "hooks" / "run_hook.cmd"
            result = subprocess.run(
                f'cmd.exe /d /s /c call "{wrapper}" "{probe}" "audit"',
                cwd=fixture,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=env,
            )
            if result.returncode or "GIT_BASH_SELECTED" not in result.stdout:
                problems.append(
                    "Windows hook launcher self-test did not prefer Git Bash over WSL bash.exe"
                )

    if problems:
        print("Workflow contract audit failed:")
        for problem in problems:
            print(f"- {problem}")
        return 1

    print("Workflow contract audit passed.")
    return 0


if __name__ == "__main__":
    configure_utf8_output()
    raise SystemExit(main())
