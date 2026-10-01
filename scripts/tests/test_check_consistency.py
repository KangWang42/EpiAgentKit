import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills" / "epi-project-audit" / "scripts" / "check_consistency.py"
MANIFEST = """version: 2
results:
  hr_smoking:
    display: {estimate: "1.45", interval: "（95% CI：1.12，1.87）", p_value: "P = 0.004", full: "1.45（95% CI：1.12，1.87）"}
  md_bmi:
    display: {estimate: "−0.32", interval: "（95% CI：−0.58，−0.06）", p_value: "P < 0.001"}
"""


def run(manuscript: str) -> subprocess.CompletedProcess:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        (root / "results").mkdir()
        (root / "paper").mkdir()
        (root / "results" / "results.yaml").write_text(MANIFEST, encoding="utf-8")
        (root / "paper" / "manuscript.md").write_text(manuscript, encoding="utf-8")
        return subprocess.run([sys.executable, str(SCRIPT), str(root)], capture_output=True,
                              text=True, encoding="utf-8", env={"PYTHONIOENCODING": "utf-8", **__import__("os").environ})


class CheckConsistencyTests(unittest.TestCase):
    def test_equivalent_formats_pass(self) -> None:
        done = run("HR 1.45 (95% CI 1.12–1.87), P = .004; BMI -0.32 (95% CI -0.58 to -0.06), P < 0.001. "
                   "HR 1.45（95% CI：1.12，1.870）")
        self.assertEqual(done.returncode, 0, done.stdout)

    def test_wrong_interval_in_any_separator_is_reported(self) -> None:
        for text in ("HR 1.45 (95% CI 1.12–1.78)", "HR 1.45 (95% CI, 1.12 to 1.78)", "(95% CI: 1.12, 1.78)"):
            done = run(text)
            self.assertEqual(done.returncode, 1, text)
            self.assertIn("1.12, 1.78", done.stdout)

    def test_wrong_estimate_with_correct_interval_is_reported(self) -> None:
        done = run("HR 1.54 (95% CI 1.12–1.87)")
        self.assertEqual(done.returncode, 1)
        self.assertIn("估计值: 1.54", done.stdout)

    def test_wrong_p_value_is_reported(self) -> None:
        done = run("HR 1.45 (95% CI 1.12–1.87), P = 0.04")
        self.assertEqual(done.returncode, 1)
        self.assertIn("P = 0.04", done.stdout)


if __name__ == "__main__":
    unittest.main()
