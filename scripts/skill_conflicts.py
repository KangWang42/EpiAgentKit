#!/usr/bin/env python3
"""Detect and remove local skills that conflict with EpiAgentKit."""

from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import shutil
import stat
import unicodedata
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


CONFLICT_DOMAINS = {
    "academic-humanizer": (
        "去 ai 味",
        "去ai味",
        "学术文本润色",
        "文风更自然",
        "ai 痕迹",
        "academic humanizer",
    ),
    "academic-publishing": (
        "写论文",
        "论文初稿",
        "生成论文",
        "manuscript writing",
        "cover letter",
        "response to reviewers",
        "审稿回复",
        "投稿信",
        "graphical abstract",
    ),
    "biostat-principles": (
        "卫生统计项目的底层行为原则",
        "流行病学项目的底层行为原则",
        "biostatistics principles",
    ),
    "epi-study-design": (
        "流行病学研究设计",
        "研究方案与统计分析计划",
        "pico peco estimand sap",
        "epidemiologic study design",
    ),
    "epiagentkit-maintenance": (
        "维护 epiagentkit",
        "epiagentkit skills hooks 同步",
        "epiagentkit maintenance",
    ),
    "consulting-delivery": (
        "统计咨询交付",
        "咨询交付包",
        "外发代码和结果",
        "consulting deliverables",
    ),
    "docx": ("word document", "word 文档", ".docx 文件处理", "manipulate a word"),
    "epi-project-audit": (
        "项目审查",
        "项目质控",
        "复核结果",
        "检查代码/表图/论文",
        "project audit",
    ),
    "evidence-research": (
        "文献检索",
        "来源核验",
        "证据矩阵",
        "literature search",
        "verify sources",
    ),
    "git-commit-helper": ("commit message", "提交信息", "reviewing staged changes"),
    "pdf": ("pdf files", "pdf 文件", "pdf处理", "anything with pdf"),
    "pptx": (".pptx", "powerpoint 文件", "presentation file", "幻灯片文件处理"),
    "project-init": (
        "创建研究项目",
        "初始化目录",
        "标准研究项目结构",
        "project initialization",
    ),
    "publication-figures": (
        "任意科研出图",
        "论文配图",
        "发表级图件",
        "任何 ggplot",
        "任何 matplotlib",
        "publication-quality figures",
    ),
    "python-ecg-analysis": (
        "python ecg",
        "ecg analysis",
        "心电图分析",
        "心电信号处理",
    ),
    "r-biostats": (
        "r 统计分析",
        "r语言统计分析",
        "描述统计、回归、生存分析",
        "中介效应、meta 分析",
        "r biostatistics",
    ),
    "python-biostats": (
        "python 统计分析",
        "python 流行病学分析",
        "python 生物统计",
        "python biostatistics",
    ),
    "research-visuals": (
        "科研视觉资产",
        "imagegen 科研视觉",
        "流程图、技术路线、结构图、概念框架",
        "学术论文配图提示词",
        "academic diagram prompt",
        "paper figure prompt",
        "scientific research visuals",
    ),
    "report-writing": (
        "分析报告",
        "进展报告",
        "操作指引",
        "报告类 word",
        "professional report writing",
    ),
    "svg-diagrams": (
        "svg 原生",
        "svg原生",
        "技术路线图",
        "结构图、层级图",
        "svg diagrams",
    ),
    "sysu-ppt": (
        "中山大学组会",
        "中山大学学术汇报",
        "中大组会",
        "sysu ppt",
    ),
    "skill-creator": (
        "创建 skill",
        "优化 agent skill",
        "create or update an agent skill",
        "skill creator",
    ),
    "xlsx": ("spreadsheet file", "电子表格文件", ".xlsx", ".xlsm"),
}

DISABLED_MARKERS = ("已停用", "disabled", "不再触发")
DELEGATION_MARKERS = (
    "委派",
    "已被",
    "默认走",
    "不要用",
    "仅当",
    "仅用于",
    "后备",
    "only when",
    "do not use",
    "fallback",
    "delegate",
)
IGNORED_NAMES = {"__pycache__", ".DS_Store"}


@dataclass(frozen=True)
class SkillConflict:
    platform: str
    kind: str
    local_name: str
    local_path: str
    authority: str
    matched_terms: tuple[str, ...]
    discovery_root: str
    target_root: bool


def normalize(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).lower().split())


def read_skill_description(skill_md: Path) -> str:
    """Read the description field without requiring a YAML dependency."""
    text = skill_md.read_text(encoding="utf-8-sig")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return ""
    try:
        closing = next(index for index in range(1, len(lines)) if lines[index].strip() == "---")
    except StopIteration:
        return ""
    frontmatter = lines[1:closing]
    for index, line in enumerate(frontmatter):
        match = re.match(r"^description\s*:\s*(.*)$", line)
        if not match:
            continue
        value = match.group(1).strip()
        if value in {"|", ">", "|-", ">-", "|+", ">+"}:
            collected: list[str] = []
            for following in frontmatter[index + 1 :]:
                if following and not following[0].isspace():
                    break
                collected.append(following.strip())
            return "\n".join(collected).strip()
        if value.startswith(('"', "'")):
            try:
                parsed = ast.literal_eval(value)
                return parsed if isinstance(parsed, str) else str(parsed)
            except (SyntaxError, ValueError):
                return value.strip('"\'')
        return value
    return ""


def skill_tree_map(root: Path) -> dict[str, str]:
    if not root.is_dir():
        return {}
    result: dict[str, str] = {}
    for path in root.rglob("*"):
        if not path.is_file() or any(part in IGNORED_NAMES for part in path.parts):
            continue
        if path.suffix == ".pyc":
            continue
        relative = path.relative_to(root).as_posix()
        result[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def skill_trees_equal(left: Path, right: Path) -> bool:
    return skill_tree_map(left) == skill_tree_map(right)


def is_delegated(description: str, authority: str) -> bool:
    normalized = normalize(description)
    if any(marker in normalized for marker in DISABLED_MARKERS):
        return True
    authority_name = normalize(authority)
    return authority_name in normalized and any(
        marker in normalized for marker in DELEGATION_MARKERS
    )


def semantic_match(description: str, incoming: set[str]) -> tuple[str, tuple[str, ...]] | None:
    normalized = normalize(description)
    candidates: list[tuple[int, str, tuple[str, ...]]] = []
    for authority in sorted(incoming):
        terms = CONFLICT_DOMAINS.get(authority, ())
        matched = tuple(term for term in terms if normalize(term) in normalized)
        if not matched or is_delegated(description, authority):
            continue
        score = sum(len(normalize(term)) for term in matched)
        candidates.append((score, authority, matched))
    if not candidates:
        return None
    _score, authority, matched = max(candidates, key=lambda item: (item[0], item[1]))
    return authority, matched


def unique_resolved(paths: list[Path]) -> list[Path]:
    result: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        resolved = path.expanduser().resolve()
        if resolved not in seen:
            seen.add(resolved)
            result.append(resolved)
    return result


def scan_skill_conflicts(
    *,
    platform: str,
    source_root: Path,
    incoming: set[str],
    discovery_roots: list[Path],
    target_roots: list[Path],
) -> list[SkillConflict]:
    """Find exact-name, duplicate-root, and broad-trigger conflicts."""
    source_skills = (source_root / "skills").resolve()
    targets = set(unique_resolved(target_roots))
    conflicts: list[SkillConflict] = []
    seen_paths: set[Path] = set()
    for discovery_root in unique_resolved(discovery_roots):
        if discovery_root == source_skills or not discovery_root.is_dir():
            continue
        for skill_dir in sorted(discovery_root.iterdir()):
            skill_md = skill_dir / "SKILL.md"
            if not skill_dir.is_dir() or not skill_md.is_file():
                continue
            resolved = skill_dir.resolve()
            if resolved in seen_paths:
                continue
            seen_paths.add(resolved)
            local_name = skill_dir.name
            is_target = discovery_root in targets
            if local_name in incoming:
                source = source_skills / local_name
                identical = source.is_dir() and skill_trees_equal(source, skill_dir)
                if identical and is_target:
                    continue
                conflicts.append(
                    SkillConflict(
                        platform=platform,
                        kind="duplicate_root" if identical else "exact_name",
                        local_name=local_name,
                        local_path=str(resolved),
                        authority=local_name,
                        matched_terms=(local_name,),
                        discovery_root=str(discovery_root),
                        target_root=is_target,
                    )
                )
                continue
            description = read_skill_description(skill_md)
            match = semantic_match(description, incoming)
            if match is None:
                continue
            authority, matched_terms = match
            conflicts.append(
                SkillConflict(
                    platform=platform,
                    kind="semantic_overlap",
                    local_name=local_name,
                    local_path=str(resolved),
                    authority=authority,
                    matched_terms=matched_terms,
                    discovery_root=str(discovery_root),
                    target_root=is_target,
                )
            )
    return conflicts


def remove_readonly(func, path: str, _exc_info) -> None:
    os.chmod(path, stat.S_IWRITE)
    func(path)


def remove_tree(path: Path) -> bool:
    """Remove a tree, tolerating an empty Windows directory held by a client."""
    try:
        shutil.rmtree(path, onerror=remove_readonly)
    except PermissionError:
        if os.name == "nt" and path.is_dir() and not any(path.iterdir()):
            print(f"DEFER  {path} (empty directory is locked; remove after client restart)")
            return False
        raise
    return True


def remove_skill_conflicts(
    conflicts: list[SkillConflict],
    *,
    home: Path,
    source_root: Path,
    dry_run: bool,
    run_id: str | None = None,
) -> Path | None:
    """Delete conflicting skill trees and write a compact audit report."""
    if not conflicts:
        print("Skill conflict preflight: no conflicts found.")
        return None
    run_id = run_id or (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        + "-"
        + uuid.uuid4().hex[:8]
    )
    run_root = (
        home.expanduser().resolve()
        / ".epiagentkit"
        / "skill-conflict-reports"
        / run_id
    )
    records: list[dict] = []
    handled: set[Path] = set()
    for conflict in conflicts:
        original = Path(conflict.local_path).resolve()
        if original in handled:
            continue
        handled.add(original)
        print(
            f"CONFLICT {conflict.kind}: {original} -> {conflict.authority} "
            f"({', '.join(conflict.matched_terms)})"
        )
        if dry_run:
            print(f"WOULD REMOVE {original}")
        record = asdict(conflict)
        record["action"] = "would_delete" if dry_run else "pending_delete"
        records.append(record)
        if not original.is_dir():
            raise FileNotFoundError(f"Conflicting skill disappeared before deletion: {original}")
        discovery_root = Path(conflict.discovery_root).resolve()
        if original.parent != discovery_root:
            raise RuntimeError(f"Refusing to delete path outside discovery root: {original}")
    if dry_run:
        print(f"Conflict deletion report would be written under {run_root}")
        return run_root / "manifest.json"
    payload = {
        "schema": 1,
        "project": "EpiAgentKit",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": str(source_root.resolve()),
        "conflicts": records,
    }
    manifest = run_root / "manifest.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    for record in records:
        manifest.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        original = Path(record["local_path"])
        print(f"REMOVE {original}")
        removed = remove_tree(original)
        record["action"] = "deleted" if removed else "deferred_empty_directory"
    manifest.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"WRITE  conflict deletion report -> {manifest}")
    return manifest
