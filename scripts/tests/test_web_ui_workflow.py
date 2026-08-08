import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_module(name: str, relative: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


browser_audit = load_module(
    "build_web_ui_audit_browser",
    "skills/build-web-ui/scripts/audit_browser.py",
)
static_audit = load_module(
    "build_web_ui_audit_static",
    "skills/build-web-ui/scripts/audit_static_html.py",
)
config_core = load_module("build_web_ui_config_core", "scripts/config_core.py")


class WebUiWorkflowTests(unittest.TestCase):
    def test_web_preset_and_routing_cases_are_available(self) -> None:
        self.assertEqual(config_core.PRESETS["web"], {"build-web-ui"})
        cases = {
            case["id"]: case
            for case in json.loads(
                (ROOT / "scripts/skill_routing_cases.json").read_text(encoding="utf-8")
            )["cases"]
        }
        self.assertEqual(cases["beautify_personal_website"]["primary"], "build-web-ui")
        self.assertEqual(cases["audit_web_ui_in_real_browser"]["primary"], "build-web-ui")
        self.assertIn("research-visuals", cases["beautify_personal_website"]["excluded"])

    def test_skill_contract_separates_static_and_browser_evidence(self) -> None:
        skill = (ROOT / "skills/build-web-ui/SKILL.md").read_text(encoding="utf-8")
        quality = (ROOT / "skills/build-web-ui/references/quality-gates.md").read_text(
            encoding="utf-8"
        )
        design = (ROOT / "skills/build-web-ui/references/design-playbook.md").read_text(
            encoding="utf-8"
        )
        for fragment in (
            "建立可检查的视觉合同",
            "效果堆叠候选",
            "公开页与后台页分别验收",
            "CDP 仿真的 390 像素手机布局视口",
            "不得把 `--window-size=390`",
            "锚点、滚动深处或任务状态",
            "控制台异常、脚本异常、HTTP 失败和网络加载失败",
        ):
            self.assertIn(fragment, skill)
        for fragment in (
            "浏览器外窗宽度不等于页面布局视口",
            "Emulation.setDeviceMetricsOverride",
            "innerWidth",
            "body.scrollWidth",
            "不能替代登录步骤、键盘操作、对比度计算",
        ):
            self.assertIn(fragment, quality)
        self.assertIn("同一视口出现两类或更多时", design)
        self.assertIn("先删除效果", design)
        workflow_audit = (ROOT / "scripts/audit_workflow_contracts.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('"skills/build-web-ui/"', workflow_audit)

    def test_local_changes_use_risk_scoped_validation(self) -> None:
        skill = (ROOT / "skills/build-web-ui/SKILL.md").read_text(encoding="utf-8")
        quality = (ROOT / "skills/build-web-ui/references/quality-gates.md").read_text(
            encoding="utf-8"
        )
        for fragment in (
            "L 局部纯前端",
            "不因网页 skill 自动触发无关的全仓测试",
            "用户明确在实际页面接手视觉验收",
            "部署后只做只读健康检查",
            "不得声称全套测试通过",
        ):
            self.assertIn(fragment, skill)
        for fragment in (
            "先选验证层级",
            "一个受影响 URL、状态和最危险视口",
            "默认不做",
            "用户明确接手实际页面的视觉验收",
            "已知范围外失败只能去重",
            "不运行会写入、回放旧负载或改变 revision 的探针",
        ):
            self.assertIn(fragment, quality)
        self.assertNotIn(
            "运行项目已有格式化、类型检查、lint、测试和生产构建",
            skill,
        )

    def test_web_ui_routes_types_palette_components_and_visual_gate(self) -> None:
        skill = (ROOT / "skills/build-web-ui/SKILL.md").read_text(encoding="utf-8")
        archetypes = (ROOT / "skills/build-web-ui/references/site-archetypes.md").read_text(
            encoding="utf-8"
        )
        colors = (ROOT / "skills/build-web-ui/references/color-systems.md").read_text(
            encoding="utf-8"
        )
        components = (ROOT / "skills/build-web-ui/references/interaction-components.md").read_text(
            encoding="utf-8"
        )
        external = (ROOT / "skills/build-web-ui/references/external-design-research.md").read_text(
            encoding="utf-8"
        )
        quality = (ROOT / "skills/build-web-ui/references/quality-gates.md").read_text(
            encoding="utf-8"
        )
        for fragment in (
            "site-archetypes.md",
            "color-systems.md",
            "interaction-components.md",
            "必须特征",
            "不得出现的特征",
            "待审阅",
            "第二次连续出现整体否定",
            "不因科研、医疗或“专业”自动使用大面积深绿、深蓝",
            "其配色不是本 skill 的默认值",
        ):
            self.assertIn(fragment, skill)
        for fragment in (
            "营销、产品与服务页",
            "电商、目录与预订",
            "内容、编辑与媒体站",
            "文档、知识库与课程站",
            "管理台、数据产品与科研工具",
            "公共服务与高风险表单",
        ):
            self.assertIn(fragment, archetypes)
        for fragment in (
            "主题、内容与配色互相证明",
            "竞争色相",
            "语义色不得承担无语义的大面积装饰",
            "通用模板、示例站和 showcase 只提供结构与颜色角色槽位",
            "当前页面的目的、读者、真实内容、使用环境",
            "Radix Colors",
            "Primer Primitives",
            "Carbon 颜色分层",
        ):
            self.assertIn(fragment, colors)
        for fragment in (
            "组件合同",
            "默认、hover、focus、pressed、selected、disabled、loading、empty、success、error、permission",
            "动效可以在任意时刻被新输入中断",
            "触控滑动不是唯一操作",
        ):
            self.assertIn(fragment, components)
        for fragment in (
            "抽象审美效果",
            "优先核验的原始来源",
            "许可证",
            "不复制品牌色",
            "项目级前端参考",
            "按具体组件建立采用矩阵",
            "组件状态与视觉回归参考",
            "生产包实际增量",
            "失败时保留实际图和差异图",
            "shadcn/ui",
            "Ant Design",
            "MUI",
            "Headless UI",
            "Storybook",
            "Playwright",
        ):
            self.assertIn(fragment, external)
        for fragment in (
            "独立的人工视觉门禁",
            "竞争色相",
            "不生成自动审美评分",
            "候选审阅与部署状态",
            "共享组件状态与截图基线",
            "禁止在测试失败时自动接受全部新截图",
        ):
            self.assertIn(fragment, quality)

        cases = {
            case["id"]: case
            for case in json.loads(
                (ROOT / "scripts/skill_routing_cases.json").read_text(encoding="utf-8")
            )["cases"]
        }
        self.assertEqual(cases["restyle_dashboard_with_vague_theme"]["primary"], "build-web-ui")
        self.assertEqual(cases["repair_local_web_spacing"]["primary"], "build-web-ui")
        self.assertEqual(cases["repair_mobile_visual_balance"]["primary"], "build-web-ui")
        self.assertEqual(cases["design_commerce_flow"]["primary"], "build-web-ui")

    def test_web_ui_showcase_is_renderable_and_explicitly_simulated(self) -> None:
        showcase = (ROOT / "docs/showcase/build-web-ui/index.html").read_text(
            encoding="utf-8"
        )
        renderer = (ROOT / "docs/demo/render_build_web_ui_showcase.py").read_text(
            encoding="utf-8"
        )
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for fragment in (
            "全部名称与数字均为模拟内容",
            "先关闭 28 条关键质控问题",
            "数据冻结准备度",
            "prefers-reduced-motion",
            'aria-label="项目导航"',
        ):
            self.assertIn(fragment, showcase)
        for relative in (
            "docs/showcase/build-web-ui/desktop.png",
            "docs/showcase/build-web-ui/mobile.png",
        ):
            self.assertTrue((ROOT / relative).is_file())
            self.assertIn(relative, readme)
        for fragment in (
            "audit_browser.py",
            "desktop=1440x960,mobile=390x844",
            "Browser audit did not pass; refusing to publish screenshots",
        ):
            self.assertIn(fragment, renderer)

    def test_static_audit_keeps_valid_noindex_page_clean(self) -> None:
        html = """<!doctype html>
        <html lang="zh-CN"><head><title>测试页</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta name="robots" content="noindex"></head>
        <body><main><h1>测试页</h1></main></body></html>"""
        findings = static_audit.audit_document(html, None, None, False)
        self.assertEqual(findings, [])

    def test_static_audit_detects_structure_and_accessibility_failures(self) -> None:
        html = """<html><head><title>Bad</title></head><body>
        <main><h1 id="same">One</h1><h1 id="same">Two</h1>
        <img src="missing.png"><input id="query"></main></body></html>"""
        codes = {
            finding.code
            for finding in static_audit.audit_document(html, None, None, False)
        }
        self.assertTrue(
            {"html-lang", "viewport", "h1-count", "description", "duplicate-id", "image-alt", "control-name"}
            <= codes
        )

    def test_browser_viewports_distinguish_real_mobile_layout(self) -> None:
        viewports = browser_audit.parse_viewports(
            "desktop=1440x1000,mobile=390x844,tablet=820x1180:mobile"
        )
        self.assertEqual([(item.width, item.mobile) for item in viewports], [(1440, False), (390, True), (820, True)])
        with self.assertRaisesRegex(Exception, "Invalid viewport"):
            browser_audit.parse_viewports("mobile:390x844")

    def test_browser_audit_rejects_credential_bearing_urls(self) -> None:
        with self.assertRaisesRegex(browser_audit.BrowserAuditError, "embedded credentials"):
            browser_audit.validate_urls(["https://user:pass@example.test/"])
        with self.assertRaisesRegex(browser_audit.BrowserAuditError, "credential-like key"):
            browser_audit.validate_urls(["https://example.test/?access_token=secret"])
        self.assertEqual(
            browser_audit.validate_urls(["http://127.0.0.1:8000/archive?year=2024#results"]),
            ["http://127.0.0.1:8000/archive?year=2024#results"],
        )

    def test_browser_audit_collects_layout_geometry_without_scoring_aesthetics(self) -> None:
        source = browser_audit.PAGE_AUDIT_JS
        for fragment in (
            "layoutGeometry",
            "inlineGaps",
            "centerOffset",
            "edgeClippedContent",
            "data-audit-layout",
        ):
            self.assertIn(fragment, source)
        self.assertNotIn("aestheticScore", source)

    def test_browser_issue_summary_checks_rendered_failures(self) -> None:
        viewport = browser_audit.Viewport("mobile", 390, 844, True)
        clean_page = {
            "innerWidth": 390,
            "clientWidth": 390,
            "scrollWidth": 390,
            "bodyScrollWidth": 390,
            "horizontalOverflow": False,
            "h1Count": 1,
            "duplicateIds": [],
            "missingAlt": [],
            "brokenImages": [],
        }
        clean_runtime = {
            "console": [],
            "exceptions": [],
            "logEntries": [],
            "httpFailures": [],
            "networkFailures": [],
        }
        self.assertEqual(
            browser_audit.scenario_issues(clean_page, clean_runtime, viewport, False),
            [],
        )
        broken_page = dict(clean_page)
        broken_page.update(
            innerWidth=504,
            clientWidth=504,
            horizontalOverflow=True,
            h1Count=0,
            duplicateIds=[{"id": "x", "count": 2}],
            brokenImages=[{"src": "/missing.png"}],
        )
        broken_runtime = dict(clean_runtime)
        broken_runtime["exceptions"] = [{"text": "boom"}]
        codes = {
            item["code"]
            for item in browser_audit.scenario_issues(
                broken_page, broken_runtime, viewport, False
            )
        }
        self.assertTrue(
            {
                "viewport-inner-width",
                "viewport-client-width",
                "horizontal-overflow",
                "h1-count",
                "duplicate-id",
                "broken-image",
                "runtime-exception",
            }
            <= codes
        )

        desktop = browser_audit.Viewport("desktop", 1440, 1000, False)
        desktop_page = dict(clean_page)
        desktop_page.update(
            innerWidth=1440,
            clientWidth=1425,
            scrollWidth=1425,
            bodyScrollWidth=1425,
        )
        self.assertEqual(
            browser_audit.scenario_issues(
                desktop_page, clean_runtime, desktop, False
            ),
            [],
        )


if __name__ == "__main__":
    unittest.main()
