from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from config_core import (
    INSTALL_MANIFEST,
    INSTALL_SCHEMA,
    LOCAL_RULES_PRESERVE_FILE,
    PROJECT_NAME,
)
from epiagentkit import check_platform
from sync_user_configs import (
    main as sync_main,
    read_codex_login_shell_setting,
    sync_codex_runtime_settings,
)


class CodexRuntimeSettingTests(unittest.TestCase):
    def test_missing_config_is_created_without_fictional_shell_key(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / ".codex" / "config.toml"

            sync_codex_runtime_settings(config, dry_run=False)

            self.assertEqual(
                config.read_text(encoding="utf-8"),
                "allow_login_shell = false\n",
            )
            self.assertIs(read_codex_login_shell_setting(config), False)
            self.assertFalse(
                any(
                    line.strip().startswith("shell =")
                    for line in config.read_text(encoding="utf-8").splitlines()
                )
            )
            self.assertFalse(
                config.with_name("config.toml.epiagentkit.bak").exists()
            )

    def test_existing_config_is_updated_and_other_text_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "config.toml"
            original = (
                b"\xef\xbb\xbfallow_login_shell = true  # personal value\r\n"
                b"model = 'personal-model'\r\n\r\n"
                b"[model_providers.local]\r\nname = 'local'\r\n"
            )
            config.write_bytes(original)

            sync_codex_runtime_settings(config, dry_run=False)

            expected = original.replace(
                b"allow_login_shell = true", b"allow_login_shell = false", 1
            )
            self.assertEqual(config.read_bytes(), expected)
            self.assertEqual(
                config.with_name("config.toml.epiagentkit.bak").read_bytes(),
                original,
            )
            before_second = config.read_bytes()
            backup_before_second = config.with_name(
                "config.toml.epiagentkit.bak"
            ).read_bytes()
            sync_codex_runtime_settings(config, dry_run=False)
            self.assertEqual(config.read_bytes(), before_second)
            self.assertEqual(
                config.with_name("config.toml.epiagentkit.bak").read_bytes(),
                backup_before_second,
            )

    def test_missing_top_level_setting_is_prepended_without_changing_tables(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "config.toml"
            original = "# personal\n\n[sandbox]\nallow_login_shell = true\n"
            config.write_text(original, encoding="utf-8")

            sync_codex_runtime_settings(config, dry_run=False)

            updated = config.read_text(encoding="utf-8")
            self.assertEqual(
                updated,
                "allow_login_shell = false\n\n" + original,
            )
            self.assertIs(read_codex_login_shell_setting(config), False)

    def test_dry_run_has_zero_filesystem_difference(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "config.toml"
            original = b"allow_login_shell = true\nmodel = 'personal'\n"
            config.write_bytes(original)

            sync_codex_runtime_settings(config, dry_run=True)

            self.assertEqual(config.read_bytes(), original)
            self.assertFalse(
                config.with_name("config.toml.epiagentkit.bak").exists()
            )

    def test_invalid_or_ambiguous_toml_is_not_modified(self) -> None:
        cases = (
            "allow_login_shell = true\nallow_login_shell = false\n",
            "allow_login_shell = 'false'\n",
            "model = [\n",
        )
        with tempfile.TemporaryDirectory() as directory:
            for index, original in enumerate(cases):
                with self.subTest(index=index):
                    config = Path(directory) / f"config-{index}.toml"
                    config.write_text(original, encoding="utf-8")
                    before = config.read_bytes()
                    with self.assertRaises(ValueError):
                        sync_codex_runtime_settings(config, dry_run=False)
                    self.assertEqual(config.read_bytes(), before)
                    self.assertFalse(
                        config.with_name(
                            f"{config.name}.epiagentkit.bak"
                        ).exists()
                    )

    def test_doctor_checks_only_the_managed_setting_value(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "repo"
            codex_home = base / ".codex"
            root.mkdir()
            codex_home.mkdir()
            (root / "CLAUDE.md").write_text("rules\n", encoding="utf-8")
            (codex_home / "AGENTS.md").write_text("rules\n", encoding="utf-8")
            (codex_home / INSTALL_MANIFEST).write_text(
                json.dumps(
                    {
                        "schema": INSTALL_SCHEMA,
                        "project": PROJECT_NAME,
                        "platform": "codex",
                        "components": ["rules"],
                    }
                ),
                encoding="utf-8",
            )
            config = codex_home / "config.toml"
            config.write_text(
                "allow_login_shell = false\nmodel = 'private-name'\n",
                encoding="utf-8",
            )

            checks = check_platform("codex", root, codex_home, [])
            setting = next(
                check
                for check in checks
                if check["item"] == "codex.runtime.allow_login_shell"
            )
            self.assertEqual(setting["status"], "PASS")
            self.assertNotIn("private-name", setting["detail"])

            config.write_text("allow_login_shell = true\n", encoding="utf-8")
            checks = check_platform("codex", root, codex_home, [])
            setting = next(
                check
                for check in checks
                if check["item"] == "codex.runtime.allow_login_shell"
            )
            self.assertEqual(setting["status"], "FAIL")
            self.assertNotIn("true", setting["detail"])

    def test_only_codex_rule_sync_manages_the_runtime_setting(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "repo"
            home = base / "home"
            (root / "skills").mkdir(parents=True)
            (root / "hooks").mkdir()
            (root / "CLAUDE.md").write_text("rules\n", encoding="utf-8")
            config = home / ".codex" / "config.toml"
            config.parent.mkdir(parents=True)
            config.write_text("allow_login_shell = true\n", encoding="utf-8")

            sync_main(
                [
                    "--target",
                    "codex",
                    "--repo-root",
                    str(root),
                    "--home",
                    str(home),
                    "--components",
                    "skills",
                ]
            )
            self.assertIs(read_codex_login_shell_setting(config), True)

            sync_main(
                [
                    "--target",
                    "codex",
                    "--repo-root",
                    str(root),
                    "--home",
                    str(home),
                    "--components",
                    "rules",
                ]
            )
            self.assertIs(read_codex_login_shell_setting(config), False)
            self.assertEqual(
                (home / ".codex" / "AGENTS.md").read_text(encoding="utf-8"),
                "rules\n",
            )

    def test_local_rule_file_preservation_keeps_runtime_setting_managed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "repo"
            home = base / "home"
            (root / "skills").mkdir(parents=True)
            (root / "hooks").mkdir()
            (root / "CLAUDE.md").write_text("public rules\n", encoding="utf-8")
            (root / LOCAL_RULES_PRESERVE_FILE).write_text("\n", encoding="utf-8")
            codex_home = home / ".codex"
            codex_home.mkdir(parents=True)
            (codex_home / "AGENTS.md").write_text(
                "personal rules\n", encoding="utf-8"
            )
            config = codex_home / "config.toml"
            config.write_text("allow_login_shell = true\n", encoding="utf-8")

            sync_main(
                [
                    "--target",
                    "codex",
                    "--repo-root",
                    str(root),
                    "--home",
                    str(home),
                    "--components",
                    "rules",
                ]
            )

            self.assertEqual(
                (codex_home / "AGENTS.md").read_text(encoding="utf-8"),
                "personal rules\n",
            )
            self.assertIs(read_codex_login_shell_setting(config), False)
            manifest = json.loads(
                (codex_home / INSTALL_MANIFEST).read_text(encoding="utf-8")
            )
            self.assertIn("runtime", manifest["components"])
            self.assertNotIn("rules", manifest["components"])
            setting_check = next(
                check
                for check in check_platform("codex", root, codex_home, [])
                if check["item"] == "codex.runtime.allow_login_shell"
            )
            self.assertEqual(setting_check["status"], "PASS")

    def test_runtime_component_rejects_claude_only_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            (root / "skills").mkdir(parents=True)
            (root / "hooks").mkdir()
            (root / "CLAUDE.md").write_text("rules\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "applies only to Codex"):
                sync_main(
                    [
                        "--target",
                        "claude",
                        "--repo-root",
                        str(root),
                        "--components",
                        "runtime",
                    ]
                )


if __name__ == "__main__":
    unittest.main()
