from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class RuntimeInstallPolicyTests(unittest.TestCase):
    def read(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_global_policy_reuses_compatible_existing_environments(self) -> None:
        rules = self.read("CLAUDE.md")
        for fragment in (
            "复用已有兼容环境",
            "不负责安装或升级 R、Python",
            "不默认追求最新版",
            "只说明检测结果、影响与用户下一步可执行的准备方式",
            "不代用户创建环境或执行安装、升级、降级命令",
            "Git 只在命令可用时使用",
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
                "Git 不可用时跳过版本管理",
                "不安装 Git",
                "Git 已跳过",
            ),
            "skills/project-init/scripts/init_project.R": (
                'Sys.which("git")',
                'git_state <- "unavailable"',
                "未安装 Git",
            ),
        }
        for relative, fragments in expected.items():
            body = self.read(relative)
            for fragment in fragments:
                self.assertIn(fragment, body, relative)

    def test_analysis_and_delivery_skills_do_not_install_missing_dependencies(self) -> None:
        expected = {
            "skills/r-biostats/SKILL.md": (
                "依赖或运行环境缺失时说明检测结果",
                "不代为安装",
            ),
            "skills/consulting-delivery/SKILL.md": (
                "复现检查只使用本机已有的兼容 R/Python 环境",
                "不得创建虚拟环境或执行安装、升级命令",
            ),
            "skills/publication-figures/SKILL.md": (
                "配方库中的 `install.packages()`",
                "不得执行或复制进主流程",
                "让用户自行准备后再继续",
            ),
        }
        for relative, fragments in expected.items():
            body = self.read(relative)
            for fragment in fragments:
                self.assertIn(fragment, body, relative)

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
            "skills/docx/SKILL.md": "do not install it",
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
