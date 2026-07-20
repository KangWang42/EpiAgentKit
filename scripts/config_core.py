#!/usr/bin/env python3
"""Shared configuration model for EpiAgentKit's Claude Code and Codex installers."""

from __future__ import annotations

import json
from pathlib import Path


PROJECT_NAME = "EpiAgentKit"
INSTALL_MANIFEST = ".epiagentkit-install.json"
SKILL_MANIFEST = ".epiagentkit-managed-skills.json"
HOOK_MANIFEST = ".epiagentkit-managed-hooks.json"
LEGACY_INSTALL_MANIFEST = ".epiclaude-install.json"
LEGACY_SKILL_MANIFEST = ".epiclaude-managed-skills.json"
LEGACY_HOOK_MANIFEST = ".epiclaude-managed-hooks.json"
INSTALL_SCHEMA = 1

# Repository skills that remain available for local development but must not be
# advertised, installed, or synchronized into user runtime skill directories.
SYNC_EXCLUDES = {"python-ecg-analysis"}

PRESETS = {
    "ppt": {
        "biostat-principles",
        "research-visuals",
        "publication-figures",
        "sysu-ppt",
        "pptx",
    },
    "writing": {
        "biostat-principles",
        "evidence-research",
        "academic-humanizer",
        "academic-publishing",
        "report-writing",
        "research-visuals",
        "publication-figures",
        "docx",
        "xlsx",
    },
    "analysis": {
        "biostat-principles",
        "evidence-research",
        "r-biostats",
        "publication-figures",
        "xlsx",
    },
}

# Installation-time bundle closure only. This does not require the listed
# skills to co-trigger at runtime; runtime routing is defined by descriptions.
DEPENDENCIES = {
    "epiagentkit-maintenance": {"skill-creator"},
    "academic-publishing": {
        "biostat-principles",
        "academic-humanizer",
        "research-visuals",
        "publication-figures",
    },
    "consulting-delivery": {
        "biostat-principles",
        "r-biostats",
        "academic-humanizer",
        "epi-project-audit",
    },
    "epi-project-audit": {"biostat-principles"},
    "project-init": {"biostat-principles", "epi-project-audit"},
    "research-visuals": {"svg-diagrams"},
    "publication-figures": {"biostat-principles"},
    "r-biostats": {"biostat-principles", "publication-figures"},
    "report-writing": {
        "academic-humanizer",
        "research-visuals",
        "publication-figures",
        "docx",
    },
    "sysu-ppt": {"research-visuals", "publication-figures", "pptx"},
}

CODEX_COMPATIBILITY_WARNING = (
    "WARNING: --codex-layout codex/both is a compatibility mode. "
    "The default Codex custom-skill root is ~/.agents/skills; "
    "compatibility layouts can expose duplicate skills."
)


def available_skills(root: Path) -> list[str]:
    return sorted(
        item.name
        for item in (root / "skills").iterdir()
        if (
            item.is_dir()
            and item.name not in SYNC_EXCLUDES
            and (item / "SKILL.md").is_file()
        )
    )


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
