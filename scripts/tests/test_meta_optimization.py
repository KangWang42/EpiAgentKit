from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


class MetaOptimizationCapabilityTests(unittest.TestCase):
    def test_optimization_playbook_is_linked_conditionally_and_covers_core_loops(self) -> None:
        maint = read("skills/epiagentkit-maintenance/SKILL.md")
        playbook = read("skills/epiagentkit-maintenance/references/optimization-playbook.md")

        self.assertIn("references/optimization-playbook.md", maint)
        self.assertIn("audit_skill_contracts.py --budget", maint)
        for fragment in (
            "触发层与执行层分离诊断",
            "上下文预算与定期减脂",
            "评测驱动的 A/B 迭代",
            "吸收外部实践与优秀仓库",
            "history summary --since-last",
            "history mark",
        ):
            self.assertIn(fragment, playbook)

    def test_skill_creator_separates_discovery_from_execution_and_enforces_budgets(self) -> None:
        creator = read("skills/skill-creator/SKILL.md")
        self.assertIn("Separate discovery failures from execution failures", creator)
        self.assertIn("finite attention budgets", creator)
        self.assertIn("reject additions that raise context or tool overhead", creator)

    def test_audit_skill_contracts_budget_mode_reports_live_telemetry(self) -> None:
        proc = subprocess.run(
            [sys.executable, "scripts/audit_skill_contracts.py", "--budget", "--json"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        data = json.loads(proc.stdout)
        self.assertGreaterEqual(data["public_skill_count"], 20)
        self.assertGreater(data["listing_chars"], 0)
        self.assertLessEqual(data["claude_md"]["chars"], 12000)
        self.assertIsInstance(data["heavy_skills"], list)
        self.assertIsInstance(data["unreferenced_top_refs"], list)

        human = subprocess.run(
            [sys.executable, "scripts/audit_skill_contracts.py", "--budget"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(human.returncode, 0, human.stdout + human.stderr)
        self.assertIn("Skill contract audit: PASS", human.stdout)
        self.assertIn("Context budget:", human.stdout)

    def test_round1_progressive_disclosure_skills_stay_under_16kb_budget(self) -> None:
        proc = subprocess.run(
            [sys.executable, "scripts/audit_skill_contracts.py", "--budget", "--json"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        data = json.loads(proc.stdout)
        by_skill = {item["skill"]: item for item in data["skills"]}
        for skill_name in ("sysu-ppt", "research-visuals", "build-web-ui"):
            entry = by_skill[skill_name]
            self.assertLessEqual(
                entry["bytes"],
                data["heavy_threshold_bytes"],
                f"{skill_name} exceeded Layer-2 budget: {entry['bytes']} B",
            )
            self.assertEqual(
                entry["unreferenced_top_refs"],
                [],
                f"{skill_name} has unreferenced top-level references",
            )


if __name__ == "__main__":
    unittest.main()
