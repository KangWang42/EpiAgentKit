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
        self.assertIn("所有待附图片均有本地路径时使用 `referenced_image_paths`", body)
        self.assertIn("最小 `num_last_images_to_include`", body)
        self.assertIn("两者不得并用", body)
        self.assertIn("参考图解构与编辑目标", planning)
        self.assertIn("携图编辑合同", planning)
        self.assertIn("载体定位与实例隔离", planning)
        self.assertIn("载体语义身份", planning)
        self.assertIn("项目专属事实只进入本次运行时合同", planning)
        self.assertIn("生成科研非统计视觉", readme)
        self.assertIn("research-visuals → imagegen", readme)
        self.assertIn("主 `SKILL.md` 始终优先", source)
        self.assertIn("携带全部且仅必要的编辑目标", source)
        self.assertIn("Edit the attached target image", recipes)
        self.assertIn("只归档选定的开源参考文档与提示词", readme)
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

    def test_image_editing_uses_no_regression_contract_and_524_split(self) -> None:
        skill = ROOT / "skills" / "research-visuals"
        body = (skill / "SKILL.md").read_text(encoding="utf-8")
        planning = (skill / "references" / "figure-planning.md").read_text(
            encoding="utf-8"
        )
        recipes = (skill / "references" / "prompt-recipes.md").read_text(
            encoding="utf-8"
        )
        svg_fallback = (ROOT / "skills" / "svg-diagrams" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        rules = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        for fragment in (
            "Image 1 视为验收基线",
            "事实与语义忠实度",
            "LOCKED",
            "FLEXIBLE",
            "FORBIDDEN",
            "第二次 524",
            "不计入两轮设计修正",
            "导出文件名和媒体序号仅作存储线索",
            "项目专属的正式图号",
        ):
            self.assertIn(fragment, body)
        for fragment in (
            "Baseline: Image 1 is the acceptance baseline",
            "A more attractive image is not acceptable",
            "Image 2: optional auxiliary reference",
            "Use case: high-fidelity scientific-figure edit",
            "Structure inventory",
            "merges or branches",
            "ambiguous source text must be copied, never guessed",
            "100% critical-text accuracy",
            "100% node and edge preservation",
            "First HTTP 524",
            "Second HTTP 524",
            "do not silently downgrade the model or switch to SVG/API",
            "每个最终提示词只保留三条永久约束",
            "相同约束只出现一次",
            "图类专属质量指标",
            "人物或临床场景",
            "网页视觉",
            "科学教育插图",
            "封面与章节图",
            "Target identity:",
            "Resolved Image 1:",
            "Instance-only facts:",
            "Carrier-managed text:",
        ):
            self.assertIn(fragment, recipes)
        self.assertIn("Baseline / Image 1", planning)
        self.assertIn("单一机制无法覆盖全部图片时", planning)
        self.assertIn("适用的 Image 2 可从首轮开始使用", planning)
        self.assertIn("SVG 只能位于这些适用 imagegen 路径之后", planning)
        self.assertIn("非统计视觉先走 `research-visuals` → `imagegen`", rules)
        self.assertIn("真实统计图走 `publication-figures`", rules)
        self.assertIn(
            "SVG 只按 `research-visuals` 与 `svg-diagrams` 的明确条件使用",
            rules,
        )
        for conditional_detail in (
            "HTTP 524",
            "referenced_image_paths",
            "num_last_images_to_include",
            "Image 1 为验收基线",
            "导出文件名或媒体序号只作存储线索",
        ):
            self.assertNotIn(conditional_detail, rules)
        self.assertIn("HTTP 524 按 `research-visuals` 保留原图并停止", svg_fallback)
        self.assertIn("连续两次 HTTP 524", svg_fallback)
        self.assertIn("适用的 Image 2 优先于 SVG", svg_fallback)
        self.assertIn("全部适用的 imagegen 路径实际耗尽", svg_fallback)
        self.assertIn("适用的 Image 2 已存在时，必须先于 SVG", body)
        self.assertIn(
            "SVG 仅在明确矢量要求、工具实际不可用或全部适用 imagegen 路径耗尽后使用",
            body,
        )
        self.assertNotIn("Preserve exactly:", recipes)
        self.assertNotIn(
            "No watermark, logo, pseudo-text, random interface copy, decorative formulas",
            recipes,
        )
        self.assertNotIn("单一修改 / 必须保持 / 允许变化 / 禁止变化", body)
        self.assertEqual(recipes.count("Permanent constraints:"), 1)
        self.assertEqual(recipes.count("no watermark or false branding"), 1)

    def test_codex_builtin_imagegen_isolates_inline_payloads(self) -> None:
        body = (
            ROOT / "skills" / "research-visuals" / "SKILL.md"
        ).read_text(encoding="utf-8")
        rules = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")

        for fragment in (
            "Codex 内置 imagegen 的会话隔离",
            "image_generation_end.result",
            "input_image.image_url",
            "一次性隔离子代理",
            "主任务不得调用 `image_gen`",
            "每次原图查看、候选图对照、定向修正和最终载体视觉检查",
            "只返回纯文本",
            "不得调用 `generatedImage(...)`",
            "不得继续使用已经接收过内联图像载荷的子代理",
            "独立图片任务",
            "不能把 compact 或直接修改会话 JSONL 当作修复",
        ):
            self.assertIn(fragment, body)
        for fragment in (
            "会话隔离门禁",
            "主任务只保留纯文本与本地文件路径",
            "不接收或回放 data URL、base64 或内联图片",
            "不得把 compact、修改会话 JSONL 或静默切换 CLI/API 当作修复",
        ):
            self.assertIn(fragment, rules)

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
