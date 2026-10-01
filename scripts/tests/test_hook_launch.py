import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from sync_user_configs import hook_command, hook_groups  # noqa: E402


class HookLaunchTests(unittest.TestCase):
    def test_claude_windows_hooks_run_directly_in_bash(self) -> None:
        command = hook_command(Path("C:/Users/u/.claude/hooks"), "post_bash_checks.sh", client="claude", windows=True)
        self.assertEqual(
            command,
            "EPIAGENTKIT_HOOK_CLIENT=claude PYTHONUTF8=1 bash C:/Users/u/.claude/hooks/post_bash_checks.sh",
        )
        entries = [
            hook
            for groups in hook_groups("claude", Path("C:/Users/u/.claude/hooks"), windows=True).values()
            for group in groups
            for hook in group["hooks"]
        ]
        self.assertTrue(entries)
        self.assertTrue(all(hook["shell"] == "bash" for hook in entries))

    def test_codex_windows_hooks_keep_cmd_launcher(self) -> None:
        command = hook_command(Path("C:/Users/u/.codex/hooks"), "post_bash_checks.sh", client="codex", windows=True)
        self.assertTrue(command.startswith('cmd.exe /d /s /c call "C:/Users/u/.codex/hooks/run_hook.cmd"'))
        entries = [
            hook
            for groups in hook_groups("codex", Path("C:/Users/u/.codex/hooks"), windows=True).values()
            for group in groups
            for hook in group["hooks"]
        ]
        self.assertTrue(all("shell" not in hook for hook in entries))

    def test_hook_scripts_pass_windows_paths_to_python(self) -> None:
        for script in (ROOT / "hooks").glob("*.sh"):
            text = script.read_text(encoding="utf-8")
            if "hook_dir=" in text:
                self.assertIn("pwd -W 2>/dev/null || pwd", text, script.name)
            self.assertNotIn('python "$(dirname "$0")', text, script.name)

    @unittest.skipUnless(os.name == "nt" and shutil.which("bash"), "Git Bash on Windows only")
    def test_generated_claude_command_runs_under_git_bash(self) -> None:
        command = hook_command(ROOT / "hooks", "post_bash_checks.sh", client="claude", windows=True)
        done = subprocess.run([shutil.which("bash"), "-c", command], cwd=ROOT, input=b"{}", capture_output=True)
        self.assertEqual(done.returncode, 0, done.stderr.decode("utf-8", "replace"))
        self.assertNotIn("can't open file", done.stderr.decode("utf-8", "replace"))


if __name__ == "__main__":
    unittest.main()
