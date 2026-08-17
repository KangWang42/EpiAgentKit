from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class WritingLanguageContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.humanizer_skill = (
            ROOT / "skills/academic-humanizer/SKILL.md"
        ).read_text(encoding="utf-8")
        cls.language_gate = (
            ROOT
            / "skills/academic-humanizer/references/chinese-academic-style.md"
        ).read_text(encoding="utf-8")
        cls.publishing = (
            ROOT / "skills/academic-publishing/SKILL.md"
        ).read_text(encoding="utf-8")
        cls.report = (ROOT / "skills/report-writing/SKILL.md").read_text(
            encoding="utf-8"
        )

    def test_fact_and_statistical_meaning_are_locked(self) -> None:
        for fragment in (
            "样本量、百分比、β 值、OR、RR、HR、置信区间、P 值",
            "不得：",
            "改变统计显著性、效应方向、比较对象、参照组、分析层级",
            "此处可能存在内容或统计逻辑问题",
            "以下仅进行语言层面的修改",
            "不在润色中偷偷纠正",
        ):
            self.assertIn(fragment, self.language_gate)

    def test_high_risk_phrases_are_contextual_clues(self) -> None:
        phrases = (
            "近年来",
            "受到广泛关注",
            "值得注意的是",
            "需要指出的是",
            "众所周知",
            "毋庸置疑",
            "不可忽视的是",
            "显而易见",
            "由此可见",
            "综上不难发现",
            "具有十分重要的意义",
            "具有重要的理论价值和现实意义",
            "提供了有力支撑",
            "提供了坚实基础",
            "填补空白",
            "突破性",
            "进一步丰富",
            "进一步拓展",
            "进一步深化",
            "充分说明",
            "有力证明",
            "彰显",
            "赋能",
            "助力",
            "多维协同",
            "精准施策",
            "系统性推进",
            "形成合力",
            "共同作用下形成",
            "全面提升",
            "有效促进",
            "显著改善",
            "真正实现",
            "切实提高",
            "已有研究",
            "部分学者",
            "专家认为",
            "我们可以看到",
            "不难发现",
        )
        for phrase in phrases:
            self.assertIn(phrase, self.language_gate)
        for boundary in (
            "只用于定位，不能机械清零",
            "规范术语",
            "真实统计结果",
            "经验证干预效果",
        ):
            self.assertIn(boundary, self.language_gate)

    def test_section_style_and_causal_boundaries_are_explicit(self) -> None:
        for fragment in (
            "摘要与执行摘要",
            "引言与报告背景",
            "方法",
            "结果",
            "讨论、解释与建议",
            "局限与结论",
            "横断面设计，无法推断因果关系",
            "随机试验",
            "具有明确因果 estimand 和充分识别条件的研究",
            "不写“1000 次 Bootstrap 分析显示 β=……”",
        ):
            self.assertIn(fragment, self.language_gate)

    def test_interaction_modes_follow_the_user_request(self) -> None:
        for fragment in (
            "直接修改",
            "原句 → 问题 → 推荐改法",
            "逐段修改",
            "用户说“继续”时直接进入下一处",
            "不再重复同类问题",
        ):
            self.assertIn(fragment, self.humanizer_skill)

    def test_paper_and_report_use_one_language_gate(self) -> None:
        reference = "../academic-humanizer/references/chinese-academic-style.md"
        self.assertIn(reference, self.publishing)
        self.assertIn(reference, self.report)
        self.assertFalse(
            (
                ROOT
                / "skills/academic-publishing/references/chinese-academic-style.md"
            ).exists()
        )
        self.assertIn("各部件写作与终审", self.publishing)
        self.assertIn("不强行套论文结构", self.report)
        self.assertIn("内容或统计逻辑疑问时单列", self.publishing)
        self.assertIn("内容或统计逻辑疑问时单列", self.report)

    def test_bootstrap_output_is_attributed_to_its_actual_source(self) -> None:
        resampling = (
            ROOT
            / "skills/academic-publishing/references/method-resampling.md"
        ).read_text(encoding="utf-8")
        for fragment in (
            "准确区分原模型估计量",
            "Bootstrap 95%CI",
            "不得写成“Bootstrap 分析显示 β/OR/RR/HR 为……”",
        ):
            self.assertIn(fragment, resampling)

    def test_existing_task_routing_is_preserved(self) -> None:
        cases = {
            case["id"]: case
            for case in json.loads(
                (ROOT / "scripts/skill_routing_cases.json").read_text(
                    encoding="utf-8"
                )
            )["cases"]
        }
        self.assertEqual(
            "academic-publishing", cases["paper_from_scratch_word"]["primary"]
        )
        self.assertEqual(
            "academic-humanizer",
            cases["existing_word_paragraph_revision"]["primary"],
        )
        self.assertEqual("report-writing", cases["report_prose_only"]["primary"])


if __name__ == "__main__":
    unittest.main()
