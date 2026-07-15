from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from config_core import DEPENDENCIES, PRESETS, expand_dependencies
from sync_user_configs import LEGACY_SKILL_ALIASES


class VisualRoutingTests(unittest.TestCase):
    def test_visual_presets_install_imagegen_orchestration_and_svg_fallback(self) -> None:
        for preset in ("ppt", "writing"):
            expanded = expand_dependencies(PRESETS[preset])
            self.assertIn("research-visuals", expanded)
            self.assertIn("svg-diagrams", expanded)

    def test_legacy_image_diagrams_name_is_not_in_installer_contract(self) -> None:
        configured = set().union(*PRESETS.values(), DEPENDENCIES.keys())
        for companions in DEPENDENCIES.values():
            configured.update(companions)
        self.assertNotIn("image-diagrams", configured)
        self.assertEqual(LEGACY_SKILL_ALIASES["image-diagrams"], "research-visuals")

    def test_research_visuals_skill_has_required_progressive_disclosure_files(self) -> None:
        skill = ROOT / "skills" / "research-visuals"
        body = (skill / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("name: research-visuals", body)
        for relative in (
            "references/visual-strategy.md",
            "references/carrier-specs.md",
            "references/prompt-recipes.md",
            "references/research-figure-patterns.md",
        ):
            self.assertTrue((skill / relative).is_file(), relative)


if __name__ == "__main__":
    unittest.main()
