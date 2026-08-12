#!/usr/bin/env python3
"""按稳定字段标识核对展示 CSV 与最终显示值来源。"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def normalize(value: str) -> str:
    return " ".join(value.replace("\u00a0", " ").split())


def column_index(header: list[str], selector: Any, label: str) -> int:
    if isinstance(selector, int) and not isinstance(selector, bool):
        if 0 <= selector < len(header):
            return selector
        raise ValueError(f"{label} 的索引 {selector} 超出表格范围")
    if not isinstance(selector, str) or not selector.strip():
        raise ValueError(f"{label} 必须是非空列名或从 0 开始的列索引")
    matches = [index for index, value in enumerate(header) if value == selector]
    if len(matches) != 1:
        raise ValueError(f"{label} 的列名 {selector!r} 匹配到 {len(matches)} 列")
    return matches[0]


def read_csv(path: Path) -> tuple[list[str], list[list[str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))
    if not rows:
        raise ValueError(f"{path} 为空")
    width = len(rows[0])
    if width == 0 or any(len(row) != width for row in rows):
        raise ValueError(f"{path} 各行列数不一致")
    return rows[0], rows[1:]


def validate_spec(spec: Any) -> tuple[list[str], list[dict[str, Any]]]:
    if not isinstance(spec, dict) or spec.get("schema_version") != 1:
        raise ValueError("schema_version 必须等于 1")
    row_keys = spec.get("row_keys")
    fields = spec.get("fields")
    if not isinstance(row_keys, list) or not row_keys:
        raise ValueError("row_keys 必须是非空数组")
    if not isinstance(fields, list) or not fields:
        raise ValueError("fields 必须是非空数组")
    field_ids: list[str] = []
    for index, item in enumerate(fields):
        if not isinstance(item, dict) or not isinstance(item.get("field_id"), str):
            raise ValueError(f"fields[{index}] 缺少 field_id")
        if not item["field_id"].strip():
            raise ValueError(f"fields[{index}].field_id 为空")
        if "source_column" not in item or "display_column" not in item:
            raise ValueError(f"fields[{index}] 缺少 source_column 或 display_column")
        field_ids.append(item["field_id"].strip())
    duplicates = sorted({value for value in field_ids if field_ids.count(value) > 1})
    if duplicates:
        raise ValueError(f"field_id 必须唯一：{', '.join(duplicates)}")
    return row_keys, fields


def reconcile(source_path: Path, display_path: Path, spec: Any) -> dict[str, Any]:
    row_keys, fields = validate_spec(spec)
    source_header, source_rows = read_csv(source_path)
    display_header, display_rows = read_csv(display_path)

    key_indexes: list[tuple[int, int]] = []
    for index, item in enumerate(row_keys):
        if not isinstance(item, dict) or "source_column" not in item or "display_column" not in item:
            raise ValueError(f"row_keys[{index}] 缺少 source_column 或 display_column")
        key_indexes.append(
            (
                column_index(source_header, item["source_column"], f"row_keys[{index}].source_column"),
                column_index(display_header, item["display_column"], f"row_keys[{index}].display_column"),
            )
        )

    field_indexes: list[tuple[str, int, int]] = []
    for index, item in enumerate(fields):
        field_indexes.append(
            (
                item["field_id"].strip(),
                column_index(source_header, item["source_column"], f"fields[{index}].source_column"),
                column_index(display_header, item["display_column"], f"fields[{index}].display_column"),
            )
        )

    def keyed(
        rows: list[list[str]], indexes: list[int], label: str
    ) -> dict[tuple[str, ...], list[str]]:
        output: dict[tuple[str, ...], list[str]] = {}
        for number, row in enumerate(rows, start=2):
            key = tuple(normalize(row[index]) for index in indexes)
            if key in output:
                raise ValueError(f"{label} 在第 {number} 行出现重复行键 {key!r}")
            output[key] = row
        return output

    source_by_key = keyed(source_rows, [item[0] for item in key_indexes], "source")
    display_by_key = keyed(display_rows, [item[1] for item in key_indexes], "display")
    missing = sorted(set(source_by_key) - set(display_by_key))
    extra = sorted(set(display_by_key) - set(source_by_key))
    mismatches: list[dict[str, Any]] = []
    for key in sorted(set(source_by_key) & set(display_by_key)):
        source_row = source_by_key[key]
        display_row = display_by_key[key]
        for field_id, source_index, display_index in field_indexes:
            source_value = normalize(source_row[source_index])
            display_value = normalize(display_row[display_index])
            if source_value != display_value:
                mismatches.append(
                    {
                        "row_key": list(key),
                        "field_id": field_id,
                        "source_value": source_value,
                        "display_value": display_value,
                    }
                )
    return {
        "status": "PASS" if not (missing or extra or mismatches) else "FAIL",
        "source_rows": len(source_rows),
        "display_rows": len(display_rows),
        "fields_checked": len(field_indexes),
        "missing_row_keys": [list(item) for item in missing],
        "extra_row_keys": [list(item) for item in extra],
        "mismatches": mismatches,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("display", type=Path)
    parser.add_argument("spec", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        spec = json.loads(args.spec.read_text(encoding="utf-8"))
        result = reconcile(args.source, args.display, spec)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        result = {"status": "FAIL", "errors": [str(error)]}
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["status"])
        for mismatch in result.get("mismatches", []):
            print(
                f"{mismatch['row_key']} {mismatch['field_id']}: "
                f"{mismatch['source_value']!r} != {mismatch['display_value']!r}"
            )
        for error in result.get("errors", []):
            print(error)
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
