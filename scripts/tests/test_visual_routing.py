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
        ppt = expand_dependencies(PRESETS["ppt"])
        self.assertIn("academic-ppt", ppt)
        self.assertIn("pptx", ppt)

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
            "references/computer-science-visuals.md",
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

    def test_computer_science_visuals_use_domain_specific_grammar_and_task_scoped_outputs(self) -> None:
        skill = ROOT / "skills" / "research-visuals"
        body = (skill / "SKILL.md").read_text(encoding="utf-8")
        computer = (skill / "references" / "computer-science-visuals.md").read_text(
            encoding="utf-8"
        )
        strategy = (skill / "references" / "visual-strategy.md").read_text(
            encoding="utf-8"
        )
        recipes = (skill / "references" / "prompt-recipes.md").read_text(
            encoding="utf-8"
        )
        source = (skill / "references" / "external" / "SOURCE.md").read_text(
            encoding="utf-8"
        )

        for fragment in (
            "计算机科学、人工智能、机器学习、信号处理、软件系统、数据系统",
            "成果数量、覆盖范围和使用位置服从用户当前请求",
            "不擅自增加近似版本",
            "内容来源图",
            "不附带内容来源图",
            "表现身份",
            "非目标文字、结构、图元、表示类型、裁切或已认可质量",
        ):
            self.assertIn(fragment, body)
        self.assertNotIn("epiagentkit-maintenance", body)
        self.assertNotIn("skill 维护", body)
        for fragment in (
            "数据表示、算法步骤、模型模块、张量变换",
            "医学人工智能、数字健康、生物信息学等混合图逐部分判定",
            "训练与推理",
            "残差或跳连",
            "软件、数据或基础设施系统",
            "成果数量服从用户请求和实际使用位置",
            "无通用 AI 脑、芯片、机器人、代码雨、全息屏",
            "架构沟通图保留全部关键模块和连接",
            "算子审计图保留精确张量",
            "只保留一个简短标题",
            "不得再加副标题",
            "纯色矩阵与特征图",
            "无渐变、无白雾、无中心高光",
            "真实遥感时相图",
        ):
            self.assertIn(fragment, computer)
        self.assertNotIn("skill 维护", computer)
        for fragment in (
            "表面系统",
            "区域分隔",
            "颜色落点",
            "容器深度",
            "密度节奏",
            "轻量浮层、柔和彩色表示或不对称分区只是可选组合",
            "纯色平涂是单独的表面合同",
            "真实时相图、概率图、热区图和连续强度图不套用纯色合同",
        ):
            self.assertIn(fragment, strategy)
        self.assertIn("Aesthetic system:", recipes)
        self.assertIn("内容来源图重构模板", recipes)
        self.assertIn("do not attach or imitate it", recipes)
        self.assertIn("Figure title:", recipes)
        self.assertIn("Raster resolution contract:", recipes)
        self.assertIn("Representation identity lock:", recipes)
        self.assertIn("Flat-fill contract:", recipes)
        self.assertIn("任何非目标文字、结构、图元、表示类型、裁切、材质或已认可质量发生漂移", recipes)
        carrier = (skill / "references" / "carrier-specs.md").read_text(
            encoding="utf-8"
        )
        for fragment in (
            "像素、最终尺寸与 DPI 合同",
            "像素 = 毫米 ÷ 25.4 × ppi",
            "不能把元数据当作像素充分性的替代",
            "不得通过插值放大后声称原生达到 300 dpi",
        ):
            self.assertIn(fragment, carrier)
        self.assertIn("academic-figure-prompt-pastel/SKILL.md", source)
        self.assertIn("不得直接执行上游 pastel skill", source)

    def test_imagegen_prompt_contract_is_minimal_reusable_and_auditable(self) -> None:
        skill = ROOT / "skills" / "research-visuals"
        body = (skill / "SKILL.md").read_text(encoding="utf-8")
        recipes = (skill / "references" / "prompt-recipes.md").read_text(
            encoding="utf-8"
        )
        planning = (skill / "references" / "figure-planning.md").read_text(
            encoding="utf-8"
        )
        computer = (skill / "references" / "computer-science-visuals.md").read_text(
            encoding="utf-8"
        )
        source = (skill / "references" / "external" / "SOURCE.md").read_text(
            encoding="utf-8"
        )
        for fragment in (
            "规划表不得整段粘给 imagegen",
            "USE`、`CONTENT LOCK`、`GRAPH OR LAYOUT`、`VISUAL DIRECTION`、`CONSTRAINTS",
            "紧凑邻接表",
            "汇聚拆成多条有向边",
            "每轮编辑只设一个可观察修改目标",
            "不承诺提示词能保证 imagegen 完美遵循",
            "不靠提示词中的 `300 dpi`、`4K` 或 `print-ready`",
        ):
            self.assertIn(fragment, body)
        for fragment in (
            "图外规划",
            "实际调用提示词",
            "USE → CONTENT LOCK → GRAPH OR LAYOUT → VISUAL DIRECTION → CONSTRAINTS",
            'NODES: input="<label>"',
            "EDGES: input>M00; M00>M01; M01>output",
            "M06>M12; M11>M12",
            "不能保证生成式模型完美复现生产级密集文字与拓扑",
            "不要把 `300 dpi`、`4K` 或 `print-ready` 当作能改变真实像素的提示词",
            "同一轮不得同时要求",
        ):
            self.assertIn(fragment, recipes)
        self.assertIn("这是来源与验收工作表，不得原样粘贴给 imagegen", planning)
        self.assertIn("同一 ID 和同一边只写一次", planning)
        self.assertIn("不得把整表追加到 imagegen 提示词末尾", computer)
        self.assertIn("GPT Image Generation Models Prompting Guide", source)
        self.assertIn("https://learn.chatgpt.com/docs/image-generation", source)

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

        self.assertIn("制定图件计划", body)
        self.assertIn("逐项写明每张候选图的来源、独立作用和采用理由", body)
        self.assertIn("不按章节机械配图", planning)
        self.assertIn("不预先指定一个占据最大面积的主要子图", planning)
        self.assertIn("TingxiYu/academic-figure-skill", planning)
        self.assertIn("LigphiDonk/academic-figure-generator", planning)
        self.assertIn("未引入原项目的执行脚本、示例图片或第三方 API 配置", planning)
        self.assertIn("不得把上游文件当独立 skill 直接执行", body)
        self.assertIn("根据原图定向修改", body)
        self.assertIn("所有目标图片都有本地路径时传入这些路径", body)
        self.assertIn("最小 `num_last_images_to_include`", body)
        self.assertIn("两者不得并用", body)
        self.assertIn("参考图解构与编辑目标", planning)
        self.assertIn("根据原图修改或按内容重构的要求", planning)
        self.assertIn("确定文档或页面中的待修改图件", planning)
        self.assertIn("图在文档或页面中的位置", planning)
        self.assertIn("项目专属事实只进入本次任务记录", planning)
        self.assertIn("生成科研非统计视觉", readme)
        self.assertIn("research-visuals → imagegen", readme)
        self.assertIn("主 `SKILL.md` 始终优先", source)
        self.assertIn("附带全部且仅必要的待修改图片", source)
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

    def test_verified_counts_do_not_turn_structural_diagrams_into_statistical_plots(self) -> None:
        visual = (ROOT / "skills/research-visuals/SKILL.md").read_text(
            encoding="utf-8"
        )
        figures = (ROOT / "skills/publication-figures/SKILL.md").read_text(
            encoding="utf-8"
        )
        patterns = (
            ROOT
            / "skills/research-visuals/references/research-figure-patterns.md"
        ).read_text(encoding="utf-8")

        self.assertIn("通过坐标位置、长度、面积、角度、颜色、大小", visual)
        self.assertIn("不会把结构图变成统计图", visual)
        self.assertIn("病例筛选", figures)
        self.assertIn("节点含有真实样本量", figures)
        self.assertIn("分流依据是数字承担的表达功能", patterns)
        self.assertIn("逐字逐数逐箭头核对", patterns)
        self.assertNotIn("任何坐标、比例、效应值、置信区间、样本量或真实数据映射", visual)

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
            "待修改原图为内容核对依据",
            "事实与语义忠实度",
            "必须保持的文字、数字、公式",
            "可以调整的版式、间距",
            "不得添加、删除、纠正、推断、合并、替换或简化的内容",
            "第二次 524",
            "不计入两轮内容修改",
            "导出文件名和媒体序号仅作存储线索",
            "项目专属的正式图号",
        ):
            self.assertIn(fragment, body)
        for fragment in (
            "Use the attached target image to verify the edit",
            "A more attractive image is not acceptable",
            "Optional reference image: use only when it has already been provided",
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
            "相同事实、节点、关系和约束只出现一次",
            "图类专属质量指标",
            "人物或临床场景",
            "网页视觉",
            "科学教育插图",
            "封面与章节图",
            "Target identity:",
            "Confirmed edit target:",
            "Instance-only facts:",
            "Carrier-managed text:",
        ):
            self.assertIn(fragment, recipes)
        self.assertIn("| 待修改原图 |", planning)
        self.assertIn("优先附带待修改原图", planning)
        self.assertIn("不为使用参考图单独增加一轮", planning)
        self.assertIn("第二次修改后保存该图作为当前结果", planning)
        self.assertIn("分别说明内容硬伤、表现身份漂移、审美问题、影响", planning)
        self.assertIn("不自动重生整图或改用 SVG", planning)
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
            "待修改原图为内容核对依据",
            "导出文件名或媒体序号只作存储线索",
        ):
            self.assertNotIn(conditional_detail, rules)
        self.assertIn("HTTP 524 按 `research-visuals` 保留原图并停止", svg_fallback)
        self.assertIn("连续两次 HTTP 524", svg_fallback)
        self.assertIn(
            "已有修改结果不准确或不好看",
            svg_fallback,
        )
        self.assertIn("目标格式强制矢量", svg_fallback)
        self.assertIn("不切换 SVG", svg_fallback)
        self.assertIn("不存在有用参考图时直接省略", body)
        self.assertIn(
            "只有 imagegen 实际不可用、用户明确要求 SVG/矢量源",
            body,
        )
        self.assertIn("第二次成功修改后已保存当前结果", body)
        self.assertIn("内容硬伤，包括错误", recipes)
        self.assertIn("表现身份漂移，包括写实/示意类型", recipes)
        self.assertIn("审美问题，包括比例", recipes)
        self.assertNotIn("Preserve exactly:", recipes)
        self.assertNotIn(
            "No watermark, logo, pseudo-text, random interface copy, decorative formulas",
            recipes,
        )
        for old_term in (
            "Image 1",
            "Image 2",
            "LOCKED",
            "FLEXIBLE",
            "FORBIDDEN",
            "Baseline / Image 1",
            "Resolved Image 1",
        ):
            self.assertNotIn(old_term, body)
            self.assertNotIn(old_term, planning)
            self.assertNotIn(old_term, recipes)
            self.assertNotIn(old_term, svg_fallback)
        self.assertEqual(recipes.count("每个最终提示词只保留三条永久约束"), 1)
        self.assertEqual(recipes.count("no watermark or false branding"), 1)

    def test_codex_builtin_imagegen_uses_current_tool_without_session_mutation(self) -> None:
        body = (
            ROOT / "skills" / "research-visuals" / "SKILL.md"
        ).read_text(encoding="utf-8")
        rules = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")

        for fragment in (
            "Codex 使用当前会话提供的内置 `imagegen` 技能和 `image_gen` 工具",
            "调用前确认完整提示词、全部输入图片、目标用途和验收条件",
            "不修改会话历史",
            "不把 data URL、base64 或内联图像内容写入项目文件",
            "工具不可用或缺少必要输入图片时",
            "不另写 API 脚本",
        ):
            self.assertIn(fragment, body)
        self.assertIn("非统计视觉先走 `research-visuals` → `imagegen`", rules)
        for obsolete_requirement in (
            "一次性隔离子代理",
            "主任务不得调用 `image_gen`",
            "修改会话 JSONL",
            "不得调用 `generatedImage(...)`",
        ):
            self.assertNotIn(obsolete_requirement, body)
            self.assertNotIn(obsolete_requirement, rules)

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
