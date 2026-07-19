#!/usr/bin/env python3
"""Unified EpiAgentKit entry point for configuration and project checks."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import configure_user
import sync_user_configs
from config_core import (
    CODEX_COMPATIBILITY_WARNING,
    HOOK_MANIFEST,
    INSTALL_MANIFEST,
    INSTALL_SCHEMA,
    LEGACY_HOOK_MANIFEST,
    LEGACY_INSTALL_MANIFEST,
    LEGACY_SKILL_MANIFEST,
    PRESETS,
    PROJECT_NAME,
    SKILL_MANIFEST,
    active_manifest,
    available_skills,
    load_json,
    resolve_codex_skill_dirs,
)


HELP = """EpiAgentKit dual-platform configuration manager

Usage:
  python scripts/epiagentkit.py install [configure options]
  python scripts/epiagentkit.py sync [sync options]
  python scripts/epiagentkit.py doctor [doctor options]
  python scripts/epiagentkit.py check-project [project] [--json]
  python scripts/epiagentkit.py list

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
        and item.name
        not in {
            SKILL_MANIFEST,
            HOOK_MANIFEST,
            LEGACY_SKILL_MANIFEST,
            LEGACY_HOOK_MANIFEST,
        }
    }


def tree_matches(source: Path, target: Path) -> bool:
    """Require every managed source file while allowing unrelated target files."""
    expected = tree_map(source)
    actual = tree_map(target)
    return all(actual.get(relative) == checksum for relative, checksum in expected.items())


def probe_windows_hook_launcher(wrapper: Path) -> tuple[bool, str]:
    """Run a minimal hook through the installed Windows launcher."""
    if os.name != "nt":
        return True, f"{wrapper} (Windows runtime probe not required)"
    if not wrapper.is_file():
        return False, f"missing {wrapper}"
    try:
        with tempfile.TemporaryDirectory(prefix="epiagentkit_hook_probe_") as directory:
            probe = Path(directory) / "probe.sh"
            probe.write_bytes(b"exit 0\n")
            result = subprocess.run(
                f'cmd.exe /d /s /c call "{wrapper}" "{probe}" "doctor"',
                cwd=directory,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
    except OSError as error:
        return False, f"{wrapper}: {error}"
    if result.returncode:
        message = (result.stderr or result.stdout).strip()
        detail = f"{wrapper}: exit {result.returncode}"
        if message:
            detail += f"; {message[:300]}"
        return False, detail
    return True, str(wrapper)


def codex_skill_duplicates(home: Path, codex_home: Path) -> dict[str, list[Path]]:
    """Find same-named skills visible from both Codex discovery roots."""
    roots = [home / ".agents" / "skills", codex_home / "skills"]
    locations: dict[str, list[Path]] = {}
    for root in roots:
        if not root.is_dir():
            continue
        for item in root.iterdir():
            if item.is_dir() and (item / "SKILL.md").is_file():
                locations.setdefault(item.name, []).append(item)
    return {name: paths for name, paths in locations.items() if len(paths) > 1}


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

    manifest_path = active_manifest(
        platform_home, INSTALL_MANIFEST, LEGACY_INSTALL_MANIFEST
    )
    try:
        manifest = load_json(manifest_path)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        record(False, f"{platform}.manifest", str(error))
        return checks
    if not manifest:
        record(False, f"{platform}.manifest", f"missing {manifest_path}")
        return checks
    valid_project = manifest.get("project") == PROJECT_NAME or (
        manifest_path.name == LEGACY_INSTALL_MANIFEST
        and manifest.get("project") == "EpiClaude"
    )
    record(
        manifest.get("schema") == INSTALL_SCHEMA
        and valid_project
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
                    manifest_path = active_manifest(
                        skill_dir, SKILL_MANIFEST, LEGACY_SKILL_MANIFEST
                    )
                    managed = set(load_json(manifest_path).get("managed", []))
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
        runtime_ok, runtime_detail = probe_windows_hook_launcher(
            hook_dir / "run_hook.cmd"
        )
        record(runtime_ok, f"{platform}.hook_runtime", runtime_detail)
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
        duplicates = codex_skill_duplicates(home, codex_home)
        if duplicates:
            detail = "; ".join(
                f"{name}: {', '.join(map(str, paths))}"
                for name, paths in sorted(duplicates.items())
            )
            compatibility_mode = bool(args.codex_skills_dir) or args.codex_layout in {
                "codex",
                "both",
            }
            checks.append(
                {
                    "status": "WARN" if compatibility_mode else "FAIL",
                    "item": "codex.skills.duplicate_roots",
                    "detail": detail,
                }
            )
        else:
            checks.append(
                {
                    "status": "PASS",
                    "item": "codex.skills.duplicate_roots",
                    "detail": "no duplicate skill names across discovery roots",
                }
            )
        if args.codex_layout in {"codex", "both"}:
            checks.append(
                {
                    "status": "WARN",
                    "item": "codex.skills.compatibility_layout",
                    "detail": CODEX_COMPATIBILITY_WARNING,
                }
            )
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


def run_check_project(argv: list[str]) -> int:
    checker = Path(__file__).resolve().parents[1] / "hooks" / "final_project_check.py"
    result = subprocess.run([sys.executable, str(checker), *argv])
    return result.returncode


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
    if command == "check-project":
        return run_check_project(rest)
    if command == "list":
        return show_list(Path(__file__).resolve().parents[1])
    raise SystemExit(f"Unknown command: {command}\n\n{HELP}")


if __name__ == "__main__":
    raise SystemExit(main())
