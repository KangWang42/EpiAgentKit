#!/usr/bin/env python3
"""Audit EpiAgentKit skill metadata, dependencies, routing cases, links, and context budgets."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from config_core import DEPENDENCIES, public_skills
from skill_conflicts import CONFLICT_DOMAINS

HEAVY_SKILL_BYTES = 16384
LISTING_BUDGET_WARN_CHARS = 7000


def load_validator():
    path = ROOT / "skills" / "skill-creator" / "scripts" / "quick_validate.py"
    spec = importlib.util.spec_from_file_location("epiagentkit_quick_validate", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load validator: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.validate_skill


def dependency_cycles(graph: dict[str, set[str]]) -> list[str]:
    cycles: set[str] = set()

    def visit(node: str, path: list[str]) -> None:
        if node in path:
            start = path.index(node)
            cycle = path[start:] + [node]
            cycles.add(" -> ".join(cycle))
            return
        for child in sorted(graph.get(node, set())):
            visit(child, path + [node])

    for node in sorted(graph):
        visit(node, [])
    return sorted(cycles)


def collect_budget_report(root: Path, public: set[str]) -> dict:
    claude_path = root / "CLAUDE.md"
    claude_text = claude_path.read_text(encoding="utf-8") if claude_path.is_file() else ""
    skills_report: list[dict] = []
    total_desc_chars = 0
    total_desc_bytes = 0

    for name in sorted(public):
        skill_dir = root / "skills" / name
        skill_md = skill_dir / "SKILL.md"
        text = skill_md.read_text(encoding="utf-8")
        match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
        frontmatter = yaml.safe_load(match.group(1)) if match else {}
        desc = str((frontmatter or {}).get("description") or "").strip()
        body = text[match.end():].lstrip("\r\n") if match else text
        byte_size = len(text.encode("utf-8"))
        desc_chars = len(desc)
        desc_bytes = len(desc.encode("utf-8"))
        total_desc_chars += desc_chars
        total_desc_bytes += desc_bytes

        refs_dir = skill_dir / "references"
        top_refs = sorted(p for p in refs_dir.glob("*.md")) if refs_dir.is_dir() else []
        unreferenced: list[str] = []
        if top_refs:
            corpus = "\n".join(
                p.read_text(encoding="utf-8", errors="replace")
                for p in [skill_md, *top_refs]
            )
            for ref in top_refs:
                rel = ref.relative_to(skill_dir).as_posix()
                if rel not in corpus and ref.name not in corpus:
                    unreferenced.append(rel)

        skills_report.append(
            {
                "skill": name,
                "bytes": byte_size,
                "body_lines": len(body.splitlines()),
                "description_chars": desc_chars,
                "description_bytes": desc_bytes,
                "top_references": len(top_refs),
                "unreferenced_top_refs": unreferenced,
            }
        )

    heavy = sorted(
        (item for item in skills_report if item["bytes"] > HEAVY_SKILL_BYTES),
        key=lambda item: (-item["bytes"], item["skill"]),
    )
    orphan_refs = [
        f"{item['skill']}/{rel}"
        for item in skills_report
        for rel in item["unreferenced_top_refs"]
    ]
    return {
        "claude_md": {
            "chars": len(claude_text),
            "bytes": len(claude_text.encode("utf-8")),
            "lines": len(claude_text.splitlines()),
        },
        "public_skill_count": len(skills_report),
        "listing_chars": total_desc_chars,
        "listing_bytes": total_desc_bytes,
        "listing_warn_threshold": LISTING_BUDGET_WARN_CHARS,
        "heavy_threshold_bytes": HEAVY_SKILL_BYTES,
        "heavy_skills": [
            {"skill": item["skill"], "bytes": item["bytes"], "body_lines": item["body_lines"]}
            for item in heavy
        ],
        "unreferenced_top_refs": orphan_refs,
        "skills": sorted(skills_report, key=lambda item: (-item["bytes"], item["skill"])),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit EpiAgentKit skill metadata, dependencies, routing cases, links, and context budgets."
    )
    parser.add_argument(
        "--budget",
        action="store_true",
        help="Print Layer-1 description listing budget, Layer-2 SKILL.md byte sizes, and unreferenced top-level references.",
    )
    parser.add_argument(
        "--json",
        dest="as_json",
        action="store_true",
        help="Emit budget report as JSON (use with --budget).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    problems: list[str] = []
    public = set(public_skills(ROOT))
    all_skill_dirs = {
        item.name
        for item in (ROOT / "skills").iterdir()
        if item.is_dir() and (item / "SKILL.md").is_file()
    }
    validate_skill = load_validator()

    for name in sorted(public):
        valid, message = validate_skill(ROOT / "skills" / name)
        if not valid:
            problems.append(f"{name}: {message}")

    for owner, dependencies in sorted(DEPENDENCIES.items()):
        if owner not in public:
            problems.append(f"DEPENDENCIES has unknown or non-public owner: {owner}")
        for dependency in sorted(dependencies):
            if dependency not in public:
                problems.append(f"{owner} depends on unknown or non-public skill: {dependency}")
    problems.extend(f"dependency cycle: {cycle}" for cycle in dependency_cycles(DEPENDENCIES))

    missing_conflict_domains = sorted(public - set(CONFLICT_DOMAINS))
    if missing_conflict_domains:
        problems.append(
            "missing conflict-domain signatures: " + ", ".join(missing_conflict_domains)
        )

    routing_path = ROOT / "scripts" / "skill_routing_cases.json"
    routing = json.loads(routing_path.read_text(encoding="utf-8"))
    cases = routing.get("cases")
    if not isinstance(cases, list):
        problems.append("skill_routing_cases.json: cases must be a list")
        cases = []
    seen_ids: set[str] = set()
    covered: set[str] = set()
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            problems.append(f"routing case {index}: must be an object")
            continue
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id:
            problems.append(f"routing case {index}: missing id")
            continue
        if case_id in seen_ids:
            problems.append(f"duplicate routing case id: {case_id}")
        seen_ids.add(case_id)
        primary = case.get("primary")
        companions = case.get("companions", [])
        excluded = case.get("excluded", [])
        if not isinstance(primary, str):
            problems.append(f"{case_id}: primary must be a skill name")
            continue
        if not isinstance(companions, list) or not isinstance(excluded, list):
            problems.append(f"{case_id}: companions and excluded must be lists")
            continue
        references = [primary, *companions, *excluded]
        unknown = sorted(set(references) - all_skill_dirs)
        if unknown:
            problems.append(f"{case_id}: unknown skill(s): {', '.join(unknown)}")
        if primary in excluded or set(companions) & set(excluded):
            problems.append(f"{case_id}: selected and excluded skills overlap")
        covered.add(primary)
        covered.update(companions)

    missing_cases = sorted(public - covered)
    if missing_cases:
        problems.append("public skills without positive routing case: " + ", ".join(missing_cases))

    if problems:
        print("Skill contract audit: FAIL")
        for problem in problems:
            print(f"- {problem}")
        return 1

    if args.budget:
        report = collect_budget_report(ROOT, public)
        if args.as_json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 0
        print(
            f"Skill contract audit: PASS ({len(public)} public skills, "
            f"{len(cases)} routing cases, no dependency cycles)"
        )
        cm = report["claude_md"]
        print(
            f"Context budget: CLAUDE.md={cm['chars']} chars ({cm['bytes']} B, {cm['lines']} lines) | "
            f"Descriptions={report['listing_chars']} chars ({report['listing_bytes']} B)"
        )
        if report["listing_chars"] > LISTING_BUDGET_WARN_CHARS:
            print(
                f"WARN: total description listing ({report['listing_chars']} chars) exceeds "
                f"{LISTING_BUDGET_WARN_CHARS} chars"
            )
        if report["heavy_skills"]:
            heavy_str = ", ".join(
                f"{h['skill']} ({h['bytes']} B / {h['body_lines']}L)" for h in report["heavy_skills"]
            )
            print(f"Heavy Layer-2 SKILL.md (> {HEAVY_SKILL_BYTES} B): {heavy_str}")
        if report["unreferenced_top_refs"]:
            print("Unreferenced top-level references: " + ", ".join(report["unreferenced_top_refs"]))
        return 0

    print(
        f"Skill contract audit: PASS ({len(public)} public skills, "
        f"{len(cases)} routing cases, no dependency cycles)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
