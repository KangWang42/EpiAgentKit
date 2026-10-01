import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "hooks"))
SPEC = importlib.util.spec_from_file_location("final_project_check", ROOT / "hooks" / "final_project_check.py")
check = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = check
SPEC.loader.exec_module(check)


class SecretScanTests(unittest.TestCase):
    def test_font_and_system_paths_are_not_secrets(self) -> None:
        for value in (
            "/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman.ttf",
            "/System/Library/Fonts/PingFang.ttc",
            "C:/Windows/Fonts/timesbd.ttf",
        ):
            self.assertTrue(check.benign_high_entropy(value, Path("fig_setup.R")), value)

    def test_credential_shaped_tokens_are_still_reported(self) -> None:
        for value in (
            "/K7MDENG/bPxRfiCYEXAMPLEKEYwJalrXUtnFEMIa9",
            "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "ghp_aB3dE5fG7hJ9kL1mN3pQ5rS7tU9vW1xY3zA5",
        ):
            self.assertFalse(check.benign_high_entropy(value, Path("analysis.R")), value)

    def test_shipped_figure_helper_has_no_secret_findings(self) -> None:
        helper = ROOT / "skills" / "publication-figures" / "scripts" / "fig_setup.R"
        flagged = []
        for number, line in enumerate(helper.read_text(encoding="utf-8").splitlines(), start=1):
            for match in check.TOKEN_PATTERN.finditer(line):
                value = match.group(0)
                if check.benign_high_entropy(value, helper):
                    continue
                classes = sum((
                    any(c.islower() for c in value), any(c.isupper() for c in value),
                    any(c.isdigit() for c in value), any(not c.isalnum() for c in value),
                ))
                if classes >= 3 and len(set(value)) >= 8 and check.entropy(value) >= 4.0:
                    flagged.append((number, value))
        self.assertEqual(flagged, [])


if __name__ == "__main__":
    unittest.main()
