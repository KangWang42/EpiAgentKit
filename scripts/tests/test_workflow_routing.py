from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from config_core import expand_dependencies


class WorkflowRoutingTests(unittest.TestCase):
    def test_global_routes_align_python_ecg_with_principles(self) -> None:
        global_rules = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        route = "`biostat-principles` → `python-ecg-analysis`"
        self.assertIn(route, global_rules)
        self.assertIn(route, readme)

    def test_python_ecg_installs_principles_and_figure_companion(self) -> None:
        expanded = expand_dependencies({"python-ecg-analysis"})
        self.assertIn("biostat-principles", expanded)
        self.assertIn("publication-figures", expanded)

    def test_readme_keeps_statistical_and_writing_boundaries_narrow(self) -> None:
        body = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("发表级统计图与数据图规范", body)
        self.assertIn("逐部件内部闭环写作", body)
        self.assertIn("审查（六层）在发现失败后继续收集全部证据", body)
        self.assertNotIn("逐部件门控写作", body)
        self.assertNotIn('审查（六层）都是"不过检不许进下一步"', body)

    def test_publication_figures_trigger_is_statistical(self) -> None:
        body = (ROOT / "skills" / "publication-figures" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("发表级统计图、数据图", body)
        self.assertIn("非统计视觉不触发本技能", body)
        self.assertNotIn("用户要求出图、画图、做图、生成 Fig", body)

    def test_results_machine_source_is_not_the_derived_markdown(self) -> None:
        body = (
            ROOT
            / "skills"
            / "academic-publishing"
            / "references"
            / "chinese-thesis.md"
        ).read_text(encoding="utf-8")
        self.assertIn("数字机器单源 = `07_paper/results.yaml`", body)
        self.assertNotIn("结果变 → 回写 `0_result_summaries.md`", body)

    def test_audit_continues_all_layers_but_blocks_signoff(self) -> None:
        body = (ROOT / "skills" / "epi-project-audit" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("继续完成其余层审查", body)
        self.assertIn("任何未闭环的 fail 都阻止签发", body)
        self.assertIn("仅在“审查并修复”模式", body)
        self.assertNotIn("不通过不进入下一层", body)
        self.assertNotIn("### 自动修复动作", body)

        checklist = (
            ROOT
            / "skills"
            / "epi-project-audit"
            / "references"
            / "audit-checklist.md"
        ).read_text(encoding="utf-8")
        self.assertIn("`results.yaml` ↔ 派生 `0_result_summaries.md`", checklist)


if __name__ == "__main__":
    unittest.main()
