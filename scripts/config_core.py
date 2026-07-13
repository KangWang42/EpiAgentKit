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

PRESETS = {
    "ppt": {
        "biostat-principles",
        "publication-figures",
        "svg-diagrams",
        "sysu-ppt",
        "pptx",
    },
    "writing": {
        "biostat-principles",
        "academic-humanizer",
        "academic-publishing",
        "report-writing",
        "publication-figures",
        "svg-diagrams",
        "docx",
        "xlsx",
    },
    "analysis": {
        "biostat-principles",
        "r-biostats",
        "publication-figures",
        "xlsx",
    },
}

DEPENDENCIES = {
    "academic-publishing": {
        "biostat-principles",
        "academic-humanizer",
        "publication-figures",
        "svg-diagrams",
    },
    "consulting-delivery": {
        "biostat-principles",
        "r-biostats",
        "academic-humanizer",
    },
    "epi-project-audit": {"biostat-principles"},
    "project-init": {"biostat-principles"},
    "publication-figures": {"biostat-principles"},
    "r-biostats": {"biostat-principles", "publication-figures"},
    "report-writing": {
        "academic-humanizer",
        "publication-figures",
        "svg-diagrams",
        "docx",
    },
    "sysu-ppt": {"publication-figures", "svg-diagrams", "pptx"},
}


def available_skills(root: Path) -> list[str]:
    return sorted(
        item.name
        for item in (root / "skills").iterdir()
        if item.is_dir() and (item / "SKILL.md").is_file()
    )


def csv_values(values: list[str] | None) -> set[str]:
    result: set[str] = set()
    for value in values or []:
        result.update(item.strip() for item in value.split(",") if item.strip())
    return result


def expand_dependencies(selected: set[str]) -> set[str]:
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
    """Resolve official and compatibility Codex skill homes without guessing silently."""
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

    targets = [official]
    managed_compatibility = (
        active_manifest(
            compatibility, SKILL_MANIFEST, LEGACY_SKILL_MANIFEST
        ).is_file()
        or (
            active_manifest(
                codex_home, INSTALL_MANIFEST, LEGACY_INSTALL_MANIFEST
            ).is_file()
            and compatibility.is_dir()
        )
    )
    if managed_compatibility:
        targets.append(compatibility)
    return unique_paths(targets)
