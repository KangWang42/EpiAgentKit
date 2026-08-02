from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class RuntimeInstallPolicyTests(unittest.TestCase):
    def read(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_global_policy_installs_official_analysis_packages_in_project_env(self) -> None:
        rules = self.read("CLAUDE.md")
        for fragment in (
            "不自行安装或升级 R、Python",
            "普通 R/Python 分析包",
            "安装到项目隔离环境",
            "不改用户级、全局或 Codex/插件共享环境",
            "不默认追求最新版",
            "从非官方来源安装前必须先征得用户同意",
            "不得静默改用非等价包、方法或分析语言",
            "用户不同意时按等价实现规则提供现有环境内备选",
            "Git 只在命令可用且当前目录为仓库时使用",
            "不安装 Git，也不隐式初始化仓库",
            "只有用户在 `project-init` 中明确启用 Git 时",
        ):
            self.assertIn(fragment, rules)

    def test_git_is_optional_and_never_installed(self) -> None:
        expected = {
            "AGENTS.md": (
                "only when Git is available and the current directory is a repository",
                "do not initialize a repository or install Git",
            ),
            "skills/git-commit-helper/SKILL.md": (
                "Git is already available",
                "Do not install Git",
                "do not run `git init`",
            ),
            "skills/project-init/SKILL.md": (
                "不安装 Git",
                "git=TRUE",
                "Git 已存在时初始化",
            ),
            "skills/project-init/scripts/init_project.R": (
                'Sys.which("git")',
                'git_state <- "unavailable"',
                'git = FALSE',
            ),
        }
        for relative, fragments in expected.items():
            body = self.read(relative)
            for fragment in fragments:
                self.assertIn(fragment, body, relative)

    def test_analysis_skills_follow_shared_install_first_policy(self) -> None:
        expected = {
            "skills/biostat-principles/SKILL.md": (
                "references/runtime-dependencies.md",
                "普通分析包只装入项目隔离环境",
                "不得静默换包、换方法或换语言",
            ),
            "skills/r-biostats/SKILL.md": (
                "普通 R 包缺失时",
                "项目隔离环境补齐",
                "失败不得静默换包、换方法或改用 Python",
            ),
            "skills/python-biostats/SKILL.md": (
                "普通 Python 包缺失时",
                "项目隔离环境补齐",
                "失败不得静默换包、换方法或换语言",
                "用户不安装则评估现有 R 环境中的经核验等价实现",
            ),
            "skills/publication-figures/SKILL.md": (
                "普通包缺失按依赖分流",
                "用户不安装时优先验证现有 R 环境中的等价实现",
                "不得自动安装其中依赖",
                "不得把它们作为方法或样式依据",
            ),
        }
        for relative, fragments in expected.items():
            body = self.read(relative)
            for fragment in fragments:
                self.assertIn(fragment, body, relative)

    def test_shared_dependency_policy_preserves_install_boundaries(self) -> None:
        policy = self.read(
            "skills/biostat-principles/references/runtime-dependencies.md"
        )
        for fragment in (
            "只有普通分析包进入自动安装",
            "不得写入用户级、系统级、全局 site-library",
            "只安装缺失包及必要的传递依赖",
            "不为追求最新版升级无关包",
            "安装失败时，停下并报告",
            "未经同意不得改用功能相近的包",
        ):
            self.assertIn(fragment, policy)

    def test_delivery_reproduction_still_does_not_change_environment(self) -> None:
        body = self.read("skills/consulting-delivery/SKILL.md")
        self.assertIn("现有且版本兼容的 R 或 Python 环境", body)
        self.assertIn("此阶段不现场安装或升级依赖", body)

    def test_file_skills_do_not_present_install_commands_as_defaults(self) -> None:
        forbidden = {
            "skills/docx/SKILL.md": ("Install: `npm install -g docx`",),
            "skills/pptx/SKILL.md": (
                '`pip install "markitdown[pptx]"`',
                "`pip install Pillow`",
                "`npm install -g pptxgenjs`",
            ),
            "skills/pptx/pptxgenjs.md": (
                "Install: `npm install -g react-icons react react-dom sharp`",
            ),
            "skills/pdf/SKILL.md": (
                "# Requires: pip install pytesseract pdf2image",
            ),
            "skills/xlsx/SKILL.md": ("You can assume LibreOffice is installed",),
        }
        for relative, fragments in forbidden.items():
            body = self.read(relative)
            for fragment in fragments:
                self.assertNotIn(fragment, body, relative)

    def test_file_skills_explain_missing_prerequisites_without_installing(self) -> None:
        expected = {
            "skills/docx/SKILL.md": "without installing it",
            "skills/pptx/SKILL.md": "do not install or upgrade it",
            "skills/pdf/SKILL.md": "do not install them",
            "skills/xlsx/SKILL.md": "do not install it",
        }
        for relative, marker in expected.items():
            body = self.read(relative)
            self.assertIn(marker, body, relative)
            self.assertIn("user", body.lower(), relative)

    def test_missing_pyyaml_reports_choice_without_installing(self) -> None:
        body = self.read("skills/epi-project-audit/scripts/check_consistency.py")
        self.assertIn("请先选择要使用的 Python 环境和安装方式", body)
        self.assertIn("本检查器不会自动安装或升级依赖", body)
        self.assertNotIn("pip install pyyaml", body)


if __name__ == "__main__":
    unittest.main()
