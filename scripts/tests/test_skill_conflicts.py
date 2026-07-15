from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from skill_conflicts import remove_skill_conflicts, scan_skill_conflicts


def write_skill(root: Path, name: str, description: str, body: str = "Instructions\n") -> Path:
    skill = root / name
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: |\n  {description}\n---\n\n{body}",
        encoding="utf-8",
    )
    return skill


class SkillConflictTests(unittest.TestCase):
    def test_research_visual_overlap_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / "repo"
            local = root / "home/.agents/skills"
            write_skill(repo / "skills", "research-visuals", "authoritative visuals")
            write_skill(local, "legacy-visuals", "生成跨载体科研视觉资产")

            conflicts = scan_skill_conflicts(
                platform="codex",
                source_root=repo,
                incoming={"research-visuals"},
                discovery_roots=[local],
                target_roots=[local],
            )

            self.assertEqual(len(conflicts), 1)
            self.assertEqual(conflicts[0].authority, "research-visuals")

    def test_semantic_overlap_is_detected_and_delegated_skill_is_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / "repo"
            local = root / "home/.agents/skills"
            write_skill(repo / "skills", "publication-figures", "authoritative figures")
            write_skill(local, "legacy-plotter", "处理任意科研出图和论文配图")
            write_skill(
                local,
                "journal-style-only",
                "仅当指定期刊样式时使用；常规论文配图默认走 publication-figures，不要用本 skill",
            )

            conflicts = scan_skill_conflicts(
                platform="codex",
                source_root=repo,
                incoming={"publication-figures"},
                discovery_roots=[local],
                target_roots=[local],
            )

            self.assertEqual([item.local_name for item in conflicts], ["legacy-plotter"])
            self.assertEqual(conflicts[0].kind, "semantic_overlap")
            self.assertEqual(conflicts[0].authority, "publication-figures")

    def test_modified_same_name_is_conflict_but_identical_target_is_not(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / "repo"
            target = root / "home/.agents/skills"
            source = write_skill(repo / "skills", "r-biostats", "R 统计分析")
            installed = write_skill(target, "r-biostats", "R 统计分析")

            no_conflicts = scan_skill_conflicts(
                platform="codex",
                source_root=repo,
                incoming={"r-biostats"},
                discovery_roots=[target],
                target_roots=[target],
            )
            self.assertEqual(no_conflicts, [])

            (installed / "local-note.md").write_text("personal change\n", encoding="utf-8")
            conflicts = scan_skill_conflicts(
                platform="codex",
                source_root=repo,
                incoming={"r-biostats"},
                discovery_roots=[target],
                target_roots=[target],
            )
            self.assertEqual(len(conflicts), 1)
            self.assertEqual(conflicts[0].kind, "exact_name")
            self.assertTrue(source.is_dir())

    def test_identical_copy_outside_target_is_duplicate_root_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / "repo"
            official = root / "home/.agents/skills"
            compatibility = root / "home/.codex/skills"
            write_skill(repo / "skills", "academic-humanizer", "去 AI 味")
            write_skill(compatibility, "academic-humanizer", "去 AI 味")

            conflicts = scan_skill_conflicts(
                platform="codex",
                source_root=repo,
                incoming={"academic-humanizer"},
                discovery_roots=[official, compatibility],
                target_roots=[official],
            )

            self.assertEqual(len(conflicts), 1)
            self.assertEqual(conflicts[0].kind, "duplicate_root")
            self.assertFalse(conflicts[0].target_root)

    def test_removal_deletes_skill_and_writes_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / "repo"
            home = root / "home"
            local = home / ".agents/skills"
            write_skill(repo / "skills", "publication-figures", "authoritative figures")
            old = write_skill(local, "legacy-plotter", "处理任意科研出图")
            (old / "notes.txt").write_text("keep me\n", encoding="utf-8")
            conflicts = scan_skill_conflicts(
                platform="codex",
                source_root=repo,
                incoming={"publication-figures"},
                discovery_roots=[local],
                target_roots=[local],
            )

            manifest = remove_skill_conflicts(
                conflicts,
                home=home,
                source_root=repo,
                dry_run=False,
                run_id="test-run",
            )

            self.assertIsNotNone(manifest)
            self.assertFalse(old.exists())
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertNotIn("backup_path", payload["conflicts"][0])
            self.assertEqual(payload["conflicts"][0]["action"], "deleted")

    def test_removal_defers_empty_windows_directory_locked_by_client(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / "repo"
            home = root / "home"
            local = home / ".agents/skills"
            write_skill(repo / "skills", "publication-figures", "authoritative figures")
            old = write_skill(local, "legacy-plotter", "处理任意科研出图")
            conflicts = scan_skill_conflicts(
                platform="codex",
                source_root=repo,
                incoming={"publication-figures"},
                discovery_roots=[local],
                target_roots=[local],
            )

            def locked_empty_tree(path: Path, onerror=None) -> None:
                for child in path.iterdir():
                    child.unlink()
                raise PermissionError("directory held by client")

            with (
                patch("skill_conflicts.os.name", "nt"),
                patch("skill_conflicts.shutil.rmtree", side_effect=locked_empty_tree),
            ):
                manifest = remove_skill_conflicts(
                    conflicts,
                    home=home,
                    source_root=repo,
                    dry_run=False,
                    run_id="locked-run",
                )

            self.assertTrue(old.is_dir())
            self.assertEqual(list(old.iterdir()), [])
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(
                payload["conflicts"][0]["action"], "deferred_empty_directory"
            )

    def test_dry_run_changes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / "repo"
            home = root / "home"
            local = home / ".agents/skills"
            write_skill(repo / "skills", "publication-figures", "authoritative figures")
            old = write_skill(local, "legacy-plotter", "处理任意科研出图")
            conflicts = scan_skill_conflicts(
                platform="codex",
                source_root=repo,
                incoming={"publication-figures"},
                discovery_roots=[local],
                target_roots=[local],
            )

            manifest = remove_skill_conflicts(
                conflicts,
                home=home,
                source_root=repo,
                dry_run=True,
                run_id="dry-run",
            )

            self.assertTrue(old.is_dir())
            self.assertFalse(manifest.exists())


if __name__ == "__main__":
    unittest.main()
