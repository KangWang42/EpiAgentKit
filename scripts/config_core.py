#!/usr/bin/env python3
"""Shared configuration model for EpiAgentKit's Claude Code, Codex, and Antigravity installers."""

from __future__ import annotations

import json
from pathlib import Path


PROJECT_NAME = "EpiAgentKit"
INSTALL_MANIFEST = ".epiagentkit-install.json"
SKILL_MANIFEST = ".epiagentkit-managed-skills.json"
HOOK_MANIFEST = ".epiagentkit-managed-hooks.json"
RULE_MANIFEST = ".epiagentkit-managed-rules.json"
LEGACY_INSTALL_MANIFEST = ".epiclaude-install.json"
LEGACY_SKILL_MANIFEST = ".epiclaude-managed-skills.json"
LEGACY_HOOK_MANIFEST = ".epiclaude-managed-hooks.json"
INSTALL_SCHEMA = 1
LOCAL_SKILL_EXCLUDES_FILE = ".epiagentkit-local-skills"
LOCAL_RULES_PRESERVE_FILE = ".epiagentkit-preserve-global-rules"
AGY_RULE_MAX_BYTES = 24000
AGY_RULE_PREFIX = "epiagentkit-rules-"
AGY_HOOK_NAME = "epiagentkit"

# Repository skills that remain available for local development but must not be
# advertised, installed, or synchronized into user runtime skill directories.
SYNC_EXCLUDES = {"python-ecg-analysis"}

PRESETS = {
    "web": {
        "build-web-ui",
    },
    "ppt": {
        "biostat-principles",
        "research-visuals",
        "publication-figures",
        "academic-ppt",
        "sysu-ppt",
        "pptx",
    },
    "writing": {
        "biostat-principles",
        "evidence-research",
        "academic-humanizer",
        "academic-publishing",
        "graduate-opening-report",
        "manuscript-peer-review",
        "report-writing",
        "research-visuals",
        "publication-figures",
        "docx",
        "xlsx",
    },
    "analysis": {
        "biostat-principles",
        "evidence-research",
        "epi-study-design",
        "r-biostats",
        "python-biostats",
        "publication-figures",
        "xlsx",
    },
}

# Installation-time bundle closure only. This does not require the listed
# skills to co-trigger at runtime; runtime routing is defined by descriptions.
DEPENDENCIES = {
    "epiagentkit-maintenance": {"skill-creator"},
    "academic-ppt": {"research-visuals", "publication-figures", "pptx"},
    "academic-publishing": {
        "biostat-principles",
        "evidence-research",
        "academic-humanizer",
        "research-visuals",
        "publication-figures",
    },
    "consulting-delivery": {
        "biostat-principles",
        "r-biostats",
        "python-biostats",
        "academic-humanizer",
        "epi-project-audit",
    },
    "epi-study-design": {"biostat-principles", "evidence-research"},
    "graduate-opening-report": {
        "biostat-principles",
        "epi-study-design",
        "evidence-research",
        "academic-humanizer",
    },
    "epi-project-audit": {"biostat-principles"},
    "manuscript-peer-review": {
        "biostat-principles",
        "evidence-research",
        "academic-humanizer",
    },
    "project-init": {
        "biostat-principles",
        "epi-study-design",
        "r-biostats",
        "python-biostats",
        "consulting-delivery",
        "epi-project-audit",
    },
    "research-visuals": {"svg-diagrams"},
    "publication-figures": {"biostat-principles"},
    "r-biostats": {"biostat-principles", "publication-figures"},
    "python-biostats": {"biostat-principles", "publication-figures"},
    "report-writing": {
        "academic-humanizer",
        "research-visuals",
        "publication-figures",
        "docx",
    },
    "sysu-ppt": {"academic-ppt", "research-visuals", "publication-figures", "pptx"},
}

CODEX_COMPATIBILITY_WARNING = (
    "WARNING: --codex-layout codex/both is a compatibility mode. "
    "The default Codex custom-skill root is ~/.agents/skills; "
    "compatibility layouts can expose duplicate skills."
)


def local_skill_excludes(root: Path) -> set[str]:
    """Read untracked, machine-local skill names that must not be distributed."""
    path = root / LOCAL_SKILL_EXCLUDES_FILE
    if not path.is_file():
        return set()
    return {
        line
        for raw in path.read_text(encoding="utf-8-sig").splitlines()
        if (line := raw.strip()) and not line.startswith("#")
    }


def preserve_global_rules(root: Path) -> bool:
    """Return whether this machine keeps its global rule files unmanaged."""
    return (root / LOCAL_RULES_PRESERVE_FILE).is_file()


def public_skills(root: Path) -> list[str]:
    """List repository skills that are public regardless of machine policy."""
    return sorted(
        item.name
        for item in (root / "skills").iterdir()
        if (
            item.is_dir()
            and item.name not in SYNC_EXCLUDES
            and (item / "SKILL.md").is_file()
        )
    )


def available_skills(root: Path) -> list[str]:
    """List public skills available for installation on this machine."""
    local_excludes = local_skill_excludes(root)
    return [name for name in public_skills(root) if name not in local_excludes]


def csv_values(values: list[str] | None) -> set[str]:
    result: set[str] = set()
    for value in values or []:
        result.update(item.strip() for item in value.split(",") if item.strip())
    return result


def expand_dependencies(selected: set[str]) -> set[str]:
    """Expand installer bundles without imposing runtime skill composition."""
    expanded = set(selected)
    changed = True
    while changed:
        changed = False
        for skill in tuple(expanded):
            additions = DEPENDENCIES.get(skill, set()) - expanded
            if additions:
                expanded.update(additions)
                changed = True
    return expanded


def load_json(path: Path, default: dict | None = None) -> dict:
    if not path.is_file():
        return {} if default is None else dict(default)
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return data


def active_manifest(directory: Path, name: str, legacy_name: str) -> Path:
    current = directory / name
    legacy = directory / legacy_name
    return current if current.is_file() or not legacy.is_file() else legacy


def unique_paths(paths: list[Path]) -> list[Path]:
    result: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        resolved = path.expanduser().resolve()
        if resolved not in seen:
            seen.add(resolved)
            result.append(resolved)
    return result


def resolve_codex_skill_dirs(
    home: Path,
    codex_home: Path,
    explicit: list[Path] | None = None,
    layout: str = "auto",
) -> list[Path]:
    """Resolve Codex skill homes; auto always selects the official custom-skill root."""
    if explicit:
        return unique_paths(explicit)

    official = home / ".agents" / "skills"
    compatibility = codex_home / "skills"
    if layout == "agents":
        return unique_paths([official])
    if layout == "codex":
        return unique_paths([compatibility])
    if layout == "both":
        return unique_paths([official, compatibility])
    if layout != "auto":
        raise ValueError(f"Unknown Codex skill layout: {layout}")

    return unique_paths([official])


def resolve_agy_home(home: Path, explicit: Path | None = None) -> Path:
    """Resolve Antigravity's shared global customization root (~/.gemini/config)."""
    return (explicit or home / ".gemini" / "config").expanduser().resolve()


def agy_skill_discovery_roots(home: Path, agy_home: Path) -> list[Path]:
    """Return global skill roots scanned by Antigravity CLI, App, and IDE."""
    return unique_paths(
        [
            agy_home / "skills",
            home / ".gemini" / "antigravity-cli" / "skills",
            home / ".gemini" / "skills",
        ]
    )


def _agy_rule_frontmatter(index: int, total: int) -> str:
    label = (
        "EpiAgentKit 全局规则"
        if total == 1
        else f"EpiAgentKit 全局规则（第 {index}/{total} 部分）"
    )
    return f'---\ntrigger: always_on\ndescription: "{label}"\n---\n\n'


def render_agy_rule_files(
    source_text: str, *, max_bytes: int = AGY_RULE_MAX_BYTES
) -> dict[str, str]:
    """Split global rules deterministically so every Antigravity rule file fits within 24 KB."""
    normalized = source_text.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff")
    if normalized and not normalized.endswith("\n"):
        normalized += "\n"

    header_budget = len(_agy_rule_frontmatter(99, 99).encode("utf-8"))
    body_limit = max_bytes - header_budget
    if body_limit <= 0:
        raise ValueError(f"Antigravity rule byte limit is too small: {max_bytes}")

    sections: list[str] = []
    current_lines: list[str] = []
    for line in normalized.splitlines(keepends=True):
        if line.startswith("## ") and current_lines:
            sections.append("".join(current_lines))
            current_lines = [line]
        else:
            current_lines.append(line)
    if current_lines:
        sections.append("".join(current_lines))

    units: list[str] = []
    for section in sections:
        if len(section.encode("utf-8")) <= body_limit:
            units.append(section)
            continue
        piece: list[str] = []
        piece_bytes = 0
        for line in section.splitlines(keepends=True):
            line_bytes = len(line.encode("utf-8"))
            if line_bytes > body_limit:
                raise ValueError(
                    "Single rule line exceeds Antigravity's per-file byte limit"
                )
            if piece and piece_bytes + line_bytes > body_limit:
                units.append("".join(piece))
                piece = [line]
                piece_bytes = line_bytes
            else:
                piece.append(line)
                piece_bytes += line_bytes
        if piece:
            units.append("".join(piece))

    chunks: list[str] = []
    current_chunk: list[str] = []
    current_bytes = 0
    for unit in units:
        unit_bytes = len(unit.encode("utf-8"))
        if current_chunk and current_bytes + unit_bytes > body_limit:
            chunks.append("".join(current_chunk))
            current_chunk = [unit]
            current_bytes = unit_bytes
        else:
            current_chunk.append(unit)
            current_bytes += unit_bytes
    if current_chunk or not chunks:
        chunks.append("".join(current_chunk))

    total = len(chunks)
    rendered: dict[str, str] = {}
    for index, body in enumerate(chunks, start=1):
        content = _agy_rule_frontmatter(index, total) + body
        if len(content.encode("utf-8")) > max_bytes:
            raise ValueError(
                f"Rendered Antigravity rule part {index} exceeds {max_bytes} bytes"
            )
        rendered[f"{AGY_RULE_PREFIX}{index:02d}.md"] = content
    return rendered
