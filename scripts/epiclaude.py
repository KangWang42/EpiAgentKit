#!/usr/bin/env python3
"""Unified EpiClaude entry point: install, sync, doctor, and list."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import configure_user
import sync_user_configs
from config_core import (
    HOOK_MANIFEST,
    INSTALL_MANIFEST,
    INSTALL_SCHEMA,
    PRESETS,
    PROJECT_NAME,
    SKILL_MANIFEST,
    available_skills,
    load_json,
    resolve_codex_skill_dirs,
)


HELP = """EpiClaude dual-platform configuration manager

Usage:
  python scripts/epiclaude.py install [configure options]
  python scripts/epiclaude.py sync [sync options]
  python scripts/epiclaude.py doctor [doctor options]
  python scripts/epiclaude.py list

Run a subcommand with --help for details.
"""


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_map(root: Path) -> dict[str, str]:
    if not root.is_dir():
        return {}
    return {
        item.relative_to(root).as_posix(): digest(item)
        for item in root.rglob("*")
        if item.is_file()
        and "__pycache__" not in item.parts
        and item.suffix != ".pyc"
        and item.name not in {SKILL_MANIFEST, HOOK_MANIFEST}
    }


def tree_matches(source: Path, target: Path) -> bool:
    """Require every managed source file while allowing unrelated target files."""
    expected = tree_map(source)
    actual = tree_map(target)
    return all(actual.get(relative) == checksum for relative, checksum in expected.items())


def doctor_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=f"{Path(sys.argv[0]).name} doctor",
        description="Verify an installed dual-platform configuration.",
    )
    parser.add_argument("--target", choices=("claude", "codex", "all"), default="all")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--claude-home", type=Path)
    parser.add_argument("--codex-home", type=Path)
    parser.add_argument("--codex-skills-dir", type=Path, action="append")
    parser.add_argument(
        "--codex-layout",
        choices=("auto", "agents", "codex", "both"),
        default="auto",
    )
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser


def check_platform(
    platform: str,
    root: Path,
    platform_home: Path,
    fallback_skill_dirs: list[Path],
) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []

    def record(ok: bool, item: str, detail: str) -> None:
        checks.append({"status": "PASS" if ok else "FAIL", "item": item, "detail": detail})

    manifest_path = platform_home / INSTALL_MANIFEST
    try:
        manifest = load_json(manifest_path)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        record(False, f"{platform}.manifest", str(error))
        return checks
    if not manifest:
        record(False, f"{platform}.manifest", f"missing {manifest_path}")
        return checks
    record(
        manifest.get("schema") == INSTALL_SCHEMA
        and manifest.get("project") == PROJECT_NAME
        and manifest.get("platform") == platform,
        f"{platform}.manifest",
        str(manifest_path),
    )
    components = set(manifest.get("components", []))

    if "rules" in components:
        target_rule = platform_home / ("CLAUDE.md" if platform == "claude" else "AGENTS.md")
        source_rule = root / "CLAUDE.md"
        ok = target_rule.is_file() and digest(target_rule) == digest(source_rule)
        record(ok, f"{platform}.rules", str(target_rule))

    if "skills" in components:
        skill_dirs = [Path(value) for value in manifest.get("skill_dirs", [])] or fallback_skill_dirs
        expected = set(manifest.get("skills", []))
        for skill_dir in skill_dirs:
            if sync_user_configs.same_path(root / "skills", skill_dir):
                managed = set(available_skills(root))
                detail = f"{skill_dir} (repository source is active)"
                record(expected <= managed, f"{platform}.skills.manifest", detail)
            else:
                try:
                    managed = set(load_json(skill_dir / SKILL_MANIFEST).get("managed", []))
                    record(expected <= managed, f"{platform}.skills.manifest", str(skill_dir))
                except (OSError, ValueError, json.JSONDecodeError) as error:
                    record(False, f"{platform}.skills.manifest", str(error))
                    continue
            for name in sorted(expected):
                source = root / "skills" / name
                target = skill_dir / name
                record(
                    source.is_dir() and tree_map(source) == tree_map(target),
                    f"{platform}.skill.{name}",
                    str(target),
                )

    if "hooks" in components:
        hook_dir = platform_home / "hooks"
        record(tree_matches(root / "hooks", hook_dir), f"{platform}.hooks", str(hook_dir))
        config_path = platform_home / ("settings.json" if platform == "claude" else "hooks.json")
        try:
            config = load_json(config_path)
            commands = [
                str(hook.get("command", ""))
                for groups in config.get("hooks", {}).values()
                for group in groups
                if isinstance(group, dict)
                for hook in group.get("hooks", [])
                if isinstance(hook, dict)
            ]
            counts = {
                name: sum(name in command for command in commands)
                for name in sync_user_configs.REGISTERED_HOOK_SCRIPTS
            }
            legacy = (
                sync_user_configs.MANAGED_HOOK_SCRIPTS
                - sync_user_configs.REGISTERED_HOOK_SCRIPTS
            )
            ok = all(value == 1 for value in counts.values()) and not any(
                name in command for name in legacy for command in commands
            )
            record(ok, f"{platform}.hook_config", str(config_path))
        except (OSError, ValueError, json.JSONDecodeError) as error:
            record(False, f"{platform}.hook_config", str(error))
    return checks


def run_doctor(argv: list[str]) -> int:
    args = doctor_parser().parse_args(argv)
    root = args.repo_root.expanduser().resolve()
    home = args.home.expanduser().resolve()
    claude_home = (args.claude_home or home / ".claude").expanduser().resolve()
    codex_home = (args.codex_home or home / ".codex").expanduser().resolve()
    codex_dirs = resolve_codex_skill_dirs(
        home,
        codex_home,
        explicit=args.codex_skills_dir,
        layout=args.codex_layout,
    )
    checks: list[dict[str, str]] = []
    if args.target in {"claude", "all"}:
        checks.extend(check_platform("claude", root, claude_home, [claude_home / "skills"]))
    if args.target in {"codex", "all"}:
        checks.extend(check_platform("codex", root, codex_home, codex_dirs))
    failed = [check for check in checks if check["status"] == "FAIL"]
    if args.as_json:
        print(json.dumps({"ok": not failed, "checks": checks}, ensure_ascii=False, indent=2))
    else:
        for check in checks:
            print(f'[{check["status"]}] {check["item"]}: {check["detail"]}')
        print(f"Doctor {'passed' if not failed else 'failed'}: {len(checks) - len(failed)}/{len(checks)} checks")
    return 1 if failed else 0


def show_list(root: Path) -> int:
    print("Presets:")
    for name, skills in PRESETS.items():
        print(f"  {name}: {', '.join(sorted(skills))}")
    print("Skills:")
    print("  " + ", ".join(available_skills(root)))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in {"-h", "--help"}:
        print(HELP)
        return 0
    command, rest = args[0], args[1:]
    if command == "install":
        return configure_user.main(rest, prog=f"{Path(sys.argv[0]).name} install")
    if command == "sync":
        sync_user_configs.main(rest, prog=f"{Path(sys.argv[0]).name} sync")
        return 0
    if command == "doctor":
        return run_doctor(rest)
    if command == "list":
        return show_list(Path(__file__).resolve().parents[1])
    raise SystemExit(f"Unknown command: {command}\n\n{HELP}")


if __name__ == "__main__":
    raise SystemExit(main())
