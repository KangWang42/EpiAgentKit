from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from hook_conflicts import reconcile_hook_conflicts


def command_group(matcher: str, *commands: str) -> dict:
    return {
        "matcher": matcher,
        "hooks": [{"type": "command", "command": command} for command in commands],
    }


class HookConflictTests(unittest.TestCase):
    def test_json_conflict_is_removed_with_its_unreferenced_script(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            client = home / ".claude"
            scripts = client / "hooks"
            scripts.mkdir(parents=True)
            conflict = scripts / "scan_ai_trace.py"
            custom = scripts / "custom_quality.py"
            conflict.write_text("# emoji AI trace BACKLOG.md\n", encoding="utf-8")
            custom.write_text("# unrelated\n", encoding="utf-8")
            settings = client / "settings.json"
            settings.write_text(
                json.dumps(
                    {
                        "model": "personal",
                        "hooks": {
                            "PostToolUse": [
                                command_group(
                                    "Edit|Write",
                                    f'python "{conflict}"',
                                    f'python "{custom}"',
                                )
                            ]
                        },
                    }
                ),
                encoding="utf-8",
            )

            report = reconcile_hook_conflicts(
                platform="claude",
                json_config=settings,
                hooks_dir=scripts,
                home=home,
                protected_names=set(),
                dry_run=False,
            )

            updated = json.loads(settings.read_text(encoding="utf-8"))
            commands = updated["hooks"]["PostToolUse"][0]["hooks"]
            self.assertEqual(updated["model"], "personal")
            self.assertEqual([item["command"] for item in commands], [f'python "{custom}"'])
            self.assertFalse(conflict.exists())
            self.assertTrue(custom.is_file())
            self.assertTrue(settings.with_name("settings.json.epiagentkit.bak").is_file())
            self.assertIsNotNone(report)
            self.assertTrue(report.is_file())

    def test_content_signature_detects_renamed_protection_hook(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            client = home / ".codex"
            scripts = client / "hooks"
            scripts.mkdir(parents=True)
            conflict = scripts / "legacy_guard.py"
            raw_marker = "raw" + "data"
            conflict.write_text(
                f"ROOT = '01_data/{raw_marker}'\nraw_roots = []\n", encoding="utf-8"
            )
            config = client / "hooks.json"
            config.write_text(
                json.dumps(
                    {
                        "hooks": {
                            "PreToolUse": [
                                command_group("apply_patch", f'python "{conflict}"')
                            ]
                        }
                    }
                ),
                encoding="utf-8",
            )

            reconcile_hook_conflicts(
                platform="codex",
                json_config=config,
                hooks_dir=scripts,
                home=home,
                protected_names=set(),
                dry_run=False,
            )

            updated = json.loads(config.read_text(encoding="utf-8"))
            self.assertEqual(updated["hooks"]["PreToolUse"], [])
            self.assertFalse(conflict.exists())

    def test_codex_inline_hooks_are_filtered_and_migrated_to_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            client = home / ".codex"
            scripts = client / "hooks"
            scripts.mkdir(parents=True)
            conflict = scripts / "check_r_syntax.py"
            custom = scripts / "custom_quality.py"
            conflict.write_text("Rscript -e 'parse(file=x)'\n", encoding="utf-8")
            custom.write_text("# unrelated\n", encoding="utf-8")
            inline = client / "config.toml"
            inline.write_text(
                "model = 'personal'\n\n"
                "[[hooks.PostToolUse]]\n"
                "matcher = 'apply_patch'\n"
                "[[hooks.PostToolUse.hooks]]\n"
                "type = 'command'\n"
                f"command = 'python \"{conflict}\"'\n"
                "[[hooks.PostToolUse.hooks]]\n"
                "type = 'command'\n"
                f"command = 'python \"{custom}\"'\n"
                "command_windows = 'py custom_quality.py'\n\n"
                "[hooks.state]\n\n"
                f"[hooks.state.'{inline}:post_tool_use:0:0']\n"
                "trusted_hash = 'sha256:old'\n\n"
                "[model_providers.local]\n"
                "name = 'local'\n",
                encoding="utf-8",
            )
            hooks_json = client / "hooks.json"

            reconcile_hook_conflicts(
                platform="codex",
                json_config=hooks_json,
                inline_config=inline,
                hooks_dir=scripts,
                home=home,
                protected_names=set(),
                dry_run=False,
            )

            text = inline.read_text(encoding="utf-8")
            migrated = json.loads(hooks_json.read_text(encoding="utf-8"))
            handlers = migrated["hooks"]["PostToolUse"][0]["hooks"]
            self.assertNotIn("[[hooks.PostToolUse]]", text)
            self.assertNotIn("post_tool_use:0:0", text)
            self.assertIn("model = 'personal'", text)
            self.assertIn("[model_providers.local]", text)
            self.assertEqual([item["command"] for item in handlers], [f'python "{custom}"'])
            self.assertEqual(handlers[0]["commandWindows"], "py custom_quality.py")
            self.assertNotIn("command_windows", handlers[0])
            self.assertFalse(conflict.exists())
            self.assertTrue(custom.is_file())
            self.assertTrue(inline.with_name("config.toml.epiagentkit.bak").is_file())

    def test_dry_run_changes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            client = home / ".codex"
            scripts = client / "hooks"
            scripts.mkdir(parents=True)
            conflict = scripts / "fig_selfcheck.py"
            conflict.write_text("# 04_figures publication-figures\n", encoding="utf-8")
            config = client / "hooks.json"
            config.write_text(
                json.dumps(
                    {
                        "hooks": {
                            "PostToolUse": [command_group("Bash", f'python "{conflict}"')]
                        }
                    }
                ),
                encoding="utf-8",
            )
            before = config.read_bytes()

            report = reconcile_hook_conflicts(
                platform="codex",
                json_config=config,
                hooks_dir=scripts,
                home=home,
                protected_names=set(),
                dry_run=True,
            )

            self.assertEqual(config.read_bytes(), before)
            self.assertTrue(conflict.is_file())
            self.assertFalse(report.exists())

    def test_same_script_outside_authoritative_event_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            client = home / ".codex"
            scripts = client / "hooks"
            scripts.mkdir(parents=True)
            script = scripts / "scan_ai_trace.py"
            script.write_text("# emoji AI trace BACKLOG.md\n", encoding="utf-8")
            config = client / "hooks.json"
            config.write_text(
                json.dumps(
                    {
                        "hooks": {
                            "SessionStart": [command_group("startup", f'python "{script}"')]
                        }
                    }
                ),
                encoding="utf-8",
            )

            report = reconcile_hook_conflicts(
                platform="codex",
                json_config=config,
                hooks_dir=scripts,
                home=home,
                protected_names=set(),
                dry_run=False,
            )

            self.assertIsNone(report)
            self.assertTrue(script.is_file())


if __name__ == "__main__":
    unittest.main()
