from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


class FitForPurposeContractsTests(unittest.TestCase):
    def test_biostats_skills_restrain_unrequested_models_and_routine_diagnostics(self) -> None:
        principles = read("skills/biostat-principles/SKILL.md")
        r_skill = read("skills/r-biostats/SKILL.md")
        r_reg = read("skills/r-biostats/references/regression.md")
        py_skill = read("skills/python-biostats/SKILL.md")

        self.assertIn("不自动追加逐步调整模型", principles)
        self.assertIn("原量表标准", principles)
        self.assertIn("原量表公认标准", r_skill)
        self.assertIn("高参数附表模型", r_skill)
        self.assertIn("不自动替换标准估计方法", r_reg)
        self.assertIn("克制模型复杂度", py_skill)
        self.assertIn("增量偏移、局部切片或本地可重建索引", principles)

    def test_maintenance_exposes_incremental_history_index(self) -> None:
        maint = read("skills/epiagentkit-maintenance/SKILL.md")
        self.assertIn("scripts/history_index.py", maint)
        self.assertIn("字节偏移增量同步", maint)

    def test_xlsx_defaults_to_clean_tables_without_unrequested_freeze_or_tooltips(self) -> None:
        xlsx = read("skills/xlsx/SKILL.md")
        self.assertIn("冻结窗格、自动筛选按钮、单元格批注或悬浮提示", xlsx)
        self.assertIn("不擅自按填充色或排序规则重排组内条目", xlsx)

    def test_academic_ppt_supports_fast_meeting_incremental_edits_and_deck_merge(self) -> None:
        ppt = read("skills/academic-ppt/SKILL.md")
        meeting = read("skills/academic-ppt/references/meeting-and-journal-club.md")

        self.assertIn("严格保留用户改动过的文字与版式", ppt)
        self.assertIn("把两份 PPT 融合时", ppt)
        self.assertIn("不出现内部文件名或核查文档引用", ppt)
        self.assertIn("不强制插入总思路概览页", meeting)

    def test_build_web_ui_codifies_anti_patterns_and_lightweight_iteration_path(self) -> None:
        web = read("skills/build-web-ui/SKILL.md")
        playbook = read("skills/build-web-ui/references/design-playbook.md")

        self.assertIn("不平铺一排大按钮或生硬文字按钮", web)
        self.assertIn("极淡浅底配高对比正文", web)
        self.assertIn("不机械附加“AI”前缀", web)
        self.assertIn("针对个人工具与日常迭代明确要求快速完成", web)
        self.assertIn("同排卡片使用等高网格", playbook)
        self.assertIn("24 寸宽屏", playbook)

    def test_cross_agent_cold_start_and_efficient_indexing_contracts(self) -> None:
        rules = read("CLAUDE.md")
        init_skill = read("skills/project-init/SKILL.md")
        init_r = read("skills/project-init/scripts/init_project.R")

        self.assertIn("新会话、换 Agent 或续接先读项目入口、计划、当前产物与未决项", rules)
        self.assertIn("增量索引", rules)
        self.assertIn("供任意 AI / Agent 新会话快速接手", init_skill)
        self.assertIn("# 通用 Agent 项目指引", init_r)
        self.assertIn("当前正式产物与入口", init_r)


if __name__ == "__main__":
    unittest.main()
