from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from config_core import (  # noqa: E402
    AGY_HOOK_NAME,
    AGY_RULE_MAX_BYTES,
    INSTALL_MANIFEST,
    INSTALL_SCHEMA,
    LOCAL_RULES_PRESERVE_FILE,
    PROJECT_NAME,
    RULE_MANIFEST,
    render_agy_rule_files,
)
from epiagentkit import check_platform, main as cli_main  # noqa: E402
from hook_conflicts import reconcile_hook_conflicts  # noqa: E402
from sync_user_configs import (  # noqa: E402
    MANAGED_HOOK_SCRIPTS,
    REGISTERED_HOOK_SCRIPTS,
    hook_command,
    hook_groups,
    main as sync_main,
    sync_agy_rules,
    sync_hook_config,
)


def strip_frontmatter(text: str) -> str:
    match = re.match(r"^---\n.*?\n---\n\n", text, flags=re.DOTALL)
    assert match is not None, f"Missing YAML frontmatter: {text[:80]!r}"
    return text[match.end() :]


def run_agy_hook(
    script: Path,
    process_cwd: Path,
    payload: dict,
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    if extra_env:
        env.update(extra_env)
    raw = json.dumps(payload, ensure_ascii=False)
    if os.name == "nt":
        wrapper = ROOT / "hooks" / "run_hook.cmd"
        command: str | list[str] = (
            f'cmd.exe /d /s /c call "{wrapper}" "{script}" "agy"'
        )
    else:
        env["EPIAGENTKIT_HOOK_CLIENT"] = "agy"
        command = ["bash", str(script)]
    return subprocess.run(
        command,
        cwd=process_cwd,
        input=raw,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )


class AgyRuleRenderingTests(unittest.TestCase):
    def test_real_claude_md_splits_losslessly_within_24kb_limit(self) -> None:
        source = (ROOT / "CLAUDE.md").read_text(encoding="utf-8-sig")
        rendered = render_agy_rule_files(source)
        self.assertGreaterEqual(len(rendered), 2)
        for name, content in rendered.items():
            self.assertTrue(name.startswith("epiagentkit-rules-"))
            self.assertIn("trigger: always_on\n", content)
            self.assertLessEqual(
                len(content.encode("utf-8")),
                AGY_RULE_MAX_BYTES,
                f"{name} exceeds {AGY_RULE_MAX_BYTES} bytes",
            )
        reconstructed = "".join(strip_frontmatter(content) for content in rendered.values())
        expected = source.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff")
        if expected and not expected.endswith("\n"):
            expected += "\n"
        self.assertEqual(reconstructed, expected)

    def test_sync_agy_rules_prunes_stale_parts_and_preserves_personal_rules(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / "CLAUDE.md"
            rules_dir = base / "rules"
            rules_dir.mkdir()
            personal = rules_dir / "personal.md"
            personal.write_text("---\ntrigger: always_on\n---\n\nkeep\n", encoding="utf-8")

            source.write_text((ROOT / "CLAUDE.md").read_text(encoding="utf-8"), encoding="utf-8")
            sync_agy_rules(source, rules_dir, dry_run=False)
            first_manifest = json.loads((rules_dir / RULE_MANIFEST).read_text(encoding="utf-8"))
            self.assertGreaterEqual(len(first_manifest["managed"]), 2)

            source.write_text("# Short Rules\n\n## 1. Rule\n\nKeep it short.\n", encoding="utf-8")
            sync_agy_rules(source, rules_dir, dry_run=False)
            second_manifest = json.loads((rules_dir / RULE_MANIFEST).read_text(encoding="utf-8"))
            self.assertEqual(second_manifest["managed"], ["epiagentkit-rules-01.md"])
            self.assertFalse((rules_dir / "epiagentkit-rules-02.md").exists())
            self.assertTrue(personal.is_file())


class AgyHookConfigTests(unittest.TestCase):
    def test_agy_hook_groups_use_named_schema_and_no_unsupported_fields(self) -> None:
        groups = hook_groups("agy", Path("C:/Users/u/.gemini/config/hooks"), windows=True)
        self.assertEqual(set(groups), {"PreToolUse", "PostToolUse"})
        edit_matcher = groups["PreToolUse"][0]["matcher"]
        for tool in (
            "write_file",
            "edit_file",
            "write_to_file",
            "replace_file_content",
            "multi_replace_file_content",
        ):
            self.assertIn(tool, edit_matcher)
        bash_matcher = groups["PostToolUse"][1]["matcher"]
        self.assertEqual(bash_matcher, "run_command")
        for event_groups in groups.values():
            for group in event_groups:
                for handler in group["hooks"]:
                    self.assertEqual(set(handler), {"type", "command", "timeout"})
                    self.assertIn('"agy"', handler["command"])

    def test_sync_hook_config_preserves_personal_named_hooks_and_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            hooks_dir = base / "hooks"
            hooks_dir.mkdir()
            config_path = base / "hooks.json"
            original = {
                "my-linter": {
                    "PostToolUse": [
                        {
                            "matcher": "run_command",
                            "hooks": [{"type": "command", "command": "echo lint", "timeout": 10}],
                        }
                    ]
                }
            }
            config_path.write_text(json.dumps(original), encoding="utf-8")

            sync_hook_config("agy", config_path, hooks_dir, dry_run=False, windows=True)
            first = json.loads(config_path.read_text(encoding="utf-8"))
            sync_hook_config("agy", config_path, hooks_dir, dry_run=False, windows=True)
            second = json.loads(config_path.read_text(encoding="utf-8"))

            self.assertEqual(first, second)
            self.assertEqual(first["my-linter"], original["my-linter"])
            self.assertIn(AGY_HOOK_NAME, first)
            commands = [
                handler["command"]
                for groups in first[AGY_HOOK_NAME].values()
                for group in groups
                for handler in group["hooks"]
            ]
            for script in REGISTERED_HOOK_SCRIPTS:
                self.assertEqual(sum(script in cmd for cmd in commands), 1)
            for legacy in MANAGED_HOOK_SCRIPTS - REGISTERED_HOOK_SCRIPTS:
                self.assertFalse(any(legacy in cmd for cmd in commands))
            self.assertTrue(config_path.with_name("hooks.json.epiagentkit.bak").is_file())

    def test_reconcile_hook_conflicts_handles_agy_named_schema(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            agy_home = home / ".gemini" / "config"
            scripts = agy_home / "hooks"
            scripts.mkdir(parents=True)
            conflict = scripts / "legacy_raw_guard.py"
            custom = scripts / "custom_lint.py"
            raw_word = "raw" + "data"
            conflict.write_text(
                f"ROOT = '01_data/{raw_word}'\nraw_roots = []\n", encoding="utf-8"
            )
            custom.write_text("# custom linter\n", encoding="utf-8")
            config = agy_home / "hooks.json"
            config.write_text(
                json.dumps(
                    {
                        "legacy-guard": {
                            "PreToolUse": [
                                {
                                    "matcher": "write_file|edit_file",
                                    "hooks": [
                                        {"type": "command", "command": f'python "{conflict}"'}
                                    ],
                                }
                            ]
                        },
                        "personal-lint": {
                            "PostToolUse": [
                                {
                                    "matcher": "run_command",
                                    "hooks": [
                                        {"type": "command", "command": f'python "{custom}"'}
                                    ],
                                }
                            ]
                        },
                    }
                ),
                encoding="utf-8",
            )

            report = reconcile_hook_conflicts(
                platform="agy",
                json_config=config,
                hooks_dir=scripts,
                home=home,
                protected_names=set(),
                dry_run=False,
            )

            self.assertIsNotNone(report)
            self.assertTrue(report.is_file())
            updated = json.loads(config.read_text(encoding="utf-8"))
            self.assertNotIn("legacy-guard", updated)
            self.assertIn("personal-lint", updated)
            self.assertFalse(conflict.exists())
            self.assertTrue(custom.is_file())


class AgyHookRuntimeTests(unittest.TestCase):
    def test_pre_tool_use_rawdata_guard_with_agy_payload_and_separate_process_cwd(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            hook_cwd = base / "config_dir"
            project = base / "research_project"
            hook_cwd.mkdir()
            (project / "01_data" / "rawdata").mkdir(parents=True)
            (project / "06_results").mkdir(parents=True)
            raw_hook = ROOT / "hooks" / "protect_rawdata.sh"

            # CLI write_file uses Path; IDE replace_file_content uses TargetFile.
            for args in (
                {"Path": "01_data/rawdata/cohort.csv"},
                {"TargetFile": str(project / "01_data" / "rawdata" / "cohort.csv")},
            ):
                denied = run_agy_hook(
                    raw_hook,
                    hook_cwd,
                    {
                        "cwd": str(project),
                        "workspacePaths": [str(project)],
                        "toolCall": {"name": "write_file", "args": args},
                    },
                )
                self.assertEqual(denied.returncode, 0, denied.stderr)
                decision = json.loads(denied.stdout)
                self.assertEqual(decision.get("decision"), "deny")
                self.assertIn("只读原始数据根", decision.get("reason", ""))

            allowed = run_agy_hook(
                raw_hook,
                hook_cwd,
                {
                    "cwd": str(project),
                    "workspacePaths": [str(project)],
                    "toolCall": {
                        "name": "write_file",
                        "args": {"Path": "06_results/summary.xlsx"},
                    },
                },
            )
            self.assertEqual(allowed.returncode, 0, allowed.stderr)
            self.assertEqual(json.loads(allowed.stdout), {"decision": "allow"})

    def test_post_edit_and_post_bash_hooks_honor_agy_contract(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            hook_cwd = base / "config_dir"
            project = base / "research_project"
            state = base / "state"
            hook_cwd.mkdir()
            (project / "02_code").mkdir(parents=True)
            (project / "04_figures").mkdir(parents=True)
            good_r = project / "02_code" / "01_ok.R"
            bad_md = project / "report.md"
            good_r.write_text("x <- 1\n", encoding="utf-8")
            bad_md.write_text("作为AI助手，我为你生成了以下内容。\n", encoding="utf-8")

            edit_hook = ROOT / "hooks" / "post_edit_checks.sh"
            ok_edit = run_agy_hook(
                edit_hook,
                hook_cwd,
                {
                    "cwd": str(project),
                    "toolCall": {"name": "edit_file", "args": {"Path": "02_code/01_ok.R"}},
                },
            )
            self.assertEqual(ok_edit.returncode, 0, ok_edit.stderr)
            self.assertEqual(json.loads(ok_edit.stdout), {})

            bad_edit = run_agy_hook(
                edit_hook,
                hook_cwd,
                {
                    "cwd": str(project),
                    "toolCall": {"name": "write_file", "args": {"Path": "report.md"}},
                },
            )
            self.assertEqual(bad_edit.returncode, 2)
            self.assertIn("过程痕迹", bad_edit.stderr)

            fig = project / "04_figures" / "Fig1_km.png"
            fig.write_bytes(b"v1")
            bash_hook = ROOT / "hooks" / "post_bash_checks.sh"
            env = {"EPIAGENTKIT_STATE_HOME": str(state)}
            payload = {
                "cwd": str(project),
                "toolCall": {"name": "run_command", "args": {"CommandLine": "Rscript run.R"}},
            }
            baseline = run_agy_hook(bash_hook, hook_cwd, payload, extra_env=env)
            self.assertEqual(baseline.returncode, 0, baseline.stderr)
            self.assertEqual(json.loads(baseline.stdout), {})
            self.assertEqual(baseline.stderr.strip(), "")

            fig.write_bytes(b"v2-updated")
            changed = run_agy_hook(bash_hook, hook_cwd, payload, extra_env=env)
            self.assertEqual(changed.returncode, 0, changed.stderr)
            self.assertEqual(json.loads(changed.stdout), {})
            self.assertIn("Fig1_km.png", changed.stderr)

    @unittest.skipUnless(os.name == "nt", "Windows cmd.exe launcher check")
    def test_generated_agy_windows_command_runs_via_cmd_c(self) -> None:
        command = hook_command(ROOT / "hooks", "post_bash_checks.sh", client="agy", windows=True)
        done = subprocess.run(
            f"cmd.exe /c {command}",
            cwd=ROOT,
            input="{}",
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(json.loads(done.stdout), {})


class AgyEndToEndInstallTests(unittest.TestCase):
    def test_install_sync_doctor_and_duplicate_root_check_for_agy(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "home"
            repo = Path(directory) / "repo"
            (repo / "skills").mkdir(parents=True)
            shutil.copy2(ROOT / "CLAUDE.md", repo / "CLAUDE.md")
            shutil.copytree(
                ROOT / "scripts",
                repo / "scripts",
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "tests"),
            )
            shutil.copytree(ROOT / "hooks", repo / "hooks")
            shutil.copytree(
                ROOT / "skills" / "academic-humanizer",
                repo / "skills" / "academic-humanizer",
            )
            personal_gemini = home / ".gemini" / "GEMINI.md"
            personal_gemini.parent.mkdir(parents=True)
            personal_gemini.write_text("# Personal Gemini Rules\n", encoding="utf-8")

            rc = cli_main(
                [
                    "install",
                    "--target",
                    "agy",
                    "--preset",
                    "custom",
                    "--skills",
                    "academic-humanizer",
                    "--with-rules",
                    "--with-hooks",
                    "--yes",
                    "--repo-root",
                    str(repo),
                    "--home",
                    str(home),
                ]
            )
            self.assertEqual(rc, 0)
            self.assertEqual(
                personal_gemini.read_text(encoding="utf-8"),
                "# Personal Gemini Rules\n",
            )
            agy_home = home / ".gemini" / "config"
            self.assertTrue((agy_home / INSTALL_MANIFEST).is_file())
            self.assertTrue((agy_home / "rules" / "epiagentkit-rules-01.md").is_file())
            self.assertTrue((agy_home / "skills" / "academic-humanizer" / "SKILL.md").is_file())
            self.assertTrue((agy_home / "hooks.json").is_file())

            # Duplicate skill in CLI-only discovery root must make doctor fail.
            dup = home / ".gemini" / "antigravity-cli" / "skills" / "academic-humanizer"
            shutil.copytree(repo / "skills" / "academic-humanizer", dup)
            rc_dup = cli_main(
                [
                    "doctor",
                    "--target",
                    "agy",
                    "--repo-root",
                    str(repo),
                    "--home",
                    str(home),
                ]
            )
            self.assertEqual(rc_dup, 1)

    def test_runtime_component_rejects_agy_only_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            (repo / "skills").mkdir(parents=True)
            (repo / "hooks").mkdir()
            (repo / "CLAUDE.md").write_text("rules\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "applies only to Codex"):
                sync_main(
                    [
                        "--target",
                        "agy",
                        "--repo-root",
                        str(repo),
                        "--components",
                        "runtime",
                    ]
                )

    def test_doctor_reports_preserved_agy_rules_drift_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            repo = base / "repo"
            agy_home = base / "agy"
            repo.mkdir()
            agy_home.mkdir()
            (repo / LOCAL_RULES_PRESERVE_FILE).touch()
            (repo / "CLAUDE.md").write_text("# Rules\n", encoding="utf-8")
            (agy_home / INSTALL_MANIFEST).write_text(
                json.dumps(
                    {
                        "schema": INSTALL_SCHEMA,
                        "project": PROJECT_NAME,
                        "platform": "agy",
                        "components": [],
                    }
                ),
                encoding="utf-8",
            )
            checks = check_platform("agy", repo, agy_home, [])
            preserved = [c for c in checks if c["item"] == "agy.rules.preserved"]
            self.assertEqual(len(preserved), 1)
            self.assertEqual(preserved[0]["status"], "WARN")
            self.assertFalse(any(c["status"] == "FAIL" for c in checks))


if __name__ == "__main__":
    unittest.main()
