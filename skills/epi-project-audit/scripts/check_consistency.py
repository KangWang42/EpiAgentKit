#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Cross-check downstream statistics against the result manifest.

把交付文档（论文/报告/PPT）里出现的统计量与 results/results.yaml 双向比对；
旧项目可读取 07_paper/results.yaml。
  方向A 文中→源：文中每个 95% CI（连同紧挨在前面的点估计）和 P 值，都必须能在
                results.yaml 的 display 或旧版 rendered 中找到数值相同的结果；
                找不到 = 疑似手敲/陈旧/下游私改未回写（高信号）。
  方向B 源→文中：results.yaml 里有、却没在任何交付文档出现的结果（信息，可能是漏用或仅内部）。
比较的是数值而不是格式：区间上下限可用逗号、短横线、长横线、to、~ 或“至”分隔，
全角标点、数学减号 −、P 值省略前导 0 都会先归一；1.2 与 1.20 视为同一数值。

用法：
  python check_consistency.py [项目根=.] [--yaml results/results.yaml]
退出码：发现数字不一致 → 1；全过 → 0；缺少结果文件或依赖 → 2。
"""
import argparse
import glob
import os
import re
import sys
from decimal import Decimal, InvalidOperation

try:
    import yaml
except ImportError:
    print(
        "缺少依赖 pyyaml；请先选择要使用的 Python 环境和安装方式。"
        "本检查器不会自动安装或升级依赖。"
    )
    sys.exit(2)


FULLWIDTH = {"：": ":", "，": ",", "（": "(", "）": ")", "＜": "<", "＞": ">",
             "＝": "=", "−": "-", "–": "–", "　": " ", "％": "%", "Ｐ": "P", "ｐ": "p",
             "～": "~", "［": "[", "］": "]"}
NUMBER = r"-?(?:\d+(?:\.\d+)?|\.\d+)"
SEPARATOR = r"\s*(?:,|–|—|-|~|to|至)\s*"
# 95% CI 及其上下限；可选地捕获紧挨在前面的点估计，例如 “1.45 (95% CI 1.12–1.87)”。
RE_EST_CI = re.compile(
    rf"(?:({NUMBER})\s*[(\[]?\s*)?95\s*%\s*ci\s*[:,]?\s*({NUMBER}){SEPARATOR}({NUMBER})",
    re.IGNORECASE,
)
RE_P = re.compile(rf"\bp\s*([=<>])\s*({NUMBER})", re.IGNORECASE)


def normalize(text):
    if text is None:
        return ""
    text = str(text)
    for key, value in FULLWIDTH.items():
        text = text.replace(key, value)
    return text


def number(value):
    try:
        return Decimal(value).normalize()
    except (InvalidOperation, TypeError):
        return None


def extract_statistics(text):
    """Return (estimate_ci, ci_only, p_values) sets of comparable numeric tuples."""
    text = normalize(text)
    estimate_ci, ci_only, p_values = set(), set(), set()
    for match in RE_EST_CI.finditer(text):
        estimate, low, high = (number(v) if v else None for v in match.groups())
        ci_only.add((low, high))
        if estimate is not None:
            estimate_ci.add((estimate, low, high))
    for match in RE_P.finditer(text):
        p_values.add((match.group(1), number(match.group(2))))
    return estimate_ci, ci_only, p_values


def extract_text(path):
    ext = path.lower().rsplit(".", 1)[-1]
    try:
        if ext == "md":
            with open(path, encoding="utf-8") as f:
                return f.read()
        if ext == "docx":
            from docx import Document
            d = Document(path)
            parts = [p.text for p in d.paragraphs]
            for t in d.tables:
                for row in t.rows:
                    parts += [c.text for c in row.cells]
            return "\n".join(parts)
        if ext == "pptx":
            from pptx import Presentation
            parts = []
            for s in Presentation(path).slides:
                for sh in s.shapes:
                    if sh.has_text_frame:
                        parts.append(sh.text_frame.text)
                    if sh.has_table:
                        for row in sh.table.rows:
                            parts += [c.text for c in row.cells]
            return "\n".join(parts)
    except Exception as e:
        print(f"  [跳过] 读取失败 {path}: {e}")
    return ""


def source_statistics(doc):
    """Collect comparable values and per-result display strings from v2 or legacy manifests."""
    estimate_ci, ci_only, p_values, displays = set(), set(), set(), {}
    for key, result in (doc.get("results") or {}).items():
        rendered = result.get("display") or result.get("rendered") or {}
        fields = ("estimate", "interval", "p_value", "full") if result.get("display") else ("est", "ci", "p", "full")
        values = [normalize(rendered.get(field)) for field in fields if rendered.get(field)]
        joined = " ".join(values)
        est_ci, ci, p = extract_statistics(joined)
        ci_only |= ci
        p_values |= p
        estimate = number(normalize(rendered.get(fields[0]) or "").strip()) if rendered.get(fields[0]) else None
        estimate_ci |= est_ci
        if estimate is not None:
            estimate_ci |= {(estimate, low, high) for low, high in ci}
        displays[key] = values
    return estimate_ci, ci_only, p_values, displays


def show(values):
    return ", ".join(str(v) for v in values)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--yaml", default=None)
    a = ap.parse_args()
    root = a.root
    yaml_path = a.yaml or os.path.join(root, "results", "results.yaml")
    if a.yaml is None and not os.path.exists(yaml_path):
        legacy = os.path.join(root, "07_paper", "results.yaml")
        if os.path.exists(legacy):
            yaml_path = legacy
    if not os.path.exists(yaml_path):
        print(f"找不到结果唯一来源：{yaml_path}")
        sys.exit(2)
    with open(yaml_path, encoding="utf-8") as f:
        doc = yaml.safe_load(f) or {}
    src_est_ci, src_ci, src_p, displays = source_statistics(doc)

    # 待审计交付文档（排除唯一来源、派生 md、备份）
    pats = ["paper/**/*.docx", "paper/**/*.md", "07_paper/**/*.docx", "07_paper/**/*.md",
            "05_reports/**/*.docx", "05_reports/**/*.md", "05_reports/**/*.pptx",
            "04_figures/**/*.pptx", "**/*.pptx"]
    files, seen = [], set()
    for pat in pats:
        for fp in glob.glob(os.path.join(root, pat), recursive=True):
            rp = os.path.normpath(fp)
            base = os.path.basename(rp).lower()
            # Only the project's own backup tree is skipped; a project that itself lives under some
            # 09_backup folder (for example a workbench reproduction) is still checked.
            relative_parts = os.path.relpath(rp, root).replace("\\", "/").split("/")
            if rp in seen or "09_backup" in relative_parts:
                continue
            if base in ("0_result_summaries.md", "results.yaml"):
                continue
            seen.add(rp)
            files.append(rp)

    problems = 0
    used_keys = set()
    print(f"== 跨文档一致性审计 ==\n源：{yaml_path}（{len(doc.get('results') or {})} 个结果）")
    print(f"待查文档：{len(files)} 个\n")

    for fp in files:
        text = extract_text(fp)
        if not text:
            continue
        compact = normalize(text).replace(" ", "")
        for key, values in displays.items():
            if any(v.replace(" ", "") in compact for v in values if v):
                used_keys.add(key)
        est_ci, ci, p_values = extract_statistics(text)
        bad = []
        for low, high in sorted(ci, key=str):
            if (low, high) not in src_ci:
                bad.append(("CI", f"{low}, {high}"))
        for triple in sorted(est_ci, key=str):
            if triple[1:] in src_ci and triple not in src_est_ci:
                bad.append(("估计值", f"{triple[0]}（区间 {show(triple[1:])} 在源中对应的估计值不同）"))
        for p in sorted(p_values, key=str):
            if p not in src_p:
                bad.append(("P", f"P {p[0]} {p[1]}"))
        if bad:
            problems += len(bad)
            print(f"[方向A 文中无源匹配] {os.path.relpath(fp, root)}")
            for kind, token in bad:
                print(f"    {kind}: {token}  ← 疑似手敲/陈旧/未回写源")

    # 方向B：源里有、文档全未用
    unused = sorted(set(displays) - used_keys)
    if unused:
        print(f"\n[方向B 源有文档未用]（信息，非必错）：{'、'.join(unused)}")

    print(f"\n== 结果：{'发现 %d 处需处理' % problems if problems else '全部一致，通过'} ==")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
