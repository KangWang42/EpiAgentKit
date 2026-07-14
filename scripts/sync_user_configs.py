#!/usr/bin/env python3
"""Synchronize selected EpiAgentKit rules, skills, and hooks to user homes."""

from __future__ import annotations

import argparse
import filecmp
import json
import os
import shlex
import shutil
import stat
import uuid
from pathlib import Path

from config_core import (
    CODEX_COMPATIBILITY_WARNING,
    HOOK_MANIFEST,
    INSTALL_MANIFEST,
    INSTALL_SCHEMA,
    LEGACY_HOOK_MANIFEST,
    LEGACY_INSTALL_MANIFEST,
    LEGACY_SKILL_MANIFEST,
    PROJECT_NAME,
    SKILL_MANIFEST,
    active_manifest,
    csv_values,
    load_json,
    resolve_codex_skill_dirs,
)
from hook_conflicts import reconcile_hook_conflicts
from skill_conflicts import remove_skill_conflicts, scan_skill_conflicts

CODEX_EXCLUDES = {"skill-creator"}
COPY_IGNORES = {"__pycache__", ".DS_Store"}
VALID_COMPONENTS = {"rules", "skills", "hooks"}
MANAGED_HOOK_SCRIPTS = {
    "protect_rawdata.sh",
    "post_edit_checks.sh",
    "post_bash_checks.sh",
    "check_r_syntax.sh",
    "scan_ai_trace.sh",
    "fig_selfcheck.sh",
    "check_results_rds.sh",
}

HOOK_DEFINITIONS = {
    "PreToolUse": (
        (
            "edit",
            (
                ("protect_rawdata.sh", 15, "校验 rawdata 保护"),
            ),
        ),
    ),
    "PostToolUse": (
        (
            "edit",
            (
                ("post_edit_checks.sh", 45, "检查 R 语法与文本规范"),
            ),
        ),
        (
            "Bash",
            (
                ("post_bash_checks.sh", 40, "检查图件与结果格式"),
            ),
        ),
    ),
}

REGISTERED_HOOK_SCRIPTS = {
    script
    for definitions in HOOK_DEFINITIONS.values()
    for _matcher, scripts in definitions
    for script, _timeout, _status in scripts
}


def remove_readonly(func, path: str, _exc_info) -> None:
    """Retry removal after clearing a Windows read-only attribute."""
    os.chmod(path, stat.S_IWRITE)
    func(path)


def same_path(left: Path, right: Path) -> bool:
    return left.expanduser().resolve() == right.expanduser().resolve()


def safe_remove(path: Path, parent: Path, dry_run: bool) -> None:
    resolved = path.expanduser().resolve()
    root = parent.expanduser().resolve()
    if resolved.parent != root:
        raise RuntimeError(f"Refusing to remove path outside target root: {resolved}")
    print(f"REMOVE {resolved}")
    if not dry_run:
        shutil.rmtree(resolved, onerror=remove_readonly)


def read_manifest(path: Path, legacy: Path | None = None) -> set[str]:
    selected = path if path.is_file() or legacy is None or not legacy.is_file() else legacy
    if not selected.exists():
        return set()
    data = json.loads(selected.read_text(encoding="utf-8"))
    return set(data.get("managed", []))


def write_manifest(
    path: Path, legacy: Path, values: list[str], dry_run: bool
) -> None:
    print(f"WRITE  {path}")
    if not dry_run:
        atomic_write_json(path, {"managed": values})
        if legacy.is_file():
            legacy.unlink()


def sync_file(source: Path, target: Path, dry_run: bool) -> None:
    if same_path(source, target):
        print(f"SOURCE {source} (already active)")
        return
    if target.is_file() and files_equal(source, target):
        print(f"SKIP   {target} (unchanged)")
        return
    print(f"COPY   {source} -> {target}")
    if not dry_run:
        atomic_copy_file(source, target)


def source_skills(
    root: Path, exclude: set[str], include: set[str] | None = None
) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for item in sorted((root / "skills").iterdir()):
        if (
            item.is_dir()
            and item.name not in exclude
            and (include is None or item.name in include)
            and (item / "SKILL.md").is_file()
        ):
            result[item.name] = item
    return result


def ignored(path: Path) -> bool:
    return path.name in COPY_IGNORES or path.suffix == ".pyc"


def files_equal(source: Path, target: Path) -> bool:
    if not target.is_file() or source.stat().st_size != target.stat().st_size:
        return False
    return filecmp.cmp(source, target, shallow=False)


def atomic_copy_file(source: Path, target: Path) -> None:
    """Replace one file without exposing a missing-file window to watchers."""
    if files_equal(source, target):
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".epi-{uuid.uuid4().hex[:8]}.tmp")
    try:
        # copy2 may inherit a read-only bit from bundled assets, which prevents
        # os.replace on Windows. Content parity matters here; timestamps do not.
        shutil.copyfile(source, temporary)
        if target.exists():
            os.chmod(target, stat.S_IWRITE | stat.S_IREAD)
        os.replace(temporary, target)
    finally:
        if temporary.exists():
            os.chmod(temporary, stat.S_IWRITE | stat.S_IREAD)
            temporary.unlink()


def atomic_write_json(path: Path, data: dict) -> None:
    """Write a JSON config without exposing a partial file to the client."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".epi-{uuid.uuid4().hex[:8]}.tmp")
    try:
        temporary.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def mirror_tree(source: Path, target: Path) -> None:
    """Mirror a skill in place while keeping SKILL.md continuously readable."""
    target.mkdir(parents=True, exist_ok=True)

    source_items = [item for item in source.rglob("*") if not ignored(item)]
    for item in sorted(source_items, key=lambda value: (not value.is_dir(), len(value.parts))):
        relative = item.relative_to(source)
        destination = target / relative
        if item.is_dir():
            if destination.is_file() or destination.is_symlink():
                destination.unlink()
            destination.mkdir(parents=True, exist_ok=True)
        elif item.is_file():
            if destination.is_dir():
                shutil.rmtree(destination, onerror=remove_readonly)
            atomic_copy_file(item, destination)

    for item in sorted(target.rglob("*"), key=lambda value: len(value.parts), reverse=True):
        relative = item.relative_to(target)
        source_item = source / relative
        if ignored(item) or not source_item.exists():
            if item.is_dir() and not item.is_symlink():
                shutil.rmtree(item, onerror=remove_readonly)
            else:
                os.chmod(item, stat.S_IWRITE | stat.S_IREAD)
                item.unlink()


def trees_equal(source: Path, target: Path) -> bool:
    """Compare two managed skill trees without reading unrelated sibling content."""
    if not source.is_dir() or not target.is_dir():
        return False
    source_files = {
        item.relative_to(source): item
        for item in source.rglob("*")
        if item.is_file() and not ignored(item)
    }
    target_files = {
        item.relative_to(target): item
        for item in target.rglob("*")
        if item.is_file() and not ignored(item)
    }
    return source_files.keys() == target_files.keys() and all(
        files_equal(source_files[relative], target_files[relative])
        for relative in source_files
    )


def migrate_codex_compatibility_skills(
    root: Path, compatibility: Path, dry_run: bool
) -> None:
    """Remove only verified EpiAgentKit copies from the legacy Codex skill root."""
    manifest = compatibility / SKILL_MANIFEST
    legacy_manifest = compatibility / LEGACY_SKILL_MANIFEST
    selected_manifest = active_manifest(manifest.parent, manifest.name, legacy_manifest.name)
    if not selected_manifest.is_file():
        return

    managed = read_manifest(manifest, legacy_manifest)
    if not managed:
        return
    print("MIGRATE Codex compatibility skills: " + ", ".join(sorted(managed)))
    remaining = set(managed)
    for name in sorted(managed):
        source = root / "skills" / name
        duplicate = compatibility / name
        if not duplicate.exists():
            remaining.discard(name)
            continue
        if not source.is_dir() or not trees_equal(source, duplicate):
            print(f"KEEP   {duplicate} (not identical to repository source)")
            continue
        safe_remove(duplicate, compatibility, dry_run)
        remaining.discard(name)

    if remaining:
        write_manifest(manifest, legacy_manifest, sorted(remaining), dry_run)
        return
    for path in (manifest, legacy_manifest):
        if path.is_file():
            print(f"REMOVE {path}")
            if not dry_run:
                path.unlink()


def sync_skills(
    root: Path,
    target: Path,
    exclude: set[str],
    dry_run: bool,
    include: set[str] | None = None,
    prune_stale: bool = True,
    prune_codex_bundled: bool = False,
    codex_home: Path | None = None,
) -> None:
    source = root / "skills"
    if same_path(source, target):
        print(f"SOURCE {source} (already active)")
        legacy_manifest = target / LEGACY_SKILL_MANIFEST
        if legacy_manifest.is_file():
            print(f"REMOVE {legacy_manifest}")
            if not dry_run:
                legacy_manifest.unlink()
        return
    if not dry_run:
        target.mkdir(parents=True, exist_ok=True)

    available = source_skills(root, exclude)
    if include is not None:
        requested = set(include)
        bundled = requested & exclude
        if bundled:
            print("SKIP   bundled skills: " + ", ".join(sorted(bundled)))
        requested -= exclude
        unknown = requested - set(available)
        if unknown:
            raise ValueError("Unknown or unavailable skills: " + ", ".join(sorted(unknown)))
        skills = {name: available[name] for name in sorted(requested)}
    else:
        skills = available
    manifest = target / SKILL_MANIFEST
    legacy_manifest = target / LEGACY_SKILL_MANIFEST
    previous = read_manifest(manifest, legacy_manifest)
    if prune_stale:
        for stale in sorted(previous - set(skills)):
            stale_path = target / stale
            if stale_path.is_dir():
                safe_remove(stale_path, target, dry_run)

    for name, skill in skills.items():
        destination = target / name
        print(f"SYNC   {skill} -> {destination}")
        if not dry_run:
            mirror_tree(skill, destination)

    if prune_codex_bundled and codex_home is not None:
        for name in sorted(exclude):
            duplicate = target / name
            bundled = codex_home / "skills" / ".system" / name / "SKILL.md"
            if duplicate.is_dir() and bundled.is_file():
                safe_remove(duplicate, target, dry_run)

    managed = set(skills) if prune_stale else previous | set(skills)
    write_manifest(manifest, legacy_manifest, sorted(managed), dry_run)


def sync_hooks(source: Path, target: Path, dry_run: bool) -> None:
    if same_path(source, target):
        print(f"SOURCE {source} (already active)")
        legacy_manifest = target / LEGACY_HOOK_MANIFEST
        if legacy_manifest.is_file():
            print(f"REMOVE {legacy_manifest}")
            if not dry_run:
                legacy_manifest.unlink()
        return
    if not dry_run:
        target.mkdir(parents=True, exist_ok=True)

    files = {
        item.name: item
        for item in source.iterdir()
        if item.is_file()
        and item.name not in {HOOK_MANIFEST, LEGACY_HOOK_MANIFEST}
    }
    manifest = target / HOOK_MANIFEST
    legacy_manifest = target / LEGACY_HOOK_MANIFEST
    previous = read_manifest(manifest, legacy_manifest)
    for stale in sorted(previous - set(files)):
        stale_path = target / stale
        if stale_path.is_file():
            print(f"REMOVE {stale_path}")
            if not dry_run:
                stale_path.unlink()
    for name, item in files.items():
        sync_file(item, target / name, dry_run)
    write_manifest(manifest, legacy_manifest, sorted(files), dry_run)


def hook_command(
    hooks_dir: Path,
    script: str,
    client: str = "claude",
    windows: bool | None = None,
) -> str:
    """Return a hook command that works even when bash is absent from PATH."""
    windows = os.name == "nt" if windows is None else windows
    script_path = hooks_dir / script
    if windows:
        wrapper = (hooks_dir / "run_hook.cmd").as_posix()
        return (
            f'cmd.exe /d /s /c call "{wrapper}" '
            f'"{script_path.as_posix()}" "{client}"'
        )
    return f"EPIAGENTKIT_HOOK_CLIENT={shlex.quote(client)} bash {shlex.quote(str(script_path))}"


def hook_groups(
    platform: str, hooks_dir: Path, windows: bool | None = None
) -> dict[str, list[dict]]:
    edit_matcher = (
        "Write|Edit|MultiEdit" if platform == "claude" else "Edit|Write|apply_patch"
    )
    groups: dict[str, list[dict]] = {}
    for event, definitions in HOOK_DEFINITIONS.items():
        groups[event] = []
        for matcher, scripts in definitions:
            groups[event].append(
                {
                    "matcher": edit_matcher if matcher == "edit" else matcher,
                    "hooks": [
                        {
                            "type": "command",
                            "command": hook_command(
                                hooks_dir, script, client=platform, windows=windows
                            ),
                            "timeout": timeout,
                            "statusMessage": status,
                        }
                        for script, timeout, status in scripts
                    ],
                }
            )
    return groups


def remove_managed_hook_commands(config: dict) -> None:
    """Remove prior EpiAgentKit hook commands while preserving unrelated hooks."""
    hooks = config.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError("Existing 'hooks' setting must be a JSON object")
    for event, groups in tuple(hooks.items()):
        if not isinstance(groups, list):
            continue
        retained_groups = []
        for group in groups:
            if not isinstance(group, dict) or not isinstance(group.get("hooks"), list):
                retained_groups.append(group)
                continue
            retained_commands = []
            for item in group["hooks"]:
                command = item.get("command", "") if isinstance(item, dict) else ""
                if not any(name in str(command) for name in MANAGED_HOOK_SCRIPTS):
                    retained_commands.append(item)
            if retained_commands:
                preserved = dict(group)
                preserved["hooks"] = retained_commands
                retained_groups.append(preserved)
        hooks[event] = retained_groups


def sync_hook_config(
    platform: str,
    config_path: Path,
    hooks_dir: Path,
    dry_run: bool,
    windows: bool | None = None,
) -> None:
    """Merge EpiAgentKit hooks into a client config without touching other settings."""
    if config_path.exists():
        try:
            current = json.loads(config_path.read_text(encoding="utf-8-sig"))
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise ValueError(f"Cannot update invalid JSON config {config_path}: {error}") from error
        if not isinstance(current, dict):
            raise ValueError(f"Config root must be a JSON object: {config_path}")
    else:
        current = {}

    backup = config_path.with_name(f"{config_path.name}.epiagentkit.bak")
    legacy_backup = config_path.with_name(f"{config_path.name}.epiclaude.bak")
    if legacy_backup.is_file() and not backup.exists():
        print(f"RENAME {legacy_backup} -> {backup}")
        if not dry_run:
            legacy_backup.replace(backup)

    updated = json.loads(json.dumps(current))
    remove_managed_hook_commands(updated)
    generated = hook_groups(platform, hooks_dir, windows)
    hooks = updated.setdefault("hooks", {})
    for event, groups in generated.items():
        hooks.setdefault(event, []).extend(groups)

    if updated == current:
        print(f"SKIP   {config_path} (hook config unchanged)")
        return
    print(f"MERGE  EpiAgentKit hooks -> {config_path}")
    if dry_run:
        return
    if config_path.exists() and not backup.exists():
        print(f"BACKUP {config_path} -> {backup}")
        atomic_copy_file(config_path, backup)
    atomic_write_json(config_path, updated)


def update_install_manifest(
    platform: str,
    platform_home: Path,
    root: Path,
    components: set[str],
    skill_dirs: list[Path],
    dry_run: bool,
) -> None:
    path = platform_home / INSTALL_MANIFEST
    legacy_path = platform_home / LEGACY_INSTALL_MANIFEST
    print(f"WRITE  install manifest -> {path}")
    if dry_run:
        return

    current = load_json(path if path.is_file() or not legacy_path.is_file() else legacy_path)
    installed_components = set(current.get("components", [])) | components
    installed_skills = set(current.get("skills", []))
    installed_dirs = [Path(value) for value in current.get("skill_dirs", [])]
    if "skills" in components:
        installed_dirs = skill_dirs
        exclude = CODEX_EXCLUDES if platform == "codex" else set()
        managed_sets = [
            set(source_skills(root, exclude))
            if same_path(root / "skills", directory)
            else read_manifest(
                directory / SKILL_MANIFEST,
                directory / LEGACY_SKILL_MANIFEST,
            )
            for directory in skill_dirs
        ]
        installed_skills = set.intersection(*managed_sets) if managed_sets else set()
    payload = {
        "schema": INSTALL_SCHEMA,
        "project": PROJECT_NAME,
        "platform": platform,
        "source": str(root),
        "components": sorted(installed_components),
        "skills": sorted(installed_skills),
        "skill_dirs": [str(path) for path in dict.fromkeys(installed_dirs)],
        "rule_file": "CLAUDE.md" if platform == "claude" else "AGENTS.md",
        "hook_config": "settings.json" if platform == "claude" else "hooks.json",
    }
    atomic_write_json(path, payload)
    if legacy_path.is_file():
        legacy_path.unlink()


def migrate_legacy_state(home: Path, dry_run: bool) -> None:
    legacy = home / ".epiclaude"
    current = home / ".epiagentkit"
    if legacy.is_dir() and not current.exists():
        print(f"RENAME {legacy} -> {current}")
        if not dry_run:
            legacy.rename(current)


def parse_args(
    argv: list[str] | None = None, prog: str | None = None
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog=prog, description=__doc__)
    parser.add_argument("--target", choices=("all", "claude", "codex"), default="all")
    parser.add_argument(
        "--components",
        action="append",
        help="Comma-separated subset of rules,skills,hooks; default installs all components.",
    )
    parser.add_argument(
        "--skills",
        action="append",
        help="Comma-separated skill names. Omit to synchronize every repository skill.",
    )
    parser.add_argument("--list-skills", action="store_true")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--home", type=Path, default=Path.home(), help="User home; useful for tests")
    parser.add_argument("--claude-home", type=Path)
    parser.add_argument("--codex-home", type=Path)
    parser.add_argument("--codex-skills-dir", type=Path, action="append")
    parser.add_argument(
        "--codex-layout",
        choices=("auto", "agents", "codex", "both"),
        default="auto",
    )
    parser.add_argument("--skip-hooks", action="store_true")
    parser.add_argument("--prune-codex-bundled", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None, prog: str | None = None) -> None:
    args = parse_args(argv, prog)
    root = args.repo_root.expanduser().resolve()
    home = args.home.expanduser().resolve()
    claude_home = (args.claude_home or home / ".claude").expanduser().resolve()
    codex_home = (args.codex_home or home / ".codex").expanduser().resolve()
    if args.codex_layout in {"codex", "both"}:
        print(CODEX_COMPATIBILITY_WARNING)
    codex_skill_dirs = resolve_codex_skill_dirs(
        home,
        codex_home,
        explicit=args.codex_skills_dir,
        layout=args.codex_layout,
    )

    required = (root / "CLAUDE.md", root / "skills", root / "hooks")
    if not all(path.exists() for path in required):
        raise FileNotFoundError(f"Not an EpiAgentKit repository: {root}")

    if args.list_skills:
        for name in source_skills(root, set()):
            print(name)
        return

    migrate_legacy_state(home, args.dry_run)

    components = csv_values(args.components) or set(VALID_COMPONENTS)
    unknown_components = components - VALID_COMPONENTS
    if unknown_components:
        raise ValueError("Unknown components: " + ", ".join(sorted(unknown_components)))
    if args.skip_hooks:
        components.discard("hooks")
    selected_skills = csv_values(args.skills) or None
    if selected_skills is not None and "skills" not in components:
        raise ValueError("--skills requires --components skills")
    prune_stale = selected_skills is None

    if "skills" in components:
        conflicts = []
        if args.target in {"all", "claude"}:
            claude_incoming = set(source_skills(root, set(), selected_skills))
            conflicts.extend(
                scan_skill_conflicts(
                    platform="claude",
                    source_root=root,
                    incoming=claude_incoming,
                    discovery_roots=[claude_home / "skills"],
                    target_roots=[claude_home / "skills"],
                )
            )
        if args.target in {"all", "codex"}:
            codex_incoming = set(source_skills(root, CODEX_EXCLUDES, selected_skills))
            conflicts.extend(
                scan_skill_conflicts(
                    platform="codex",
                    source_root=root,
                    incoming=codex_incoming,
                    discovery_roots=[
                        home / ".agents" / "skills",
                        codex_home / "skills",
                        *codex_skill_dirs,
                    ],
                    target_roots=codex_skill_dirs,
                )
            )
        remove_skill_conflicts(
            conflicts,
            home=home,
            source_root=root,
            dry_run=args.dry_run,
        )

    if args.target in {"all", "claude"}:
        print("\n[Claude Code]")
        if "rules" in components:
            sync_file(root / "CLAUDE.md", claude_home / "CLAUDE.md", args.dry_run)
        if "skills" in components:
            sync_skills(
                root,
                claude_home / "skills",
                set(),
                args.dry_run,
                include=selected_skills,
                prune_stale=prune_stale,
            )
        if "hooks" in components:
            reconcile_hook_conflicts(
                platform="claude",
                json_config=claude_home / "settings.json",
                hooks_dir=claude_home / "hooks",
                home=home,
                protected_names={item.name for item in (root / "hooks").iterdir()},
                dry_run=args.dry_run,
            )
            sync_hooks(root / "hooks", claude_home / "hooks", args.dry_run)
            sync_hook_config(
                "claude",
                claude_home / "settings.json",
                claude_home / "hooks",
                args.dry_run,
            )
        update_install_manifest(
            "claude",
            claude_home,
            root,
            components,
            [claude_home / "skills"] if "skills" in components else [],
            dry_run=args.dry_run,
        )

    if args.target in {"all", "codex"}:
        print("\n[Codex]")
        if "rules" in components:
            sync_file(root / "CLAUDE.md", codex_home / "AGENTS.md", args.dry_run)
        if "skills" in components:
            for codex_skills in codex_skill_dirs:
                sync_skills(
                    root,
                    codex_skills,
                    CODEX_EXCLUDES,
                    args.dry_run,
                    include=selected_skills,
                    prune_stale=prune_stale,
                    prune_codex_bundled=args.prune_codex_bundled,
                    codex_home=codex_home,
                )
            if not args.codex_skills_dir and args.codex_layout in {"auto", "agents"}:
                migrate_codex_compatibility_skills(
                    root, codex_home / "skills", args.dry_run
                )
        if "hooks" in components:
            reconcile_hook_conflicts(
                platform="codex",
                json_config=codex_home / "hooks.json",
                inline_config=codex_home / "config.toml",
                hooks_dir=codex_home / "hooks",
                home=home,
                protected_names={item.name for item in (root / "hooks").iterdir()},
                dry_run=args.dry_run,
            )
            sync_hooks(root / "hooks", codex_home / "hooks", args.dry_run)
            sync_hook_config(
                "codex",
                codex_home / "hooks.json",
                codex_home / "hooks",
                args.dry_run,
            )
        update_install_manifest(
            "codex",
            codex_home,
            root,
            components,
            codex_skill_dirs if "skills" in components else [],
            dry_run=args.dry_run,
        )

    print("\nSync complete. Restart the client if changed skills are not visible.")


if __name__ == "__main__":
    main()
