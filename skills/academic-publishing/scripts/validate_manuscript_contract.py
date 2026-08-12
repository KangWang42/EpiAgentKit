#!/usr/bin/env python3
"""检查任务级稿件约定的结构，不替代科学事实核验。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ALLOWED_KINDS = {"design", "estimand", "method", "data", "reporting"}
ALLOWED_STATES = {"pending", "passed", "blocked"}
ALLOWED_MODES = {"complete_manuscript", "structural_rewrite"}


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def unique_ids(items: Any, label: str, errors: list[str]) -> set[str]:
    if not isinstance(items, list):
        errors.append(f"{label} 必须是数组")
        return set()
    ids: list[str] = []
    for index, item in enumerate(items):
        if not isinstance(item, dict) or not nonempty(item.get("id")):
            errors.append(f"{label}[{index}] 必须包含非空 id")
            continue
        ids.append(item["id"].strip())
    duplicates = sorted({item for item in ids if ids.count(item) > 1})
    if duplicates:
        errors.append(f"{label} 的 id 必须唯一：{', '.join(duplicates)}")
    return set(ids)


def string_list(value: Any, label: str, errors: list[str]) -> list[str]:
    if not isinstance(value, list) or not all(nonempty(item) for item in value):
        errors.append(f"{label} 必须是非空字符串数组")
        return []
    return [item.strip() for item in value]


def validate_contract(contract: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(contract, dict):
        return ["稿件约定的根节点必须是对象"]
    if contract.get("schema_version") != 1:
        errors.append("schema_version 必须等于 1")
    if contract.get("mode") not in ALLOWED_MODES:
        errors.append("mode 仅接受 complete_manuscript 或 structural_rewrite")
    status = contract.get("status")
    if status not in {"draft", "complete"}:
        errors.append("status 仅接受 draft 或 complete")

    artifacts = contract.get("artifacts")
    artifact_ids = unique_ids(artifacts, "artifacts", errors)
    if isinstance(artifacts, list):
        for index, item in enumerate(artifacts):
            if not isinstance(item, dict):
                continue
            for field in ("audience", "purpose", "output"):
                if not nonempty(item.get(field)):
                    errors.append(f"artifacts[{index}].{field} 不能为空")
            allowed = string_list(
                item.get("allowed_information"),
                f"artifacts[{index}].allowed_information",
                errors,
            )
            forbidden = string_list(
                item.get("forbidden_information"),
                f"artifacts[{index}].forbidden_information",
                errors,
            )
            overlap = sorted(set(allowed) & set(forbidden))
            if overlap:
                errors.append(
                    f"artifacts[{index}] 的允许信息与排除信息重叠：{', '.join(overlap)}"
                )

    modules = contract.get("modules")
    module_ids = unique_ids(modules, "modules", errors)
    if isinstance(modules, list):
        for index, item in enumerate(modules):
            if not isinstance(item, dict):
                continue
            if item.get("kind") not in ALLOWED_KINDS:
                errors.append(f"modules[{index}].kind 不受支持")
            for field in ("source", "manuscript_locations", "required_fields"):
                string_list(item.get(field), f"modules[{index}].{field}", errors)

    sections = contract.get("sections")
    section_ids = unique_ids(sections, "sections", errors)
    if isinstance(sections, list):
        for index, item in enumerate(sections):
            if not isinstance(item, dict):
                continue
            for field in ("function", "output"):
                if not nonempty(item.get(field)):
                    errors.append(f"sections[{index}].{field} 不能为空")
            evidence = string_list(
                item.get("evidence_sources"),
                f"sections[{index}].evidence_sources",
                errors,
            )
            section_modules = string_list(
                item.get("modules"), f"sections[{index}].modules", errors
            )
            unknown = sorted(set(section_modules) - module_ids)
            if unknown:
                errors.append(
                    f"sections[{index}] 引用了未声明的适用要求：{', '.join(unknown)}"
                )
            if not evidence:
                continue
            if item.get("content_check") not in ALLOWED_STATES:
                errors.append(f"sections[{index}].content_check 不受支持")

    if isinstance(modules, list):
        for index, item in enumerate(modules):
            if not isinstance(item, dict):
                continue
            locations = item.get("manuscript_locations", [])
            if isinstance(locations, list):
                unknown = sorted(set(locations) - section_ids)
                if unknown:
                    errors.append(
                        f"modules[{index}] 包含未声明的稿件位置：{', '.join(unknown)}"
                    )

    table_ids = unique_ids(contract.get("tables"), "tables", errors)
    tables = contract.get("tables")
    if isinstance(tables, list):
        for table_index, table in enumerate(tables):
            if not isinstance(table, dict):
                continue
            for field in ("role", "source", "placement", "caption"):
                if not nonempty(table.get(field)):
                    errors.append(f"tables[{table_index}].{field} 不能为空")
            columns = table.get("columns")
            if not isinstance(columns, list) or not columns:
                errors.append(f"tables[{table_index}].columns 必须是非空数组")
                continue
            field_ids: list[str] = []
            for column_index, column in enumerate(columns):
                if not isinstance(column, dict) or any(
                    not nonempty(column.get(field))
                    for field in ("field_id", "label", "source_field")
                ):
                    errors.append(
                        f"tables[{table_index}].columns[{column_index}] 缺少 field_id、label 或 source_field"
                    )
                    continue
                field_ids.append(column["field_id"].strip())
            duplicates = sorted(
                {field_id for field_id in field_ids if field_ids.count(field_id) > 1}
            )
            if duplicates:
                errors.append(
                    f"tables[{table_index}] 的 field_id 必须唯一：{', '.join(duplicates)}"
                )

    figure_ids = unique_ids(contract.get("figures"), "figures", errors)
    figures = contract.get("figures")
    if isinstance(figures, list):
        for index, item in enumerate(figures):
            if not isinstance(item, dict):
                continue
            for field in ("role", "source", "placement", "caption"):
                if not nonempty(item.get(field)):
                    errors.append(f"figures[{index}].{field} 不能为空")

    checks = contract.get("checks")
    if not isinstance(checks, dict):
        errors.append("checks 必须是对象")
    else:
        for key in ("content", "field_reconciliation", "file_display"):
            if checks.get(key) not in ALLOWED_STATES:
                errors.append(f"checks.{key} 仅接受 pending、passed 或 blocked")

    if not artifact_ids:
        errors.append("至少声明一个目标成品")
    if not module_ids:
        errors.append("至少声明一项实际采用的研究设计、方法或报告规范要求")
    if not section_ids:
        errors.append("至少声明一个稿件部分")
    if status == "complete":
        if isinstance(sections, list) and any(
            isinstance(item, dict) and item.get("content_check") != "passed"
            for item in sections
        ):
            errors.append("status=complete 时，每个稿件部分的 content_check 必须为 passed")
        if isinstance(checks, dict) and any(
            checks.get(key) != "passed"
            for key in ("content", "field_reconciliation", "file_display")
        ):
            errors.append("status=complete 时，内容、字段对账和文件显示三项检查必须全部为 passed")

    _ = (table_ids, figure_ids)
    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contract", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        contract = json.loads(args.contract.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        errors = [f"无法读取稿件约定：{type(error).__name__}"]
    else:
        errors = validate_contract(contract)
    payload = {"status": "PASS" if not errors else "FAIL", "errors": errors}
    if args.as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
    else:
        print("PASS")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
