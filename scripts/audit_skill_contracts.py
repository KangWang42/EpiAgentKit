#!/usr/bin/env python3
"""Audit EpiAgentKit skill metadata, dependencies, routing cases and links."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from config_core import DEPENDENCIES, available_skills
from skill_conflicts import CONFLICT_DOMAINS


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


def main() -> int:
    problems: list[str] = []
    public = set(available_skills(ROOT))
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
    print(
        f"Skill contract audit: PASS ({len(public)} public skills, "
        f"{len(cases)} routing cases, no dependency cycles)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
