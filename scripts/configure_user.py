#!/usr/bin/env python3
"""Install shared rules, skills, and hooks for Claude Code, Codex, or both."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from config_core import (
    CODEX_COMPATIBILITY_WARNING,
    PRESETS,
    available_skills,
    csv_values,
    expand_dependencies,
)


def parse_args(
    argv: list[str] | None = None, prog: str | None = None
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog=prog, description=__doc__)
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
    parser.add_argument("--codex-skills-dir", type=Path, action="append")
    parser.add_argument(
        "--codex-layout",
        choices=("auto", "agents", "codex", "both"),
        default="auto",
    )
    parser.add_argument("--skip-doctor", action="store_true")
    return parser.parse_args(argv)


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
                "2": "PPT 与 imagegen 图解技能包",
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


def main(argv: list[str] | None = None, prog: str | None = None) -> int:
    args = parse_args(argv, prog)
    root = args.repo_root.expanduser().resolve()
    if not (root / "scripts" / "sync_user_configs.py").is_file():
        raise FileNotFoundError(f"Not an EpiAgentKit repository: {root}")

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
    print("- 行为：覆盖同名 EpiAgentKit 文件，保留无关个人配置")
    if "skills" in components:
        print(
            "- 冲突门禁：安装前遍历 Skill 发现目录；同名或触发范围冲突的 "
            "本地 Skill 将直接删除（--dry-run 仅预览）"
        )
    if target in {"codex", "all"}:
        print(f"- Codex skills 布局：{args.codex_layout}")
        if args.codex_layout in {"codex", "both"}:
            print(f"- {CODEX_COMPATIBILITY_WARNING}")
    if "hooks" in components:
        print("- Hooks：复制脚本并合并客户端配置；Windows 自动使用 Git Bash 启动器")

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
    for directory in args.codex_skills_dir or []:
        command.extend(("--codex-skills-dir", str(directory)))
    command.extend(("--codex-layout", args.codex_layout))
    if args.dry_run:
        command.append("--dry-run")

    result = subprocess.run(command, cwd=root)
    if result.returncode:
        return result.returncode
    if args.dry_run:
        print("演练完成，未写入用户配置。")
    else:
        if not args.skip_doctor:
            doctor = [
                sys.executable,
                str(root / "scripts" / "epiagentkit.py"),
                "doctor",
                "--target",
                target,
                "--repo-root",
                str(root),
                "--codex-layout",
                args.codex_layout,
            ]
            if args.home:
                doctor.extend(("--home", str(args.home)))
            for directory in args.codex_skills_dir or []:
                doctor.extend(("--codex-skills-dir", str(directory)))
            checked = subprocess.run(doctor, cwd=root)
            if checked.returncode:
                return checked.returncode
        print("配置与双端验收完成。若客户端未刷新，请重启对应客户端。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
