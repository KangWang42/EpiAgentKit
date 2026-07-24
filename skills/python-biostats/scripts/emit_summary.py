#!/usr/bin/env python3
"""Write and render EpiAgentKit's language-neutral results.yaml contract."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any
import math

try:
    import yaml
except ImportError as exc:  # pragma: no cover - environment-dependent guard
    raise RuntimeError(
        "emit_summary.py requires PyYAML in the active project environment; "
        "prepare it outside EpiAgentKit, then rerun."
    ) from exc


def _load(path: str | Path) -> dict[str, Any]:
    target = Path(path)
    if not target.is_file():
        return {"meta": {}, "results": {}}
    value = yaml.safe_load(target.read_text(encoding="utf-8")) or {}
    if not isinstance(value, dict):
        raise ValueError(f"results.yaml root must be a mapping: {target}")
    value.setdefault("meta", {})
    value.setdefault("results", {})
    if not isinstance(value["meta"], dict) or not isinstance(value["results"], dict):
        raise ValueError("results.yaml meta and results must be mappings")
    return value


def _write(path: str | Path, document: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        yaml.safe_dump(document, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def _present(value: Any) -> bool:
    return value is not None and not (
        isinstance(value, float) and math.isnan(value)
    )


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
    rendered: dict[str, str] = {}
    est_text = None
    if _present(est):
        separator = "" if unit == "%" else " "
        est_text = _number(float(est), digits) + (separator + unit if unit else "")
        rendered["est"] = est_text
    ci_text = None
    if _present(ci_low) and _present(ci_high):
        low = _number(float(ci_low), digits)
        high = _number(float(ci_high), digits)
        ci_text = (
            f"（95%CI：{low}，{high}）"
            if style == "zh"
            else f" (95% CI: {low}, {high})"
        )
        rendered["ci"] = ci_text
    p_text = None
    if _present(p):
        p_text = _p_value(float(p), p_digits, p_floor)
        rendered["p"] = p_text
    if est_text is not None and ci_text is not None:
        rendered["est_ci"] = est_text + ci_text
    full = (est_text or "") + (ci_text or "")
    if p_text is not None:
        full = f"{full}{'，' if full else ''}{p_text}"
    rendered["full"] = full
    return rendered


def _raw_signature(values: list[Any]) -> str:
    return "|".join("" if value is None else str(value) for value in values)


def add_result(
    path: str | Path,
    key: str,
    *,
    label: str = "",
    est: float | None = None,
    ci_low: float | None = None,
    ci_high: float | None = None,
    p: float | None = None,
    unit: str = "",
    section: str = "结果",
    source: str = "",
    table: str = "",
    interp: str | None = None,
    digits: int = 2,
    p_digits: int = 3,
    p_floor: float = 0.001,
    style: str = "zh",
) -> str:
    """Upsert one result and return rendered.full."""
    if style not in {"zh", "en"}:
        raise ValueError("style must be 'zh' or 'en'")
    document = _load(path)
    previous = document["results"].get(key)
    signature = _raw_signature([est, ci_low, ci_high, p, unit])
    previous_interp = previous.get("interp", "") if isinstance(previous, dict) else ""
    changed = bool(previous and previous.get("raw_sig") != signature)
    interp_value = previous_interp if interp is None else interp
    needs_review = bool(changed and interp is None and interp_value)
    if previous and not needs_review and interp is None:
        needs_review = bool(previous.get("interp_review", False))
    rendered = _render(
        est, ci_low, ci_high, p, unit, digits, p_digits, p_floor, style
    )
    document["results"][key] = {
        "label": label,
        "section": section,
        "source": source,
        "table": table,
        "raw": {
            "est": est,
            "ci_low": ci_low,
            "ci_high": ci_high,
            "p": p,
            "unit": unit,
        },
        "rendered": rendered,
        "interp": interp_value,
        "interp_review": needs_review,
        "raw_sig": signature,
    }
    document["meta"]["updated"] = date.today().isoformat()
    _write(path, document)
    return rendered["full"]


def confirm_interp(path: str | Path, key: str, interp: str | None = None) -> None:
    document = _load(path)
    if key not in document["results"]:
        raise KeyError(f"results.yaml has no key: {key}")
    if interp is not None:
        document["results"][key]["interp"] = interp
    document["results"][key]["interp_review"] = False
    _write(path, document)


def set_conclusion(path: str | Path, text: str) -> None:
    document = _load(path)
    document["conclusion"] = text
    _write(path, document)


def stale_interps(path: str | Path) -> list[str]:
    document = _load(path)
    return [
        key
        for key, item in document["results"].items()
        if isinstance(item, dict) and item.get("interp_review") is True
    ]


def val(path: str | Path, key: str, which: str = "full") -> str:
    document = _load(path)
    try:
        return str(document["results"][key]["rendered"][which])
    except KeyError as exc:
        raise KeyError(f"results.yaml has no {key}.rendered.{which}") from exc


def render_summary_md(path: str | Path, output: str | Path) -> Path:
    document = _load(path)
    results = document["results"]
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    if not results:
        target.write_text("# 结果汇总（暂无）\n", encoding="utf-8")
        return target
    lines = ["# 结果汇总（由 results.yaml 自动生成，勿手改）", ""]
    stale = stale_interps(path)
    if stale:
        lines.extend([f"> [解读待复核] {'、'.join(stale)}", ""])
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
            sources = [value for value in (item.get("source"), item.get("table")) if value]
            suffix = f"（来源：{'；'.join(sources)}）" if sources else ""
            lines.append(f"- **{label}**（`{key}`）：{item['rendered']['full']}{suffix}")
            if item.get("interp"):
                flag = " [解读待复核]" if item.get("interp_review") else ""
                lines.append(f"  - 解读{flag}：{item['interp']}")
        lines.append("")
    if document.get("conclusion"):
        lines.extend(["## 结论", "", str(document["conclusion"]), ""])
    target.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return target
