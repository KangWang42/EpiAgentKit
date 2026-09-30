import importlib.util
import json
import posixpath
import re
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location("build_agensi", ROOT / "scripts" / "build_agensi.py")
build_agensi = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = build_agensi
SPEC.loader.exec_module(build_agensi)
LISTINGS = json.loads((ROOT / "scripts" / "agensi_listings.json").read_text(encoding="utf-8"))
EXCLUDED = {"docx", "pdf", "pptx", "xlsx", "skill-creator", "sysu-ppt", "epiagentkit-maintenance"}


class AgensiBuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.builder = build_agensi.Builder(ROOT, LISTINGS)

    def test_proprietary_and_private_skills_are_not_sellable(self):
        self.assertFalse(EXCLUDED & set(LISTINGS["skills"]))

    def test_cross_skill_links_are_vendored_and_resolve(self):
        package = self.builder.build("academic-publishing")
        self.assertIn("shared/academic-humanizer/references/chinese-academic-style.md", package.files)
        skill = package.files["SKILL.md"].decode("utf-8")
        self.assertIn("](shared/academic-humanizer/references/chinese-academic-style.md)", skill)
        for location, data in package.files.items():
            if not location.endswith(".md"):
                continue
            for target in re.findall(r"\]\(([^)\s#]+)", data.decode("utf-8")):
                if re.match(r"^[a-z]+:", target):
                    continue
                resolved = posixpath.normpath(posixpath.join(posixpath.dirname(location), target))
                self.assertIn(resolved, package.files, f"{location} -> {target}")

    def test_publication_figures_excludes_third_party_recipes(self):
        package = self.builder.build("publication-figures")
        self.assertFalse(any("recipes_" in path for path in package.files))

    def test_zip_has_single_top_folder_and_bilingual_frontmatter(self):
        package = self.builder.build("git-commit-helper")
        with tempfile.TemporaryDirectory() as temporary:
            archive = Path(temporary) / "git-commit-helper.zip"
            build_agensi.write_zip(archive, package)
            with zipfile.ZipFile(archive) as opened:
                names = opened.namelist()
                skill = opened.read("git-commit-helper/SKILL.md").decode("utf-8")
        self.assertEqual({name.split("/")[0] for name in names}, {"git-commit-helper"})
        self.assertIn("git-commit-helper/README.md", names)
        self.assertIn("git-commit-helper/references/core-rules.md", names)
        frontmatter, _ = build_agensi.split_frontmatter(skill)
        description = json.loads(frontmatter.split("description: ", 1)[1])
        self.assertTrue(description.startswith(LISTINGS["skills"]["git-commit-helper"]["description_en"]))

    def test_core_rules_drop_repository_only_and_shell_specific_bullets(self):
        rules = self.builder.core_rules()
        self.assertNotIn("自动提交", rules)
        self.assertNotIn("Invoke-Expression", rules)
        self.assertIn("NEVER", rules)


if __name__ == "__main__":
    unittest.main()
