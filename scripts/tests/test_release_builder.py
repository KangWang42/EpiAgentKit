import hashlib
import importlib.util
import re
import subprocess
import sys
import tempfile
import unittest
import urllib.parse
import zipfile
from pathlib import Path, PurePosixPath
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "build_release.py"
SPEC = importlib.util.spec_from_file_location("build_release", MODULE_PATH)
build_release = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = build_release
SPEC.loader.exec_module(build_release)


class ReleaseBuilderTests(unittest.TestCase):
    def test_dirty_tree_requires_explicit_override(self):
        with tempfile.TemporaryDirectory() as temporary:
            with mock.patch.object(
                build_release,
                "git_state",
                return_value=("a" * 40, " M README.md"),
            ):
                with self.assertRaisesRegex(
                    build_release.ReleaseError,
                    "Working tree has uncommitted changes",
                ):
                    build_release.build_release(
                        ROOT,
                        Path(temporary),
                        allow_dirty=False,
                    )

    def test_release_is_deterministic_complete_and_self_verifying(self):
        with tempfile.TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            first = build_release.build_release(
                ROOT,
                temporary_root / "first",
                allow_dirty=True,
            )
            second = build_release.build_release(
                ROOT,
                temporary_root / "second",
                allow_dirty=True,
            )

            self.assertEqual(first.sha256, second.sha256)
            self.assertEqual(first.archive.read_bytes(), second.archive.read_bytes())
            self.assertEqual(
                first.sha256,
                hashlib.sha256(first.archive.read_bytes()).hexdigest(),
            )
            self.assertEqual(first.skill_count, 17)

            with self.assertRaisesRegex(
                build_release.ReleaseError,
                "Release target already exists",
            ):
                build_release.build_release(
                    ROOT,
                    temporary_root / "first",
                    allow_dirty=True,
                )

            rebuilt = build_release.build_release(
                ROOT,
                temporary_root / "first",
                allow_dirty=True,
                force=True,
            )
            self.assertEqual(first.sha256, rebuilt.sha256)
            self._inspect_archive(rebuilt.archive, temporary_root / "extracted")

    def _inspect_archive(self, archive_path: Path, extract_root: Path) -> None:
        package_name = build_release.PACKAGE_NAME
        prefix = f"{package_name}/"
        with zipfile.ZipFile(archive_path, "r") as archive:
            self.assertIsNone(archive.testzip())
            members = archive.namelist()
            self.assertEqual(members, sorted(members))
            self.assertTrue(all(member.startswith(prefix) for member in members))
            self.assertTrue(all("\\" not in member for member in members))
            self.assertTrue(
                all(archive.getinfo(member).date_time == (1980, 1, 1, 0, 0, 0) for member in members)
            )

            relative_members = {member[len(prefix):] for member in members}
            for required in (
                "CLAUDE.md",
                "README_中文.md",
                "VERSION",
                "SOURCE_COMMIT",
                "SKILLS_INCLUDED.txt",
                "SHA256SUMS",
                "NOTICE_许可与外部依赖.md",
            ):
                self.assertIn(required, relative_members)

            skill_names = {
                PurePosixPath(relative).parts[1]
                for relative in relative_members
                if relative.startswith("skills/") and len(PurePosixPath(relative).parts) >= 3
            }
            self.assertEqual(skill_names, set(build_release.INCLUDED_SKILLS))
            self.assertEqual(
                {
                    relative.removeprefix("skills/publication-figures/")
                    for relative in relative_members
                    if relative.startswith("skills/publication-figures/")
                },
                set(build_release.PUBLICATION_FIGURE_FILES),
            )

            lowered = [member.lower() for member in members]
            for forbidden in (
                "/docx/",
                "/pdf/",
                "/pptx/",
                "/xlsx/",
                "/sysu-ppt/",
                "/python-ecg-analysis/",
                "/build-web-ui/",
                "/epiagentkit-maintenance/",
                "recipes_common_50",
                "recipes_advanced/",
                "recipes_catalog.md",
                "build_catalog.r",
                "/.git/",
                "/09_backup/",
                "__pycache__",
            ):
                self.assertFalse(any(forbidden in member for member in lowered), forbidden)

            manifest = archive.read(f"{prefix}SHA256SUMS").decode("utf-8")
            expected_hashes = {}
            for line in manifest.splitlines():
                digest, relative = line.split("  ", 1)
                expected_hashes[relative] = digest
            self.assertEqual(
                set(expected_hashes),
                relative_members - {"SHA256SUMS"},
            )
            for relative, digest in expected_hashes.items():
                self.assertEqual(
                    digest,
                    hashlib.sha256(archive.read(f"{prefix}{relative}")).hexdigest(),
                    relative,
                )

            for relative in relative_members:
                suffix = PurePosixPath(relative).suffix.lower()
                if suffix in build_release.TEXT_SUFFIXES or PurePosixPath(relative).name in {
                    "VERSION",
                    "SOURCE_COMMIT",
                }:
                    archive.read(f"{prefix}{relative}").decode("utf-8-sig")

            archive.extractall(extract_root)

        package_root = extract_root / package_name
        self._check_relative_markdown_links(package_root)
        validator = ROOT / "skills" / "skill-creator" / "scripts" / "quick_validate.py"
        for skill_name in build_release.INCLUDED_SKILLS:
            completed = subprocess.run(
                ["python", str(validator), str(package_root / "skills" / skill_name)],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            self.assertEqual(
                completed.returncode,
                0,
                f"{skill_name}: {completed.stdout}\n{completed.stderr}",
            )

    def _check_relative_markdown_links(self, package_root: Path) -> None:
        pattern = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
        for markdown in package_root.rglob("*.md"):
            text = markdown.read_text(encoding="utf-8-sig")
            text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
            for raw_target in pattern.findall(text):
                target = raw_target.strip().strip("<>").split()[0]
                if not target or target.startswith(("#", "http://", "https://", "mailto:")):
                    continue
                relative_target = urllib.parse.unquote(target.split("#", 1)[0])
                if not relative_target:
                    continue
                resolved = (markdown.parent / relative_target).resolve()
                self.assertTrue(
                    resolved.is_relative_to(package_root.resolve()),
                    f"Link leaves package: {markdown} -> {target}",
                )
                self.assertTrue(
                    resolved.exists(),
                    f"Broken package link: {markdown} -> {target}",
                )


if __name__ == "__main__":
    unittest.main()
