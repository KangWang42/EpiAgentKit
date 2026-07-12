#!/usr/bin/env python3
"""Audit cross-skill workflow contracts that are easy to regress."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from sync_user_configs import SKILL_MANIFEST, mirror_tree, sync_skills


ROOT = Path(__file__).resolve().parents[1]
LINE_BUDGET = 200


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def main() -> int:
    problems: list[str] = []

    for relative in ("CLAUDE.md", "AGENTS.md"):
        count = len(read(relative).splitlines())
        if count > LINE_BUDGET:
            problems.append(f"{relative}: {count} lines exceeds {LINE_BUDGET}")

    validator = ROOT / "skills/skill-creator/scripts/quick_validate.py"
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

    required = {
        "skills/project-init/scripts/init_project.R": (
            '"PROTOCOL.md"',
            '"SAP.md"',
            '"09_backup/EXPERIMENTS.md"',
            '"09_backup/INDEX.md"',
            '"02_code/config.R"',
            '"02_code/conventions.R"',
            '"02_code/vendored"',
        ),
        "skills/r-biostats/SKILL.md": (
            "02_code/vendored/emit_summary.R",
            "02_code/vendored/fig_setup.R",
            "PROTOCOL.md",
            "SAP.md",
        ),
        "skills/biostat-principles/SKILL.md": (
            "09_backup/EXPERIMENTS.md",
            "PLAN.md",
            "FINDINGS.md",
        ),
        "skills/consulting-delivery/SKILL.md": (
            "09_backup/INDEX.md",
            "MANIFEST.md",
            "唯一当前交付包",
        ),
        "skills/consulting-delivery/scripts/consulting_scaffold.R": (
            'subdirs <- c("data", "code", "results", "tables", "figures")',
            'source("code/config.R"',
            "TABLE_REGISTRY <- character()",
        ),
        "scripts/sync_user_configs.py": (
            "def atomic_copy_file(",
            "def mirror_tree(",
            "mirror_tree(skill, destination)",
            "include: set[str] | None",
            "prune_stale: bool = True",
        ),
        "skills/svg-diagrams/SKILL.md": (
            "序号与标题第一行垂直居中对齐",
            "包含关系图",
            "SVG XML 有效",
        ),
        "skills/sysu-ppt/scripts/sysu_toolkit.R": (
            'default = list(file = "template.pptx"',
            'public_health = list(file = "template-公卫学院.pptx"',
            ".svg_aspect <- function(path)",
        ),
    }
    for relative, fragments in required.items():
        body = read(relative)
        for fragment in fragments:
            if fragment not in body:
                problems.append(f"{relative}: missing workflow contract {fragment!r}")

    forbidden = {
        "skills/project-init/scripts/init_project.R": (
            'system2("git", c("add"',
            'c("commit", "-m"',
            "Table0_flowchart",
        ),
        "skills/r-biostats/SKILL.md": ('source("../skills/',),
        "skills/r-biostats/references/result-summary-schema.md": (
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
        ),
        "scripts/sync_user_configs.py": (
            "safe_remove(destination, target, dry_run)",
            "shutil.copytree(skill, destination)",
        ),
        "skills/sysu-ppt/references/figure_snippets.R": (
            "flow_box <- function",
            "make_decision <- function",
        ),
    }
    for relative, fragments in forbidden.items():
        body = read(relative)
        for fragment in fragments:
            if fragment in body:
                problems.append(f"{relative}: forbidden workflow fragment {fragment!r}")

    with tempfile.TemporaryDirectory(prefix="epiclaude_sync_audit_") as directory:
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
            if list(target.rglob("*.epiclaude-*.tmp")):
                problems.append("sync mirror self-test: temporary files remain")
        except OSError as error:
            problems.append(f"sync mirror self-test failed: {error}")

    with tempfile.TemporaryDirectory(prefix="epiclaude_partial_sync_") as directory:
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
        (target / SKILL_MANIFEST).write_text(
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
            if not (target / "alpha" / "SKILL.md").is_file():
                problems.append("partial sync self-test: existing managed skill was removed")
        except OSError as error:
            problems.append(f"partial sync self-test failed: {error}")

    if problems:
        print("Workflow contract audit failed:")
        for problem in problems:
            print(f"- {problem}")
        return 1

    print("Workflow contract audit passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
