#!/usr/bin/env python3
"""Resolve the central EpiAgentKit CLI and run its check-project command."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


INSTALL_MANIFEST = ".epiagentkit-install.json"


def cli_from_root(root: Path) -> Path | None:
    candidate = root.expanduser().resolve() / "scripts" / "epiagentkit.py"
    return candidate if candidate.is_file() else None


def source_from_manifest(path: Path) -> Path | None:
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return None
    source = payload.get("source") if isinstance(payload, dict) else None
    return Path(source) if isinstance(source, str) and source.strip() else None


def resolve_cli(explicit_root: Path | None = None) -> Path:
    home = Path.home()
    roots: list[Path] = []
    if explicit_root is not None:
        roots.append(explicit_root)

    for manifest in (
        home / ".codex" / INSTALL_MANIFEST,
        home / ".claude" / INSTALL_MANIFEST,
    ):
        source = source_from_manifest(manifest)
        if source is not None:
            roots.append(source)

    # Covers the repository-source Claude layout and its standard default.
    roots.extend((Path(__file__).resolve().parents[3], home / ".claude"))

    checked: list[Path] = []
    for root in roots:
        resolved = root.expanduser().resolve()
        if resolved in checked:
            continue
        checked.append(resolved)
        cli = cli_from_root(resolved)
        if cli is not None:
            return cli

    rendered = ", ".join(str(path / "scripts" / "epiagentkit.py") for path in checked)
    raise FileNotFoundError(
        "Cannot resolve the central EpiAgentKit CLI from install manifests or "
        f"standard source roots. Checked: {rendered}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the central EpiAgentKit check-project gate."
    )
    parser.add_argument("project", type=Path, nargs="?", default=Path.cwd())
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--print-cli", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        cli = resolve_cli(args.repo_root)
    except FileNotFoundError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    if args.print_cli:
        print(cli)
        return 0

    command = [sys.executable, str(cli), "check-project", str(args.project.resolve())]
    if args.as_json:
        command.append("--json")
    return subprocess.run(command, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
