#!/usr/bin/env python3
"""Interactively install EpiClaude for Claude Code, Codex, or both."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


PRESETS = {
    "ppt": {
        "biostat-principles",
        "publication-figures",
        "svg-diagrams",
        "sysu-ppt",
        "pptx",
    },
    "writing": {
        "biostat-principles",
        "academic-humanizer",
        "academic-publishing",
        "report-writing",
        "publication-figures",
        "svg-diagrams",
        "docx",
        "xlsx",
    },
    "analysis": {
        "biostat-principles",
        "r-biostats",
        "publication-figures",
        "xlsx",
    },
}

DEPENDENCIES = {
    "academic-publishing": {
        "biostat-principles",
        "academic-humanizer",
        "publication-figures",
        "svg-diagrams",
    },
    "consulting-delivery": {
        "biostat-principles",
        "r-biostats",
        "academic-humanizer",
    },
    "epi-project-audit": {"biostat-principles"},
    "project-init": {"biostat-principles"},
    "publication-figures": {"biostat-principles"},
    "r-biostats": {"biostat-principles", "publication-figures"},
    "report-writing": {
        "academic-humanizer",
        "publication-figures",
        "svg-diagrams",
        "docx",
    },
    "sysu-ppt": {"publication-figures", "svg-diagrams", "pptx"},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", choices=("claude", "codex", "all"))
    parser.add_argument(
        "--preset",
        choices=("rules", "ppt", "writing", "analysis", "custom", "full"),
    )
    parser.add_argument("--skills", action="append", help="Comma-separated custom skills")
    parser.add_argument("--with-rules", action="store_true")
    parser.add_argument("--with-hooks", action="store_true")
    parser.add_argument("--yes", action="store_true", help="Skip final confirmation")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--home", type=Path)
    parser.add_argument("--codex-skills-dir", type=Path)
    return parser.parse_args()


def available_skills(root: Path) -> list[str]:
    return sorted(
        item.name
        for item in (root / "skills").iterdir()
        if item.is_dir() and (item / "SKILL.md").is_file()
    )


def csv_values(values: list[str] | None) -> set[str]:
    result: set[str] = set()
    for value in values or []:
        result.update(item.strip() for item in value.split(",") if item.strip())
    return result


def expand_dependencies(selected: set[str]) -> set[str]:
    expanded = set(selected)
    changed = True
    while changed:
        changed = False
        for skill in tuple(expanded):
            additions = DEPENDENCIES.get(skill, set()) - expanded
            if additions:
                expanded.update(additions)
                changed = True
    return expanded


def ask_choice(prompt: str, choices: dict[str, str]) -> str:
    print(prompt)
    for key, label in choices.items():
        print(f"  {key}. {label}")
    while True:
        answer = input("选择：").strip()
        if answer in choices:
            return answer
        print("输入无效，请重新选择。")


def ask_yes_no(prompt: str, default: bool = False) -> bool:
    suffix = "[Y/n]" if default else "[y/N]"
    answer = input(f"{prompt} {suffix} ").strip().lower()
    if not answer:
        return default
    return answer in {"y", "yes", "是"}


def interactive_values(
    args: argparse.Namespace, root: Path
) -> tuple[str, str, set[str], bool, bool]:
    prompted = args.target is None or args.preset is None
    target = args.target
    if target is None:
        key = ask_choice(
            "选择目标平台：",
            {"1": "Claude Code", "2": "Codex", "3": "Claude Code + Codex"},
        )
        target = {"1": "claude", "2": "codex", "3": "all"}[key]

    preset = args.preset
    if preset is None:
        key = ask_choice(
            "选择导入范围：",
            {
                "1": "仅共享规则",
                "2": "PPT 与 SVG 图解技能包",
                "3": "论文与报告技能包",
                "4": "统计分析技能包",
                "5": "自选 skills",
                "6": "完整环境（规则 + 全部 skills + hooks）",
            },
        )
        preset = {
            "1": "rules",
            "2": "ppt",
            "3": "writing",
            "4": "analysis",
            "5": "custom",
            "6": "full",
        }[key]

    selected = csv_values(args.skills)
    if preset == "custom" and not selected:
        names = available_skills(root)
        print("可选 skills：")
        print(", ".join(names))
        selected = {
            item.strip()
            for item in input("输入 skill 名，多个用逗号分隔：").split(",")
            if item.strip()
        }

    with_rules = args.with_rules
    with_hooks = args.with_hooks
    if preset not in {"rules", "full"} and prompted:
        if not args.with_rules:
            with_rules = ask_yes_no("同时覆盖共享规则？", default=False)
        if not args.with_hooks:
            with_hooks = ask_yes_no("同时安装 hooks？", default=False)
    return target, preset, selected, with_rules, with_hooks


def plan_install(
    preset: str, selected: set[str], with_rules: bool, with_hooks: bool
) -> tuple[set[str], set[str] | None]:
    if preset == "full":
        return {"rules", "skills", "hooks"}, None
    if preset == "rules":
        return {"rules"}, set()

    skills = set(PRESETS.get(preset, set())) if preset != "custom" else set(selected)
    skills = expand_dependencies(skills)
    components = {"skills"}
    if with_rules:
        components.add("rules")
    if with_hooks:
        components.add("hooks")
    return components, skills


def main() -> int:
    args = parse_args()
    root = args.repo_root.expanduser().resolve()
    if not (root / "scripts" / "sync_user_configs.py").is_file():
        raise FileNotFoundError(f"Not an EpiClaude repository: {root}")

    if not sys.stdin.isatty() and (args.target is None or args.preset is None):
        raise SystemExit("非交互运行必须同时指定 --target 与 --preset。")

    target, preset, selected, with_rules, with_hooks = interactive_values(args, root)
    components, skills = plan_install(preset, selected, with_rules, with_hooks)

    available = set(available_skills(root))
    unknown = (skills or set()) - available
    if unknown:
        raise SystemExit("未知 skills：" + ", ".join(sorted(unknown)))
    if preset == "custom" and not skills:
        raise SystemExit("自选模式至少需要一个 skill。")

    print("\n配置计划")
    print(f"- 平台：{target}")
    print(f"- 组件：{', '.join(sorted(components))}")
    print(f"- Skills：{'全部' if skills is None else ', '.join(sorted(skills))}")
    print("- 行为：覆盖同名 EpiClaude 文件，保留无关个人配置")

    if not args.yes:
        if not sys.stdin.isatty():
            raise SystemExit("非交互运行请加 --yes，或先用 --dry-run 检查。")
        if not ask_yes_no("执行以上配置？", default=True):
            print("已取消。")
            return 0

    sys.stdout.flush()

    command = [
        sys.executable,
        str(root / "scripts" / "sync_user_configs.py"),
        "--target",
        target,
        "--repo-root",
        str(root),
        "--components",
        ",".join(sorted(components)),
    ]
    if skills is not None:
        command.extend(("--skills", ",".join(sorted(skills))))
    if args.home:
        command.extend(("--home", str(args.home)))
    if args.codex_skills_dir:
        command.extend(("--codex-skills-dir", str(args.codex_skills_dir)))
    if args.dry_run:
        command.append("--dry-run")

    result = subprocess.run(command, cwd=root)
    if result.returncode:
        return result.returncode
    if args.dry_run:
        print("演练完成，未写入用户配置。")
    else:
        print("配置完成。若客户端未识别新 skills，请重启对应客户端。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
