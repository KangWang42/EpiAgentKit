from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT / "skills/epiagentkit-maintenance/scripts/knowledge_index.py"
SPEC = importlib.util.spec_from_file_location("knowledge_index", HELPER)
index = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(index)


class KnowledgeIndexTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name) / "中文 目录"
        self.skills = self.base / "skills"
        self.reference = self.skills / "r-biostats/references/regression.md"
        self.reference.parent.mkdir(parents=True)
        (self.reference.parents[1] / "SKILL.md").write_text(
            '---\nname: r-biostats\ndescription: "回归分析与统计表"\n---\n# R 分析\n\n正文。\n',
            encoding="utf-8",
        )
        self.reference.write_text(
            "# 回归分析\n\n本文件用于回归模型。\n\n## 缺失数据\n\nLinear logistic regression.\n",
            encoding="utf-8",
        )
        other = self.skills / "docx"
        other.mkdir()
        (other / "SKILL.md").write_text(
            "---\nname: docx\ndescription: >-\n  编辑 Word 文件\n  和数据表格\n---\n# Word\n",
            encoding="utf-8",
        )
        self.catalog = index.Catalog(self.skills, self.base / "cache")

    @contextlib.contextmanager
    def prepared(self, **kwargs):
        connection, stats = self.catalog.prepare(**kwargs)
        try:
            yield connection, stats
        finally:
            connection.close()

    def search(self, query, skill=None, kind=None, limit=6):
        with self.prepared() as (connection, _):
            return self.catalog.search(connection, query, skill, kind, limit)

    def test_chinese_groups_do_not_match_generic_data(self):
        matches = self.search("缺失数据")
        self.assertEqual([item["path"] for item in matches], ["r-biostats/references/regression.md"])
        self.assertEqual(self.search("缺失数据", "docx"), [])
        self.assertEqual(self.search("missing-unknown"), [])

    def test_english_path_filter_and_limit(self):
        self.assertEqual(self.search("REGRESSION", kind="reference")[0]["path"],
                         "r-biostats/references/regression.md")
        self.assertEqual(len(self.search("回归 Word", limit=1)), 1)
        self.assertTrue(all(item["kind"] == "skill" for item in self.search("回归 Word", kind="skill")))

    def test_incremental_queries_do_not_read_unchanged_source_bodies(self):
        with self.prepared() as (_, stats):
            self.assertEqual(stats["updated"], 3)
        with patch.object(Path, "read_bytes", side_effect=AssertionError("unexpected body read")):
            with self.prepared() as (_, stats):
                self.assertEqual(stats, {"documents": 3, "updated": 0, "removed": 0})

    def test_add_edit_rename_delete_remove_old_search_records(self):
        self.search("缺失数据")
        self.reference.write_text("# 生存模型\n\nCox survival.\n", encoding="utf-8")
        self.assertEqual(self.search("缺失数据"), [])
        renamed = self.reference.with_name("survival.md")
        self.reference.rename(renamed)
        self.assertEqual(self.search("Cox")[0]["path"], "r-biostats/references/survival.md")
        renamed.unlink()
        self.assertEqual(self.search("Cox"), [])
        with self.prepared() as (connection, _):
            self.assertEqual(connection.execute("SELECT count(*) FROM search").fetchone()[0], 2)
            self.assertEqual(connection.execute("SELECT count(*) FROM documents").fetchone()[0], 2)

    def test_peek_reads_live_head_links_and_reports_truncation(self):
        self.reference.write_text(
            "# 回归\n\n[entry](../SKILL.md)\n[external](https://example.com)\n"
            "[outside](../../../../outside.md)\n", encoding="utf-8")
        with self.prepared() as (connection, _):
            peek = self.catalog.peek(connection, "r-biostats/references/regression.md", 1)
            self.assertEqual(peek["head"], "# 回归")
            self.assertTrue(peek["truncated"])
            self.assertEqual(peek["linked_documents"], ["r-biostats/SKILL.md"])
            self.assertEqual(len(peek["sha256"]), 64)

    def test_peek_rejects_changed_file_and_verify_repairs_it(self):
        with self.prepared() as (connection, _):
            self.reference.write_text("# 已变化\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "文件已变化"):
                self.catalog.peek(connection, "r-biostats/references/regression.md", 20)
        with self.prepared(verify=True) as (connection, stats):
            self.assertEqual(stats["updated"], 1)
            self.assertEqual(self.catalog.peek(connection, "r-biostats/references/regression.md", 20)["head"],
                             "# 已变化")

    def test_verify_catches_content_change_with_matching_cached_stat(self):
        with self.prepared() as (connection, _):
            self.reference.write_text("# 修改后的原文\n", encoding="utf-8")
            stat = self.reference.stat()
            connection.execute("UPDATE documents SET mtime=?,ctime=?,size=? WHERE path=?",
                               (stat.st_mtime_ns, stat.st_ctime_ns, stat.st_size,
                                "r-biostats/references/regression.md"))
            connection.commit()
        with self.prepared(verify=True) as (connection, stats):
            self.assertEqual(stats["updated"], 1)
            self.assertEqual(self.catalog.search(connection, "缺失数据", None, None, 6), [])

    def test_scope_excludes_assets_scripts_hidden_files_and_project_data(self):
        for relative in ("r-biostats/assets/sample.md", "r-biostats/scripts/notes.md",
                         "r-biostats/references/.private/a.md", ".hidden/SKILL.md",
                         "01_data/rawdata/private.md"):
            path = self.skills / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("private sentinel", encoding="utf-8")
        self.assertEqual(len(index.discover(self.skills)), 3)
        self.assertEqual(self.search("sentinel"), [])
        with self.prepared() as (connection, _):
            for relative in ("../outside.md", str(self.reference), "r-biostats/assets/sample.md"):
                with self.assertRaises(ValueError):
                    self.catalog.peek(connection, relative, 20)

    def test_symlink_files_and_directories_are_excluded(self):
        outside = self.base / "outside"
        outside.mkdir()
        (outside / "secret.md").write_text("secret", encoding="utf-8")
        try:
            (self.reference.parent / "linked").symlink_to(outside, target_is_directory=True)
            (self.reference.parent / "linked.md").symlink_to(outside / "secret.md")
        except OSError as error:
            self.skipTest(f"symlink creation unavailable: {error}")
        self.assertEqual(len(index.discover(self.skills)), 3)

    def test_corrupt_cache_fails_then_explicit_rebuild_recovers(self):
        self.search("缺失数据")
        self.catalog.path.write_bytes(b"not a SQLite database")
        with self.assertRaises(sqlite3.DatabaseError):
            self.catalog.prepare()
        with self.prepared(rebuild=True) as (connection, stats):
            self.assertEqual(stats["updated"], 3)
            self.assertEqual(len(self.catalog.search(connection, "缺失数据", None, None, 6)), 1)

    def test_failed_refresh_rolls_back_instead_of_returning_stale_candidates(self):
        self.search("缺失数据")
        new = self.reference.with_name("invalid.md")
        new.write_bytes(b"\xff\xfe")
        with self.assertRaises(UnicodeError):
            self.catalog.prepare()
        new.unlink()
        self.assertEqual(len(self.search("缺失数据")), 1)

    def test_rebuild_failure_preserves_existing_database(self):
        self.search("缺失数据")
        before = self.catalog.path.read_bytes()
        self.reference.write_bytes(b"\xff")
        with self.assertRaises(UnicodeError):
            self.catalog.prepare(rebuild=True)
        self.assertEqual(self.catalog.path.read_bytes(), before)
        self.assertEqual(list(self.catalog.cache_dir.glob(".skills-*")), [])

    def test_source_root_identity_and_cache_location(self):
        with self.assertRaisesRegex(ValueError, "之外"):
            index.Catalog(self.skills, self.skills / ".cache")
        self.search("缺失数据")
        other = self.base / "other-skills"
        shutil.copytree(self.skills, other)
        second = index.Catalog(other, self.catalog.cache_dir)
        self.assertNotEqual(second.path, self.catalog.path)
        with self.prepared() as (connection, _):
            connection.execute("UPDATE metadata SET root='wrong-root'")
            connection.commit()
        with self.assertRaisesRegex(ValueError, "来源目录不匹配"):
            self.catalog.prepare()

    def test_query_parameters_are_not_sql_or_fts_commands(self):
        self.search("\" OR 1=1; DROP TABLE documents; --")
        self.assertEqual(len(self.search("缺失数据")), 1)
        with self.assertRaises(ValueError):
            self.search("!!!")
        with self.assertRaises(ValueError):
            self.search("long " * 150)

    def test_metadata_uses_existing_headers_and_ignores_code_fences(self):
        source = "---\ndescription: >-\n  第一行\n  第二行\n---\n# 真实标题\n\n开头。\n\n```md\n# 假标题\n```\n## 章节\n"
        info = index.metadata(source, "x/SKILL.md")
        self.assertEqual(info["summary"], "第一行 第二行")
        self.assertEqual(info["headings"], ["真实标题", "章节"])
        self.assertEqual(info["summary_source"], "description")

    def test_installed_copy_uses_own_skill_root_from_other_working_directory(self):
        helper = self.skills / "epiagentkit-maintenance/scripts/knowledge_index.py"
        helper.parent.mkdir(parents=True)
        shutil.copy2(HELPER, helper)
        result = subprocess.run(
            [sys.executable, str(helper), "--cache-dir", str(self.base / "installed-cache"),
             "search", "缺失数据", "--skill", "r-biostats"], cwd=ROOT,
            capture_output=True, encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)
        self.assertEqual(output["root"], str(self.skills.resolve()))
        self.assertEqual(len(output["candidates"]), 1)

    def test_cli_error_does_not_emit_success_output(self):
        output, error = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
            status = index.main(["--root", str(self.skills), "--cache-dir", str(self.base / "cache"),
                                 "peek", "../secret.md"])
        self.assertEqual(status, 1)
        self.assertEqual(output.getvalue(), "")
        self.assertIn("error", json.loads(error.getvalue()))

    def test_repository_examples_find_expected_documents(self):
        catalog = index.Catalog(ROOT / "skills", self.base / "repo-cache")
        connection, _ = catalog.prepare()
        try:
            for skill, query, expected in (
                ("r-biostats", "缺失数据", "r-biostats/references/regression.md"),
                ("academic-humanizer", "修订", "academic-humanizer/references/revision-workflow.md"),
                ("biostat-principles", "依赖", "biostat-principles/references/runtime-dependencies.md"),
            ):
                with self.subTest(query=query):
                    self.assertIn(expected, [item["path"] for item in catalog.search(connection, query, skill, None, 6)])
        finally:
            connection.close()


if __name__ == "__main__":
    unittest.main()
