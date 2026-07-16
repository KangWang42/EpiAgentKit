from __future__ import annotations

import hashlib
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
            "references/figure-planning.md",
            "references/diagram-iconography.md",
            "references/external/SOURCE.md",
            "references/external/academic-figure-skill/figure-contract.md",
            "references/external/academic-figure-skill/multipanel-layout.md",
            "references/external/academic-figure-skill/LICENSE",
            "references/external/academic-figure-generator/academic-figure-prompt-upstream.md",
            "references/external/academic-figure-generator/LICENSE",
        ):
            self.assertTrue((skill / relative).is_file(), relative)

    def test_external_figure_patterns_are_adapted_without_route_regression(self) -> None:
        skill = ROOT / "skills" / "research-visuals"
        body = (skill / "SKILL.md").read_text(encoding="utf-8")
        planning = (skill / "references" / "figure-planning.md").read_text(
            encoding="utf-8"
        )
        source = (skill / "references" / "external" / "SOURCE.md").read_text(
            encoding="utf-8"
        )
        recipes = (skill / "references" / "prompt-recipes.md").read_text(
            encoding="utf-8"
        )
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("来源到图件矩阵", body)
        self.assertIn("必要性与证据、内容与拓扑、视觉与可读性、最终载体", body)
        self.assertIn("不按章节机械配图", planning)
        self.assertIn("不强制设置“英雄面板”", planning)
        self.assertIn("TingxiYu/academic-figure-skill", planning)
        self.assertIn("LigphiDonk/academic-figure-generator", planning)
        self.assertIn("未引入上游生产脚本、示例图片或第三方 API 配置", planning)
        self.assertIn("不得把上游文件当独立 skill 直接执行", body)
        self.assertIn("携图定向编辑", body)
        self.assertIn("全部目标都有本地路径时使用 `referenced_image_paths`", body)
        self.assertIn("最小 `num_last_images_to_include`", body)
        self.assertIn("两者不得并用", body)
        self.assertIn("参考图解构与编辑目标", planning)
        self.assertIn("携图编辑合同", planning)
        self.assertIn("imagegen 新图或携图编辑", readme)
        self.assertIn("主 `SKILL.md` 始终优先", source)
        self.assertIn("携带全部且仅必要的编辑目标", source)
        self.assertIn("Edit the attached target image", recipes)
        self.assertIn("选定的开源参考文档和提示词", readme)
        self.assertNotIn("最多连续两次纯文本重生成", body)
        self.assertNotIn("Do not use or condition on any reference image", recipes)
        self.assertNotIn("minimum 500 words", body)
        self.assertNotIn("User Confirms", body)

    def test_diagram_iconography_is_semantic_and_adaptive(self) -> None:
        reference = (
            ROOT
            / "skills"
            / "research-visuals"
            / "references"
            / "diagram-iconography.md"
        ).read_text(encoding="utf-8")

        for fragment in (
            "W3C G207",
            "Microsoft Fluent 2 Iconography",
            "IBM Pictogram Usage",
            "GOV.UK Design System",
            "全图最多 4 个",
            "通常 2–4 个，不逐节点配图",
            "全图 0–3 个",
            "Icon strategy",
            "必要图标与相邻背景至少 3:1",
        ):
            self.assertIn(fragment, reference)
        self.assertIn("本地操作性启发式", reference)
        self.assertIn("不使用灯泡、奖杯、火箭、脑、芯片或发光 DNA", reference)

    def test_vendored_figure_references_match_reviewed_snapshots(self) -> None:
        external = ROOT / "skills" / "research-visuals" / "references" / "external"
        expected = {
            "academic-figure-skill/figure-contract.md":
                "f67fab86c84069368988cf49b699b901758bc04dbc98a69d22fd62ee3e3692c6",
            "academic-figure-skill/multipanel-layout.md":
                "c6494e4e086ed006f379cc6f126514aba1ea6c4de3b10e98f55c280a2c57b1bc",
            "academic-figure-generator/academic-figure-prompt-upstream.md":
                "6d84103d20c43dbf46c97f0aea99867bd7675599885901390860da35a9033e47",
        }
        for relative, digest in expected.items():
            actual = hashlib.sha256((external / relative).read_bytes()).hexdigest()
            self.assertEqual(actual, digest, relative)

    def test_external_source_local_override_paths_exist(self) -> None:
        references = ROOT / "skills" / "research-visuals" / "references"
        source = (references / "external" / "SOURCE.md").read_text(encoding="utf-8")
        for filename in (
            "figure-planning.md",
            "research-figure-patterns.md",
            "prompt-recipes.md",
        ):
            self.assertIn(f"`../{filename}`", source)
            self.assertTrue((references / filename).is_file(), filename)


if __name__ == "__main__":
    unittest.main()
