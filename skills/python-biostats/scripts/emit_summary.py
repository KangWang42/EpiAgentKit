#!/usr/bin/env python3
"""Write and read the EpiAgentKit result data file."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Iterable
import math
import os

try:
    import yaml
except ImportError as exc:  # pragma: no cover - environment-dependent guard
    raise RuntimeError(
        "emit_summary.py requires PyYAML in the active project environment; "
        "install it there under the shared runtime-dependency policy, then rerun."
    ) from exc


def _load(path: str | Path) -> dict[str, Any]:
    target = Path(path)
    if not target.is_file():
        return {"meta": {"schema_version": 2}, "results": {}}
    value = yaml.safe_load(target.read_text(encoding="utf-8")) or {}
    if not isinstance(value, dict):
        raise ValueError(f"results.yaml root must be a mapping: {target}")
    value.setdefault("meta", {})
    value.setdefault("results", {})
    if not isinstance(value["meta"], dict) or not isinstance(value["results"], dict):
        raise ValueError("results.yaml meta and results must be mappings")
    return value


def _write(path: str | Path, document: dict[str, Any]) -> None:
    """Replace the result data file through a temporary sibling file."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with NamedTemporaryFile(
            "w", encoding="utf-8", dir=target.parent, prefix=".results-", suffix=".yaml",
            delete=False,
        ) as handle:
            yaml.safe_dump(document, handle, allow_unicode=True, sort_keys=False)
            handle.flush()
            os.fsync(handle.fileno())
            temporary = Path(handle.name)
        os.replace(temporary, target)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def _present(value: Any) -> bool:
    return value is not None and not (isinstance(value, float) and math.isnan(value))


def _number(value: float, digits: int) -> str:
    return f"{value:.{digits}f}".replace("-", "−")


def _p_value(value: float, digits: int, floor: float) -> str:
    if value < floor:
        return f"P < {floor:.{digits}f}"
    return f"P = {value:.{digits}f}"


def _render(
    est: float | None,
    ci_low: float | None,
    ci_high: float | None,
    p: float | None,
    unit: str,
    digits: int,
    p_digits: int,
    p_floor: float,
    style: str,
) -> dict[str, str]:
    display: dict[str, str] = {}
    estimate = None
    if _present(est):
        separator = "" if unit == "%" else " "
        estimate = _number(float(est), digits) + (separator + unit if unit else "")
        display["estimate"] = estimate
    interval = None
    if _present(ci_low) and _present(ci_high):
        low = _number(float(ci_low), digits)
        high = _number(float(ci_high), digits)
        interval = (
            f"（95% CI：{low}，{high}）"
            if style == "zh"
            else f" (95% CI: {low}, {high})"
        )
        display["interval"] = interval
    p_value = None
    if _present(p):
        p_value = _p_value(float(p), p_digits, p_floor)
        display["p_value"] = p_value
    full = (estimate or "") + (interval or "")
    if p_value is not None:
        full = f"{full}{'，' if full and style == 'zh' else '; ' if full else ''}{p_value}"
    display["full"] = full
    return display


def _strings(value: str | Path | Iterable[str | Path] | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (str, Path)):
        values = [value]
    else:
        values = list(value)
    return [str(item).replace("\\", "/") for item in values if str(item).strip()]


def add_result(
    path: str | Path,
    key: str,
    *,
    producer: str,
    source: str,
    analysis_set: str,
    run_id: str,
    input: str | Path | Iterable[str | Path] | None = None,
    input_hash: str = "",
    consumers: str | Path | Iterable[str | Path] | None = None,
    label: str = "",
    est: float | None = None,
    ci_low: float | None = None,
    ci_high: float | None = None,
    p: float | None = None,
    unit: str = "",
    section: str = "结果",
    digits: int = 2,
    p_digits: int = 3,
    p_floor: float = 0.001,
    style: str = "zh",
    term_label: str = "",
    short_label: str = "",
    scale_label: str = "",
    change_definition: str = "",
) -> str:
    """Upsert one schema-v2 result and return display.full."""
    if style not in {"zh", "en"}:
        raise ValueError("style must be 'zh' or 'en'")
    required = {
        "key": key,
        "producer": producer,
        "source": source,
        "analysis_set": analysis_set,
        "run_id": run_id,
    }
    missing = [name for name, value in required.items() if not str(value).strip()]
    inputs = _strings(input)
    if not inputs and not input_hash.strip():
        missing.append("input_or_input_hash")
    if missing:
        raise ValueError("missing result provenance: " + ", ".join(missing))

    document = _load(path)
    schema = document["meta"].get("schema_version")
    if document["results"] and schema not in {None, 2}:
        raise ValueError("legacy results.yaml is read-only; write schema v2 to results/results.yaml")
    display = _render(est, ci_low, ci_high, p, unit, digits, p_digits, p_floor, style)
    presentation = {
        "term_label": term_label,
        "short_label": short_label,
        "scale_label": scale_label,
        "change_definition": change_definition,
    }
    display.update(
        {name: value.strip() for name, value in presentation.items() if value.strip()}
    )
    provenance: dict[str, Any] = {
        "producer": producer.replace("\\", "/"),
        "source": source,
        "input": inputs,
        "analysis_set": analysis_set,
        "run_id": run_id,
    }
    if input_hash.strip():
        provenance["input_hash"] = input_hash.strip()
    document["results"][key] = {
        "label": label,
        "section": section,
        "estimate": {
            "value": est,
            "ci_low": ci_low,
            "ci_high": ci_high,
            "p_value": p,
            "unit": unit,
        },
        "display": display,
        "provenance": provenance,
        "consumers": _strings(consumers),
    }
    document["meta"]["schema_version"] = 2
    document["meta"]["updated_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    _write(path, document)
    return display["full"]


def _display(item: dict[str, Any]) -> dict[str, Any]:
    display = item.get("display")
    if isinstance(display, dict):
        return display
    rendered = item.get("rendered")
    if not isinstance(rendered, dict):
        raise ValueError("result has no display/rendered mapping")
    return {
        "estimate": rendered.get("est"),
        "interval": rendered.get("ci"),
        "p_value": rendered.get("p"),
        "full": rendered.get("full"),
    }


def val(path: str | Path, key: str, which: str = "full") -> str:
    document = _load(path)
    try:
        value = _display(document["results"][key])[which]
    except KeyError as exc:
        raise KeyError(f"results.yaml has no {key}.display.{which}") from exc
    if value is None:
        raise KeyError(f"results.yaml has no {key}.display.{which}")
    return str(value)


def render_summary_md(path: str | Path, output: str | Path) -> Path:
    document = _load(path)
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# 结果汇总",
        "",
        "> 本文件根据 results/results.yaml 自动生成，仅用于核对；如需修改数字，请回到实际生成结果的分析脚本。",
        "",
    ]
    results = document["results"]
    if not results:
        lines.append("暂无结果。")
    sections: list[str] = []
    for item in results.values():
        section = item.get("section") or "结果"
        if section not in sections:
            sections.append(section)
    for section in sections:
        lines.extend([f"## {section}", ""])
        for key, item in results.items():
            if (item.get("section") or "结果") != section:
                continue
            label = item.get("label") or key
            provenance = item.get("provenance") or {}
            producer = provenance.get("producer") or item.get("source") or "未记录"
            run_id = provenance.get("run_id") or "legacy"
            lines.append(
                f"- **{label}**（`{key}`）：{_display(item).get('full', '')}"
                f"（生成脚本：`{producer}`；运行编号：`{run_id}`）"
            )
        lines.append("")
    temporary = target.with_name(f".{target.name}.tmp")
    temporary.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    os.replace(temporary, target)
    return target
