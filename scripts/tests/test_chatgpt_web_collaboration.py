from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from skill_conflicts import semantic_match


class ChatGPTWebCollaborationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        skill_root = ROOT / "skills" / "chatgpt-web-collaboration"
        cls.skill = (skill_root / "SKILL.md").read_text(encoding="utf-8")
        cls.playbook = (skill_root / "references" / "task-playbook.md").read_text(
            encoding="utf-8"
        )
        cls.rules = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        cls.readme = (ROOT / "README.md").read_text(encoding="utf-8")
        cls.cases = {
            case["id"]: case
            for case in json.loads(
                (ROOT / "scripts" / "skill_routing_cases.json").read_text(
                    encoding="utf-8"
                )
            )["cases"]
        }

    def test_session_authorization_is_sticky_but_not_persisted(self) -> None:
        for fragment in (
            "本 Codex 对话内保持启用",
            "不再询问启用、继续、准备材料、读取回复或本地核验",
            "直到再次明确启用",
            "不把授权写入项目",
            "不带到新的 Codex 对话",
            "一次说明 `chatgpt.com` 和发送内容",
            "不为同一批重复或逐条确认",
            "不把会话授权当作未确定未来消息的批准",
        ):
            self.assertIn(fragment, self.skill)

    def test_browser_binding_prefers_edge_and_stays_on_chatgpt(self) -> None:
        for fragment in (
            "Edge 优先、Chrome 备用",
            "专用标签页并在本会话持续复用",
            "只在 `chatgpt.com` 收发消息",
            "不要检查 Cookie、本地存储、密码、账号设置或浏览器配置",
            "不关闭用户原有标签页",
        ):
            self.assertIn(fragment, self.skill)

    def test_web_output_never_replaces_domain_verification(self) -> None:
        for fragment in (
            "未核验内容不得进入正式引文或证据矩阵",
            "事实与含义核对",
            "不直接改变 SAP",
            "一致意见也不替代原验收",
        ):
            self.assertIn(fragment, self.playbook)
        self.assertIn("回复始终是候选内容", self.skill)

    def test_documents_are_pasted_as_locally_extracted_text(self) -> None:
        for fragment in (
            "绝不向 ChatGPT 网页上传文件",
            "在本地提取为 UTF-8 文本或 Markdown",
            "保留标题层级、段落编号和表格语义",
            "按完整语义块编号后复制粘贴",
            "无法由纯文本忠实保留的内容只在本地核验",
        ):
            self.assertIn(fragment, self.skill)
        for fragment in (
            "文档位置、必要上下文、锁定项和本批任务",
            "网页端只判断本批可见文字",
        ):
            self.assertIn(fragment, self.playbook)

        case = self.cases["paste_document_text_without_upload"]
        self.assertEqual(case["primary"], "academic-humanizer")
        self.assertEqual(case["companions"], ["docx", "chatgpt-web-collaboration"])
        self.assertIn("extract_utf8_text", case["expected_action"])
        self.assertIn("verify_nontext_locally", case["expected_action"])

    def test_skill_stays_compact(self) -> None:
        self.assertLess(len(self.skill.splitlines()), 45)
        self.assertLess(len(self.playbook.splitlines()), 20)
        self.assertNotIn("TODO", self.skill + self.playbook)

    def test_routing_covers_enable_continue_stop_and_web_ui_boundary(self) -> None:
        enabled = self.cases["enable_chatgpt_web_for_session"]
        self.assertEqual(enabled["primary"], "chatgpt-web-collaboration")
        self.assertIn("edge_then_chrome", enabled["expected_action"])
        self.assertIn("confirm_only_at_browser_action_time", enabled["expected_action"])

        continued = self.cases["active_session_manuscript_web_review"]
        self.assertEqual(continued["primary"], "academic-humanizer")
        self.assertIn("chatgpt-web-collaboration", continued["companions"])

        stopped = self.cases["stop_chatgpt_web_for_session"]
        self.assertEqual(stopped["primary"], "chatgpt-web-collaboration")
        self.assertIn("explicit_reactivation", stopped["expected_action"])

        web_ui = self.cases["audit_web_ui_in_real_browser"]
        self.assertEqual(web_ui["primary"], "build-web-ui")
        self.assertIn("chatgpt-web-collaboration", web_ui["excluded"])

    def test_skill_is_discoverable_without_duplication(self) -> None:
        self.assertIn("当前会话中的 ChatGPT 网页协作", self.rules)
        self.assertIn("`chatgpt-web-collaboration`", self.readme)

    def test_conflict_detection_is_specific_to_chatgpt_collaboration(self) -> None:
        match = semantic_match(
            "调用 ChatGPT 网页协作完成分段润色",
            {"chatgpt-web-collaboration"},
        )
        self.assertIsNotNone(match)
        self.assertEqual(match[0], "chatgpt-web-collaboration")
        self.assertIsNone(
            semantic_match(
                "构建响应式网页并在真实浏览器检查布局",
                {"chatgpt-web-collaboration"},
            )
        )


if __name__ == "__main__":
    unittest.main()
