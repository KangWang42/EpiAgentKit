#!/usr/bin/env python3
"""Audit cross-skill workflow contracts that are easy to regress."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from config_core import (
    LEGACY_HOOK_MANIFEST,
    LEGACY_INSTALL_MANIFEST,
    LEGACY_SKILL_MANIFEST,
)
from sync_user_configs import (
    MANAGED_HOOK_SCRIPTS,
    REGISTERED_HOOK_SCRIPTS,
    SKILL_MANIFEST,
    hook_command,
    mirror_tree,
    sync_hook_config,
    sync_skills,
)


ROOT = Path(__file__).resolve().parents[1]
LINE_BUDGET = 200


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def snapshot_tree(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file()
    }


def run_epiagentkit(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts/epiagentkit.py"), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def run_hook_script(
    script: Path,
    cwd: Path,
    payload: str = "{}",
    environment: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if environment:
        env.update(environment)
    if os.name == "nt":
        wrapper = ROOT / "hooks" / "run_hook.cmd"
        command: str | list[str] = (
            f'cmd.exe /d /s /c call "{wrapper}" "{script}" "claude"'
        )
    else:
        command = ["bash", str(script)]
        env["EPIAGENTKIT_HOOK_CLIENT"] = "claude"
    return subprocess.run(
        command,
        cwd=cwd,
        input=payload,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )


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
            "def sync_hook_config(",
            'hooks_dir / "run_hook.cmd"',
            "mirror_tree(skill, destination)",
            "include: set[str] | None",
            "prune_stale: bool = True",
            "def update_install_manifest(",
        ),
        "scripts/config_core.py": (
            'PROJECT_NAME = "EpiAgentKit"',
            'INSTALL_MANIFEST = ".epiagentkit-install.json"',
            "def resolve_codex_skill_dirs(",
            'layout == "both"',
        ),
        "scripts/configure_user.py": (
            "from config_core import PRESETS",
            '"doctor"',
            '"--skip-doctor"',
        ),
        "scripts/epiagentkit.py": (
            "def tree_matches(",
            "def run_doctor(",
            'command == "install"',
            'command == "sync"',
        ),
        "scripts/epiclaude.py": ("from epiagentkit import main",),
        "hooks/_emit_notice.py": (
            '"hookEventName": "PostToolUse"',
            '"additionalContext": message',
            '"systemMessage": message',
        ),
        "hooks/fig_selfcheck.sh": ('_emit_notice.py"',),
        "hooks/check_results_rds.sh": ('_emit_notice.py"',),
        "hooks/post_edit_checks.sh": (
            'run_check "check_r_syntax.sh"',
            'run_check "scan_ai_trace.sh"',
        ),
        "hooks/post_bash_checks.sh": (
            'collect_notice "fig_selfcheck.sh"',
            'collect_notice "check_results_rds.sh"',
            '_emit_notice.py"',
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
            ".validate_meeting_deck <- function(ppt)",
            'genre = c("meeting", "formal")',
            "组会 PPT 禁止目录页",
            "组会 PPT 禁止章节分隔/过渡页",
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
        "scripts/configure_user.py": (
            "PRESETS = {",
            "DEPENDENCIES = {",
            "def csv_values(",
        ),
        "skills/sysu-ppt/references/figure_snippets.R": (
            "flow_box <- function",
            "make_decision <- function",
        ),
        "skills/sysu-ppt/references/deck_skeleton.R": (
            'ppt <- sysu_add_section(',
            'sysu_add_text(ppt, "目录"',
            'genre = "formal"',
        ),
    }
    for relative, fragments in forbidden.items():
        body = read(relative)
        for fragment in fragments:
            if fragment in body:
                problems.append(f"{relative}: forbidden workflow fragment {fragment!r}")

    with tempfile.TemporaryDirectory(prefix="epiagentkit_sync_audit_") as directory:
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
            if list(target.rglob(".epi-*.tmp")):
                problems.append("sync mirror self-test: temporary files remain")
        except OSError as error:
            problems.append(f"sync mirror self-test failed: {error}")

    with tempfile.TemporaryDirectory(prefix="epiagentkit_partial_sync_") as directory:
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
        (target / LEGACY_SKILL_MANIFEST).write_text(
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
            if (target / LEGACY_SKILL_MANIFEST).exists():
                problems.append("partial sync self-test: legacy manifest was not migrated")
            if not (target / "alpha" / "SKILL.md").is_file():
                problems.append("partial sync self-test: existing managed skill was removed")
        except OSError as error:
            problems.append(f"partial sync self-test failed: {error}")

    with tempfile.TemporaryDirectory(prefix="epiagentkit_hook_sync_") as directory:
        test_root = Path(directory)
        hooks_dir = test_root / ".claude" / "hooks"
        config_path = test_root / ".claude" / "settings.json"
        hooks_dir.mkdir(parents=True)
        original = {
            "model": "custom-model",
            "hooks": {
                "PostToolUse": [
                    {
                        "matcher": "Bash",
                        "hooks": [
                            {
                                "type": "command",
                                "command": "custom-quality-check",
                            },
                            {
                                "type": "command",
                                "command": "bash ~/.claude/hooks/fig_selfcheck.sh",
                            },
                        ],
                    }
                ]
            },
        }
        config_path.write_text(
            json.dumps(original, ensure_ascii=False), encoding="utf-8"
        )
        try:
            sync_hook_config(
                "claude", config_path, hooks_dir, dry_run=False, windows=True
            )
            first = json.loads(config_path.read_text(encoding="utf-8"))
            sync_hook_config(
                "claude", config_path, hooks_dir, dry_run=False, windows=True
            )
            second = json.loads(config_path.read_text(encoding="utf-8"))
            commands = [
                hook.get("command", "")
                for groups in second.get("hooks", {}).values()
                for group in groups
                if isinstance(group, dict)
                for hook in group.get("hooks", [])
                if isinstance(hook, dict)
            ]
            managed = [
                command
                for command in commands
                if any(name in command for name in MANAGED_HOOK_SCRIPTS)
            ]
            registered = [
                command
                for command in commands
                if any(name in command for name in REGISTERED_HOOK_SCRIPTS)
            ]
            legacy = MANAGED_HOOK_SCRIPTS - REGISTERED_HOOK_SCRIPTS
            if first != second:
                problems.append("hook sync self-test: repeated install is not idempotent")
            if second.get("model") != "custom-model" or "custom-quality-check" not in commands:
                problems.append("hook sync self-test: unrelated settings were not preserved")
            if len(managed) != len(REGISTERED_HOOK_SCRIPTS):
                problems.append("hook sync self-test: managed hook count is incorrect")
            if len(registered) != len(REGISTERED_HOOK_SCRIPTS):
                problems.append("hook sync self-test: registered hook count is incorrect")
            if any(any(name in command for name in legacy) for command in commands):
                problems.append("hook sync self-test: legacy checks remain separately registered")
            if any("run_hook.cmd" not in command for command in managed):
                problems.append("hook sync self-test: Windows hook bypasses run_hook.cmd")
            if any(not command.startswith("cmd.exe /d /s /c call ") for command in managed):
                problems.append("hook sync self-test: Windows hook is shell-dependent")
            if any('"claude"' not in command for command in managed):
                problems.append("hook sync self-test: client identity is not forwarded")
            if not config_path.with_name("settings.json.epiagentkit.bak").is_file():
                problems.append("hook sync self-test: config backup was not created")
            if not hook_command(hooks_dir, "fig_selfcheck.sh", windows=False).startswith(
                "EPIAGENTKIT_HOOK_CLIENT=claude bash "
            ):
                problems.append("hook sync self-test: POSIX command does not use bash")
        except (OSError, ValueError) as error:
            problems.append(f"hook sync self-test failed: {error}")

    with tempfile.TemporaryDirectory(prefix="epiagentkit_install_audit_") as directory:
        home = Path(directory)
        (home / ".epiclaude").mkdir()
        (home / ".epiclaude/state").write_text("legacy\n", encoding="utf-8")
        for platform, config_name in ((".claude", "settings.json"), (".codex", "hooks.json")):
            platform_home = home / platform
            (platform_home / "hooks").mkdir(parents=True)
            config_path = platform_home / config_name
            config_path.write_text(
                json.dumps({"model": "personal-model"}), encoding="utf-8"
            )
            config_path.with_name(f"{config_name}.epiclaude.bak").write_text(
                "legacy backup\n", encoding="utf-8"
            )
            (platform_home / "hooks" / "custom.sh").write_text(
                "#!/usr/bin/env bash\n", encoding="utf-8"
            )
            (platform_home / LEGACY_INSTALL_MANIFEST).write_text(
                '{"components": [], "skills": [], "skill_dirs": []}\n',
                encoding="utf-8",
            )
            (platform_home / "hooks" / LEGACY_HOOK_MANIFEST).write_text(
                '{"managed": []}\n', encoding="utf-8"
            )

        install = [
            "install",
            "--target",
            "all",
            "--preset",
            "custom",
            "--skills",
            "academic-humanizer",
            "--with-rules",
            "--with-hooks",
            "--yes",
            "--home",
            str(home),
            "--codex-layout",
            "both",
        ]

        first = run_epiagentkit(install)
        if first.returncode:
            problems.append(
                "dual-platform install self-test failed: "
                + (first.stdout + first.stderr).strip()
            )
        else:
            expected_paths = (
                home / ".claude/CLAUDE.md",
                home / ".codex/AGENTS.md",
                home / ".claude/skills/academic-humanizer/SKILL.md",
                home / ".agents/skills/academic-humanizer/SKILL.md",
                home / ".codex/skills/academic-humanizer/SKILL.md",
                home / ".claude/.epiagentkit-install.json",
                home / ".codex/.epiagentkit-install.json",
                home / ".epiagentkit/state",
                home / ".claude/settings.json.epiagentkit.bak",
                home / ".codex/hooks.json.epiagentkit.bak",
            )
            missing = [str(path) for path in expected_paths if not path.is_file()]
            if missing:
                problems.append(
                    "dual-platform install self-test: missing files: " + ", ".join(missing)
                )
            legacy = [
                path
                for platform in (home / ".claude", home / ".codex")
                for path in (
                    platform / LEGACY_INSTALL_MANIFEST,
                    platform / "hooks" / LEGACY_HOOK_MANIFEST,
                )
                if path.exists()
            ]
            legacy.extend(home.glob("*/**/*.epiclaude.bak"))
            if (home / ".epiclaude").exists():
                legacy.append(home / ".epiclaude")
            if legacy:
                problems.append(
                    "dual-platform install self-test: legacy manifests remain: "
                    + ", ".join(map(str, legacy))
                )

            for config_path in (home / ".claude/settings.json", home / ".codex/hooks.json"):
                config = json.loads(config_path.read_text(encoding="utf-8"))
                if config.get("model") != "personal-model":
                    problems.append(
                        f"dual-platform install self-test: personal config changed: {config_path}"
                    )

            before = snapshot_tree(home)
            second = run_epiagentkit(install)
            if second.returncode:
                problems.append(
                    "dual-platform reinstall self-test failed: "
                    + (second.stdout + second.stderr).strip()
                )
            elif snapshot_tree(home) != before:
                problems.append("dual-platform reinstall self-test: install is not idempotent")

            doctor = run_epiagentkit(
                [
                    "doctor",
                    "--target",
                    "all",
                    "--home",
                    str(home),
                    "--codex-layout",
                    "both",
                    "--json",
                ]
            )
            try:
                doctor_payload = json.loads(doctor.stdout)
            except json.JSONDecodeError:
                doctor_payload = {}
            if doctor.returncode or not doctor_payload.get("ok"):
                problems.append(
                    "dual-platform doctor self-test failed: "
                    + (doctor.stdout + doctor.stderr).strip()
                )

    notice_helper = ROOT / "hooks" / "_emit_notice.py"
    for client, expected_key in (("claude", "hookSpecificOutput"), ("codex", "systemMessage")):
        environment = os.environ.copy()
        environment["EPIAGENTKIT_HOOK_CLIENT"] = client
        result = subprocess.run(
            [sys.executable, str(notice_helper)],
            input="quality reminder",
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=environment,
        )
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            payload = {}
        if result.returncode or expected_key not in payload:
            problems.append(f"hook notice self-test: invalid {client} success payload")

    with tempfile.TemporaryDirectory(prefix="epiagentkit_hook_aggregate_") as directory:
        project = Path(directory) / "project"
        state = Path(directory) / "state"
        code = project / "02_code"
        figures = project / "04_figures"
        results = project / "06_results"
        code.mkdir(parents=True)
        figures.mkdir()
        results.mkdir()
        good_r = code / "01_good.R"
        bad_r = code / "02_bad.R"
        bad_text = project / "report.md"
        good_r.write_text("x <- 1\n", encoding="utf-8")
        bad_r.write_text("x <-\n", encoding="utf-8")
        bad_text.write_text("AI辅助\n", encoding="utf-8")
        (figures / "Fig1_test.png").write_bytes(b"png fixture")
        (results / "model.rds").write_bytes(b"rds fixture")

        edit_hook = ROOT / "hooks" / "post_edit_checks.sh"
        bash_hook = ROOT / "hooks" / "post_bash_checks.sh"

        def edit_payload(path: Path) -> str:
            return json.dumps({"tool_input": {"file_path": path.as_posix()}})

        good = run_hook_script(edit_hook, project, edit_payload(good_r))
        bad_syntax = run_hook_script(edit_hook, project, edit_payload(bad_r))
        bad_trace = run_hook_script(edit_hook, project, edit_payload(bad_text))
        if good.returncode or good.stdout.strip() or good.stderr.strip():
            problems.append("aggregate edit hook self-test: valid R file did not pass cleanly")
        if bad_syntax.returncode != 2 or "R 语法检查未过" not in bad_syntax.stderr:
            problems.append("aggregate edit hook self-test: R syntax failure was not preserved")
        if bad_trace.returncode != 2 or "生成过程痕迹" not in bad_trace.stderr:
            problems.append("aggregate edit hook self-test: text trace failure was not preserved")

        hook_env = {"EPIAGENTKIT_STATE_HOME": str(state)}
        combined = run_hook_script(bash_hook, project, environment=hook_env)
        repeated = run_hook_script(bash_hook, project, environment=hook_env)
        try:
            combined_payload = json.loads(combined.stdout)
            combined_message = combined_payload["hookSpecificOutput"]["additionalContext"]
        except (json.JSONDecodeError, KeyError, TypeError):
            combined_message = ""
        if (
            combined.returncode
            or "检测到新生成/修改的图" not in combined_message
            or "检测到 06_results/ 新写入 .rds" not in combined_message
        ):
            problems.append("aggregate Bash hook self-test: combined notice lost a check")
        if repeated.returncode or repeated.stdout.strip() or repeated.stderr.strip():
            problems.append("aggregate Bash hook self-test: repeated notice was not deduplicated")

    for skill_dir in (ROOT / "skills").iterdir():
        if not skill_dir.is_dir():
            continue
        for directory in (item for item in skill_dir.rglob("*") if item.is_dir()):
            if directory.parent != skill_dir and directory.name == directory.parent.name:
                problems.append(
                    "skill path audit: redundant repeated directory lengthens Windows path: "
                    + str(directory.relative_to(ROOT))
                )

    cmd_bytes = (ROOT / "hooks" / "run_hook.cmd").read_bytes()
    if b"\r\n" not in cmd_bytes or b"\n" in cmd_bytes.replace(b"\r\n", b""):
        problems.append("hook path audit: run_hook.cmd must use CRLF line endings")

    if problems:
        print("Workflow contract audit failed:")
        for problem in problems:
            print(f"- {problem}")
        return 1

    print("Workflow contract audit passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
