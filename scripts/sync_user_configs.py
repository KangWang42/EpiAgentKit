#!/usr/bin/env python3
"""Synchronize selected EpiClaude rules, skills, and hooks to user homes."""

from __future__ import annotations

import argparse
import filecmp
import json
import os
import shutil
import stat
import uuid
from pathlib import Path


SKILL_MANIFEST = ".epiclaude-managed-skills.json"
HOOK_MANIFEST = ".epiclaude-managed-hooks.json"
CODEX_EXCLUDES = {"skill-creator"}
COPY_IGNORES = {"__pycache__", ".DS_Store"}
VALID_COMPONENTS = {"rules", "skills", "hooks"}


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


def read_manifest(path: Path) -> set[str]:
    if not path.exists():
        return set()
    data = json.loads(path.read_text(encoding="utf-8"))
    return set(data.get("managed", []))


def write_manifest(path: Path, values: list[str], dry_run: bool) -> None:
    print(f"WRITE  {path}")
    if not dry_run:
        path.write_text(
            json.dumps({"managed": values}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


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
    temporary = target.with_name(f".{target.name}.epiclaude-{uuid.uuid4().hex}.tmp")
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
    previous = read_manifest(manifest)
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
    write_manifest(manifest, sorted(managed), dry_run)


def sync_hooks(source: Path, target: Path, dry_run: bool) -> None:
    if same_path(source, target):
        print(f"SOURCE {source} (already active)")
        return
    if not dry_run:
        target.mkdir(parents=True, exist_ok=True)

    files = {
        item.name: item
        for item in source.iterdir()
        if item.is_file() and item.name not in {HOOK_MANIFEST}
    }
    manifest = target / HOOK_MANIFEST
    previous = read_manifest(manifest)
    for stale in sorted(previous - set(files)):
        stale_path = target / stale
        if stale_path.is_file():
            print(f"REMOVE {stale_path}")
            if not dry_run:
                stale_path.unlink()
    for name, item in files.items():
        sync_file(item, target / name, dry_run)
    write_manifest(manifest, sorted(files), dry_run)


def csv_values(values: list[str] | None) -> set[str] | None:
    if not values:
        return None
    result: set[str] = set()
    for value in values:
        result.update(item.strip() for item in value.split(",") if item.strip())
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
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
    parser.add_argument("--codex-skills-dir", type=Path)
    parser.add_argument("--skip-hooks", action="store_true")
    parser.add_argument("--prune-codex-bundled", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = args.repo_root.expanduser().resolve()
    home = args.home.expanduser().resolve()
    claude_home = (args.claude_home or home / ".claude").expanduser().resolve()
    codex_home = (args.codex_home or home / ".codex").expanduser().resolve()
    codex_skills = (
        args.codex_skills_dir or home / ".agents" / "skills"
    ).expanduser().resolve()

    required = (root / "CLAUDE.md", root / "skills", root / "hooks")
    if not all(path.exists() for path in required):
        raise FileNotFoundError(f"Not an EpiClaude repository: {root}")

    if args.list_skills:
        for name in source_skills(root, set()):
            print(name)
        return

    components = csv_values(args.components) or set(VALID_COMPONENTS)
    unknown_components = components - VALID_COMPONENTS
    if unknown_components:
        raise ValueError("Unknown components: " + ", ".join(sorted(unknown_components)))
    if args.skip_hooks:
        components.discard("hooks")
    selected_skills = csv_values(args.skills)
    if selected_skills is not None and "skills" not in components:
        raise ValueError("--skills requires --components skills")
    prune_stale = selected_skills is None

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
            sync_hooks(root / "hooks", claude_home / "hooks", args.dry_run)

    if args.target in {"all", "codex"}:
        print("\n[Codex]")
        if "rules" in components:
            sync_file(root / "CLAUDE.md", codex_home / "AGENTS.md", args.dry_run)
        if "skills" in components:
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
        if "hooks" in components:
            sync_hooks(root / "hooks", codex_home / "hooks", args.dry_run)

    print("\nSync complete. Restart the client if changed skills are not visible.")


if __name__ == "__main__":
    main()
