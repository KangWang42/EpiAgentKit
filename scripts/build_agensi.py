#!/usr/bin/env python3
"""Build one standalone Agensi marketplace zip per sellable EpiAgentKit skill.

Each archive contains a single top-level folder named after the skill with
SKILL.md at its root. Files referenced from other skills are copied into
``shared/<skill>/`` with their original layout, and the root working rules are
shipped as ``references/core-rules.md``. Source skills are never modified.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import posixpath
import re
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from build_release import FIXED_ZIP_TIME, IGNORED_NAMES, IGNORED_PARTS, IGNORED_SUFFIXES

# publication-figures ships only its vetted files; the recipe folders are
# third-party material without redistribution rights.
FILE_ALLOWLIST = {
    "publication-figures": {
        "SKILL.md",
        "references/chart-gallery.md",
        "references/manuscript-layout.md",
        "references/recipe-quarantine.md",
        "scripts/fig_setup.R",
    },
}
TEXT_SUFFIXES = {
    ".css", ".csv", ".html", ".js", ".json", ".md", ".py", ".r", ".sh",
    ".svg", ".toml", ".tsv", ".txt", ".xml", ".yaml", ".yml",
}
TEXT_NAMES = {"LICENSE"}
EXECUTABLE_SUFFIXES = {".py", ".r", ".sh"}
# CLAUDE.md bullets tied to the author's own repositories or Windows shell setup.
CORE_RULE_EXCLUDED_PREFIXES = ("- Git ", "- 已有仓库", "- Windows PowerShell 处理")
SECRET_PATTERN = re.compile(
    r"(?i)(?:api[_-]?key|access[_-]?token|secret|password)\s*[:=]\s*['\"][A-Za-z0-9_\-]{12,}['\"]"
    r"|sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{30,}|AKIA[0-9A-Z]{16}"
)
USER_PATH_PATTERN = re.compile(r"(?i)(?:[A-Z]:[\\/]Users[\\/][^\\/\s]+|/Users/[^/\s]+|/home/[^/\s]+)")
MD_LINK_PATTERN = re.compile(r"\]\(([^)\s#]+)(#[^)\s]*)?\)")


class BuildError(RuntimeError):
    pass


@dataclass
class Package:
    name: str
    files: dict[str, bytes] = field(default_factory=dict)
    companions: set[str] = field(default_factory=set)
    warnings: list[str] = field(default_factory=list)


def is_ignored(relative: PurePosixPath) -> bool:
    return (
        relative.name in IGNORED_NAMES
        or relative.name.startswith(".")
        or relative.suffix.lower() in IGNORED_SUFFIXES
        or bool(set(relative.parts) & IGNORED_PARTS)
    )


def skill_files(skills_root: Path, skill: str) -> dict[str, Path]:
    base = skills_root / skill
    if not (base / "SKILL.md").is_file():
        raise BuildError(f"Skill is missing SKILL.md: {skill}")
    allow = FILE_ALLOWLIST.get(skill)
    found: dict[str, Path] = {}
    for path in sorted(base.rglob("*")):
        if not path.is_file():
            continue
        relative = PurePosixPath(path.relative_to(base).as_posix())
        if is_ignored(relative) or (allow is not None and relative.as_posix() not in allow):
            continue
        if path.is_symlink():
            raise BuildError(f"Symbolic link is not allowed: {skill}/{relative}")
        found[relative.as_posix()] = path
    return found


def cross_reference_pattern(skill_names: list[str]) -> re.Pattern[str]:
    names = "|".join(sorted((re.escape(name) for name in skill_names), key=len, reverse=True))
    return re.compile(
        r"(?<![\w./-])((?:\.\./)*)(skills/)?(" + names + r")/((?:references|scripts|assets|agents)/[\w./-]*[\w-])"
    )


def split_frontmatter(text: str) -> tuple[str, str]:
    match = re.match(r"---\r?\n(.*?)\r?\n---\r?\n", text, flags=re.S)
    if not match:
        raise BuildError("SKILL.md has no YAML frontmatter")
    return match.group(1), text[match.end():]


def frontmatter_value(frontmatter: str, key: str) -> str:
    match = re.search(rf"^{key}:\s*(.*?)(?=^\S|\Z)", frontmatter, flags=re.M | re.S)
    if not match:
        raise BuildError(f"Frontmatter field is missing: {key}")
    value = match.group(1).strip()
    if value.startswith("|") or value.startswith(">"):
        value = " ".join(line.strip() for line in value.splitlines()[1:])
    return value.strip().strip('"').strip("'")


class Builder:
    def __init__(self, repo_root: Path, listings: dict) -> None:
        self.repo_root = repo_root
        self.skills_root = repo_root / "skills"
        self.listings = listings
        self.sellable = list(listings["skills"])
        self.external = listings["external_companions"]
        all_skills = sorted(p.name for p in self.skills_root.iterdir() if (p / "SKILL.md").is_file())
        self.all_skills = all_skills
        self.cross_pattern = cross_reference_pattern(all_skills)
        self.companion_pattern = re.compile(
            r"`(" + "|".join(re.escape(n) for n in sorted(set(all_skills) | set(self.external), key=len, reverse=True)) + r")`"
        )
        self.sources = {skill: skill_files(self.skills_root, skill) for skill in all_skills}

    # --- path mapping -----------------------------------------------------
    def package_path(self, package: str, owner: str, relative: str) -> str:
        return relative if owner == package else f"shared/{owner}/{relative}"

    def resolve_markdown_target(self, owner: str, file_relative: str, target: str) -> tuple[str, str] | None:
        """Return (skill, relative path) for a relative link inside skills/, else None."""
        if re.match(r"^[a-z]+:", target) or target.startswith("/"):
            return None
        joined = posixpath.normpath(posixpath.join(owner, posixpath.dirname(file_relative), target))
        parts = joined.split("/")
        if not parts or parts[0] not in self.sources or len(parts) < 2:
            return None
        return parts[0], "/".join(parts[1:])

    # --- content rewriting ------------------------------------------------
    def rewrite_markdown(self, pkg: Package, owner: str, relative: str, text: str, queue: list) -> str:
        own_location = self.package_path(pkg.name, owner, relative)

        def replace_link(match: re.Match[str]) -> str:
            target, anchor = match.group(1), match.group(2) or ""
            resolved = self.resolve_markdown_target(owner, relative, target)
            if resolved is None:
                return match.group(0)
            skill, rest = resolved
            if skill == owner and owner == pkg.name:
                return match.group(0)
            if skill not in self.sellable or rest not in self.sources[skill]:
                pkg.warnings.append(f"{own_location}: link to unavailable {skill}/{rest} kept as text")
                return f"]({target}{anchor})"
            queue.append((skill, rest))
            new_target = posixpath.relpath(
                self.package_path(pkg.name, skill, rest), posixpath.dirname(own_location) or "."
            )
            return f"]({new_target}{anchor})"

        text = MD_LINK_PATTERN.sub(replace_link, text)

        def replace_mention(match: re.Match[str]) -> str:
            dots, prefix, skill, rest = match.groups()
            if skill == pkg.name:
                return f"<skill-dir>/{rest}" if prefix else match.group(0)
            if skill not in self.sellable:
                return f"<{skill}-skill-dir>/{rest}" if prefix else match.group(0)
            if rest not in self.sources[skill]:
                pkg.warnings.append(f"{own_location}: mention of missing {skill}/{rest} kept as text")
                return match.group(0)
            queue.append((skill, rest))
            mapped = self.package_path(pkg.name, skill, rest)
            return f"<skill-dir>/{mapped}" if prefix else mapped

        text = self.cross_pattern.sub(replace_mention, text)
        if owner != pkg.name:
            # Unprefixed references/... paths inside a copied file are rooted at shared/<owner>/.
            for match in re.finditer(r"(?<![\w./-])((?:references|scripts|assets)/[\w./-]*[\w-])", text):
                if match.group(1) in self.sources[owner]:
                    queue.append((owner, match.group(1)))
        for name in self.companion_pattern.findall(text):
            if name != pkg.name:
                pkg.companions.add(name)
        return text

    def add_file(self, pkg: Package, owner: str, relative: str, queue: list) -> None:
        location = self.package_path(pkg.name, owner, relative)
        if location in pkg.files:
            return
        data = self.sources[owner][relative].read_bytes()
        if relative.endswith(".md"):
            text = data.decode("utf-8-sig")
            pkg.files[location] = b""  # reserve before recursion
            data = self.rewrite_markdown(pkg, owner, relative, text, queue).encode("utf-8")
        pkg.files[location] = data

    # --- generated files --------------------------------------------------
    def core_rules(self) -> str:
        text = (self.repo_root / "CLAUDE.md").read_text(encoding="utf-8-sig")
        body = text.split("\n", 1)[1]
        kept = [line for line in body.splitlines() if not line.startswith(CORE_RULE_EXCLUDED_PREFIXES)]
        return (
            "# 核心工作规则 | Core working rules\n\n"
            "> 本文件是作者在流行病学与生物统计工作中使用的全局规则，供正文中“全局规则”“根规则”或 `CLAUDE.md` 的引用使用。"
            "用户当轮指示和项目自身的 `CLAUDE.md` 优先于本文件；表格中列出的其它 skill 未安装时，按 "
            "[companion-skills.md](companion-skills.md) 处理。\n>\n"
            "> These are the author's global working rules referenced by this skill. The user's instructions and the "
            "project's own rules take precedence.\n"
            + "\n".join(kept).rstrip()
            + "\n"
        )

    def skill_summary(self, skill: str) -> str:
        if skill in self.sellable:
            listing = self.listings["skills"][skill]
            return f"{listing['description_en']} Available separately on Agensi as `{skill}`."
        return self.external.get(skill, "Not included in this package; skip steps that require it and tell the user.")

    def companion_file(self, pkg: Package) -> str:
        lines = [
            "# 配合使用的 skill | Companion skills",
            "",
            "正文提到的下列 skill 不在本 zip 内。已安装时按正文调用；未安装时由本 skill 按下表说明完成同一步骤，"
            "无法完成时向用户说明缺少的能力，不假装已经执行。`shared/<skill>/` 目录保存了本 skill 实际引用的对方文件，"
            "保持原目录结构；其中不带前缀的 `references/...` 路径以 `shared/<skill>/` 为根。",
            "",
            "The skills below are mentioned in this skill but not bundled. If one is not installed, perform the "
            "equivalent step yourself as described, or tell the user which capability is missing.",
            "",
            "| Skill | What it covers / fallback |",
            "| --- | --- |",
        ]
        for name in sorted(pkg.companions):
            lines.append(f"| `{name}` | {self.skill_summary(name)} |")
        if not pkg.companions:
            lines.append("| (none) | 本 skill 正文不依赖其它 skill；`core-rules.md` 表格中的其它 skill 均为可选。 |")
        return "\n".join(lines) + "\n"

    def readme(self, pkg: Package, chinese_description: str) -> str:
        listing = self.listings["skills"][pkg.name]
        lines = [
            f"# {listing['title']}",
            "",
            listing["description_en"],
            "",
            f"中文说明：{chinese_description}",
            "",
            "## What it does",
            "",
            *[f"- {item}" for item in listing["highlights"]],
            "",
            "## Install",
            "",
            f"Unzip and copy the `{pkg.name}/` folder into your agent's skills directory, for example "
            f"`~/.claude/skills/{pkg.name}/` for Claude Code or `~/.codex/skills/{pkg.name}/` for Codex CLI. "
            "The skill activates automatically when a request matches its description, or invoke it by name.",
            "",
            "## Requirements",
            "",
            listing["requirements"],
            "",
            "## Language",
            "",
            "The instructions are written in Chinese and work with requests in Chinese or English. "
            "正文为中文，支持中英文请求。",
            "",
        ]
        if listing.get("network_note") or listing.get("env_note"):
            lines += ["## Network and environment access", ""]
            if listing.get("network_note"):
                lines += [f"- Network: {listing['network_note']}"]
            if listing.get("env_note"):
                lines += [f"- Environment variables: {listing['env_note']}"]
            lines.append("")
        else:
            lines += ["## Network and environment access", "", "- None. All scripts work only on files you pass in.", ""]
        lines += [
            "## Package layout",
            "",
            "- `SKILL.md`: workflow and trigger description.",
            "- `references/core-rules.md`: the author's global working rules that the skill refers to.",
        ]
        lines.append("- `references/companion-skills.md`: other skills mentioned and what to do without them.")
        if any(path.startswith("shared/") for path in pkg.files):
            lines.append("- `shared/`: files from companion skills that this skill reads directly.")
        lines += ["", "## Safety", "", "Scripts only read and write inside the paths you give them. They do not install packages, change system settings or delete files outside the project.", ""]
        notices = sorted(path for path in pkg.files if PurePosixPath(path).name == "LICENSE")
        if notices:
            lines += ["## Third-party notices", ""]
            lines += [f"- `{path}`" for path in notices]
            lines.append("")
        lines += [f"Author: {self.listings['author']} · Version {self.listings['package_version']}", ""]
        return "\n".join(lines)

    # --- build ------------------------------------------------------------
    def build(self, skill: str) -> Package:
        pkg = Package(skill)
        queue: list[tuple[str, str]] = [(skill, rel) for rel in self.sources[skill]]
        while queue:
            owner, relative = queue.pop(0)
            if relative not in self.sources[owner]:
                continue
            self.add_file(pkg, owner, relative, queue)

        frontmatter, body = split_frontmatter(pkg.files["SKILL.md"].decode("utf-8"))
        chinese = frontmatter_value(frontmatter, "description")
        description = f"{self.listings['skills'][skill]['description_en']} {chinese}"
        new_frontmatter = f"name: {skill}\ndescription: {json.dumps(description, ensure_ascii=False)}"
        appendix = [
            "",
            "## 独立安装说明 | Standalone use",
            "",
            "- 正文中的“全局规则”“根规则”或 `CLAUDE.md` 规则指 [references/core-rules.md](references/core-rules.md)；用户当轮指示和项目自身规则优先。",
            "- `<skill-dir>` 指本 skill 的安装目录。",
        ]
        appendix.append(
            "- 正文提到的其它 skill 见 [references/companion-skills.md](references/companion-skills.md)；未安装时按其中说明完成相同步骤，或向用户说明缺少的能力。"
        )
        pkg.files["SKILL.md"] = (f"---\n{new_frontmatter}\n---\n{body.rstrip()}\n" + "\n".join(appendix) + "\n").encode("utf-8")
        pkg.files["references/core-rules.md"] = self.core_rules().encode("utf-8")
        pkg.files["references/companion-skills.md"] = self.companion_file(pkg).encode("utf-8")
        pkg.files["README.md"] = self.readme(pkg, chinese).encode("utf-8")
        self.validate(pkg)
        return pkg

    def validate(self, pkg: Package) -> None:
        for location, data in pkg.files.items():
            path = PurePosixPath(location)
            if path.is_absolute() or ".." in path.parts or path.name.startswith("."):
                raise BuildError(f"{pkg.name}: invalid archive path {location}")
            if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in TEXT_NAMES:
                raise BuildError(f"{pkg.name}: non-text file {location}")
            text = data.decode("utf-8")
            if "license: Proprietary" in text:
                raise BuildError(f"{pkg.name}: proprietary content in {location}")
            if USER_PATH_PATTERN.search(text):
                raise BuildError(f"{pkg.name}: user-profile absolute path in {location}")
            if SECRET_PATTERN.search(text):
                raise BuildError(f"{pkg.name}: possible hardcoded secret in {location}")
            if path.suffix == ".md":
                for match in MD_LINK_PATTERN.finditer(text):
                    target = match.group(1)
                    if re.match(r"^[a-z]+:", target) or target.startswith("<"):
                        continue
                    resolved = posixpath.normpath(posixpath.join(posixpath.dirname(location), target))
                    if resolved not in pkg.files:
                        pkg.warnings.append(f"{location}: broken link {target}")
        frontmatter, body = split_frontmatter(pkg.files["SKILL.md"].decode("utf-8"))
        if frontmatter_value(frontmatter, "name") != pkg.name or not body.strip():
            raise BuildError(f"{pkg.name}: SKILL.md name or body is invalid")
        try:
            import yaml  # type: ignore

            parsed = yaml.safe_load(frontmatter)
            if parsed.get("name") != pkg.name or not parsed.get("description"):
                raise BuildError(f"{pkg.name}: frontmatter does not parse to name and description")
        except ImportError:
            json.loads(frontmatter.split("description: ", 1)[1])


def write_zip(archive_path: Path, pkg: Package) -> None:
    temporary = archive_path.with_name(f".{archive_path.name}.tmp")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative, data in sorted(pkg.files.items()):
            info = zipfile.ZipInfo(f"{pkg.name}/{relative}", date_time=FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            executable = PurePosixPath(relative).suffix.lower() in EXECUTABLE_SUFFIXES
            info.external_attr = (0o100755 if executable else 0o100644) << 16
            archive.writestr(info, data)
    with zipfile.ZipFile(temporary) as archive:
        if archive.testzip():
            raise BuildError(f"ZIP CRC validation failed: {archive_path.name}")
    os.replace(temporary, archive_path)


def listing_sheet(listings: dict, packages: list[Package], sums: dict[str, str]) -> str:
    lines = ["# Agensi listing sheet", "", "Copy each block into Creator Dashboard > Submit a Skill.", ""]
    for pkg in packages:
        listing = listings["skills"][pkg.name]
        price = "Free" if not listing["price_usd"] else f"${listing['price_usd']} (suggested)"
        lines += [
            f"## {listing['title']} (`{pkg.name}.zip`)",
            "",
            f"- Price: {price}",
            f"- Tags: {', '.join(listing['tags'])}",
            f"- SHA-256: `{sums[pkg.name]}`",
            "",
            "Listing description:",
            "",
            listing["description_en"],
            "",
            *[f"- {item}" for item in listing["highlights"]],
            "",
        ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--only", nargs="*", help="Build only these skills.")
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    listings = json.loads((repo_root / "scripts" / "agensi_listings.json").read_text(encoding="utf-8"))
    output_dir = (args.output_dir or repo_root / "releases" / "agensi").resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        builder = Builder(repo_root, listings)
        names = args.only or builder.sellable
        packages: list[Package] = []
        sums: dict[str, str] = {}
        for name in names:
            if name not in builder.sellable:
                raise BuildError(f"Not a sellable skill: {name}")
            pkg = builder.build(name)
            archive = output_dir / f"{name}.zip"
            write_zip(archive, pkg)
            sums[name] = hashlib.sha256(archive.read_bytes()).hexdigest()
            packages.append(pkg)
            size_kb = archive.stat().st_size / 1024
            print(f"built {archive.name}: {len(pkg.files)} files, {size_kb:.1f} KB, companions={len(pkg.companions)}")
            for warning in pkg.warnings:
                print(f"  WARN {warning}")
    except BuildError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    (output_dir / "SHA256SUMS").write_text(
        "".join(f"{sums[p.name]}  {p.name}.zip\n" for p in packages), encoding="utf-8", newline="\n"
    )
    if not args.only:
        (output_dir / "LISTINGS.md").write_text(listing_sheet(listings, packages, sums), encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
