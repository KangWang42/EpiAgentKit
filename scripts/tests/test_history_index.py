from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills" / "epiagentkit-maintenance" / "scripts" / "history_index.py"


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


class HistoryIndexTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.home = self.base / "home"
        self.cache = self.base / "cache"
        (self.home / ".claude").mkdir(parents=True)
        (self.home / ".codex").mkdir(parents=True)
        (self.home / ".gemini" / "antigravity-cli").mkdir(parents=True)

        self.cc_file = self.home / ".claude" / "history.jsonl"
        self.codex_file = self.home / ".codex" / "history.jsonl"
        self.agy_file = self.home / ".gemini" / "antigravity-cli" / "history.jsonl"

        self.cc_file.write_text(
            "\n".join([
                json.dumps({"display": "这个Excel表格不要加冻结窗格和筛选按钮，按原顺序保持干净", "timestamp": 1760000000000, "sessionId": "s1", "project": "E:/projA"}),
                json.dumps({"display": "继续", "timestamp": 1760000010000, "sessionId": "s1", "project": "E:/projA"}),
                json.dumps({"display": "我的token=supersecretvalue12345 还有 sk-abcdefghijklmnop 和 C:\\Users\\Alice\\secret.xlsx 不要泄露", "timestamp": 1760000020000, "sessionId": "s1", "project": "E:/projA"}),
            ]) + "\n",
            encoding="utf-8",
        )
        self.codex_file.write_text(
            json.dumps({"text": "网页顶部不要平铺一排大按钮，改简洁菜单，卡片等高对齐", "ts": 1760100000, "session_id": "cx1"}) + "\n",
            encoding="utf-8",
        )
        self.agy_file.write_text(
            json.dumps({"display": "我希望用高效增量索引和复用脚本来读取历史，不要每次硬来重扫", "timestamp": 1760200000000, "conversationId": "ag1", "workspace": "E:/EpiAgentKit"}) + "\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_incremental_sync_zero_byte_noop_and_delta_append(self) -> None:
        cc_before = self.cc_file.read_bytes()

        first = run_cli("--home", str(self.home), "--cache-dir", str(self.cache), "sync", "--json")
        self.assertEqual(first.returncode, 0, first.stderr)
        d1 = json.loads(first.stdout)
        self.assertEqual(d1["new_entries"], 5)
        self.assertEqual(d1["total_entries"], 5)
        self.assertGreater(d1["bytes_read"], 0)
        self.assertEqual(self.cc_file.read_bytes(), cc_before)

        second = run_cli("--home", str(self.home), "--cache-dir", str(self.cache), "sync", "--json")
        self.assertEqual(second.returncode, 0, second.stderr)
        d2 = json.loads(second.stdout)
        self.assertEqual(d2["new_entries"], 0)
        self.assertEqual(d2["bytes_read"], 0)
        self.assertEqual(d2["clients"]["cc"]["status"], "unchanged")

        extra = json.dumps({"text": "PPT里不要写内部文件名，保留我改过的文字", "ts": 1760300000, "session_id": "cx2"}) + "\n"
        with self.codex_file.open("a", encoding="utf-8", newline="\n") as fh:
            fh.write(extra)

        third = run_cli("--home", str(self.home), "--cache-dir", str(self.cache), "sync", "--json")
        self.assertEqual(third.returncode, 0, third.stderr)
        d3 = json.loads(third.stdout)
        self.assertEqual(d3["new_entries"], 1)
        self.assertEqual(d3["total_entries"], 6)
        self.assertEqual(d3["clients"]["codex"]["status"], "incremental")
        self.assertEqual(d3["clients"]["cc"]["status"], "unchanged")
        self.assertEqual(d3["bytes_read"], len(extra.encode("utf-8")))

    def test_redaction_noise_filtering_fts_search_and_checkpoints(self) -> None:
        sync = run_cli("--home", str(self.home), "--cache-dir", str(self.cache), "sync")
        self.assertEqual(sync.returncode, 0, sync.stderr)

        fb = run_cli("--home", str(self.home), "--cache-dir", str(self.cache), "feedback", "--json")
        self.assertEqual(fb.returncode, 0, fb.stderr)
        items = json.loads(fb.stdout)
        texts = [item["text"] for item in items]
        self.assertFalse(any(t == "继续" for t in texts))
        self.assertTrue(any("冻结窗格" in t for t in texts))

        search_secret = run_cli("--home", str(self.home), "--cache-dir", str(self.cache), "search", "泄露", "--json")
        self.assertEqual(search_secret.returncode, 0, search_secret.stderr)
        secret_items = json.loads(search_secret.stdout)
        self.assertEqual(len(secret_items), 1)
        self.assertNotIn("supersecretvalue12345", secret_items[0]["text"])
        self.assertNotIn("sk-abcdefghijklmnop", secret_items[0]["text"])
        self.assertNotIn("C:\\Users\\Alice\\", secret_items[0]["text"])
        self.assertIn("[REDACTED", secret_items[0]["text"])

        search_cjk = run_cli("--home", str(self.home), "--cache-dir", str(self.cache), "search", "增量索引", "--json")
        self.assertEqual(search_cjk.returncode, 0, search_cjk.stderr)
        cjk_items = json.loads(search_cjk.stdout)
        self.assertEqual(len(cjk_items), 1)
        self.assertEqual(cjk_items[0]["client"], "agy")

        mark = run_cli("--home", str(self.home), "--cache-dir", str(self.cache), "mark", "--note", "v1-distill")
        self.assertEqual(mark.returncode, 0, mark.stderr)

        with self.agy_file.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"display": "新反馈：回归分析不要自动追加逐步调整模型", "timestamp": 1760400000000, "conversationId": "ag2"}) + "\n")

        since_last = run_cli("--home", str(self.home), "--cache-dir", str(self.cache), "feedback", "--since-last", "--json")
        self.assertEqual(since_last.returncode, 0, since_last.stderr)
        new_items = json.loads(since_last.stdout)
        self.assertEqual(len(new_items), 1)
        self.assertIn("逐步调整模型", new_items[0]["text"])

    def test_refuses_cache_inside_skills_directory(self) -> None:
        bad_cache = ROOT / "skills" / "epiagentkit-maintenance" / "bad-cache"
        proc = run_cli("--home", str(self.home), "--cache-dir", str(bad_cache), "sync")
        self.assertNotEqual(proc.returncode, 0)
        self.assertFalse(bad_cache.exists())


if __name__ == "__main__":
    unittest.main()
