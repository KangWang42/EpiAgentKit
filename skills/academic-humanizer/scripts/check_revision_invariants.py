#!/usr/bin/env python3
"""Compare scholarly revision invariants in two UTF-8 text files."""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Callable, Iterable


CHARACTER_TRANSLATION = str.maketrans(
    {
        "−": "-",
        "–": "-",
        "—": "-",
        "‐": "-",
        "‑": "-",
        "﹣": "-",
        "，": ",",
        "；": ";",
        "：": ":",
    }
)
NUMBER_PATTERN = re.compile(
    r"(?<![\d.])[+-]?(?:(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?|\.\d+)"
    r"(?:[eE][+-]?\d+)?(?:\s*(?:%|‰))?(?!\w)"
)
NUMERIC_CITATION_PATTERN = re.compile(
    r"\[(?P<body>\d+(?:\s*(?:[,;\-])\s*\d+)*)\]"
)
AUTHOR_NAME = r"[A-ZÀ-ÖØ-Þ][A-Za-zÀ-ÖØ-öø-ÿ'’\-]+"
AUTHOR_YEAR_PATTERN = re.compile(
    rf"\b(?P<authors>{AUTHOR_NAME}(?:\s+(?:et\s+al\.?|(?:&|and)\s+{AUTHOR_NAME}))?)"
    rf"\s*(?:,\s*|\(\s*)(?P<year>(?:19|20)\d{{2}}[a-z]?)\s*\)?"
)
DOI_PATTERN = re.compile(
    r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+",
    re.IGNORECASE,
)
PMID_PATTERN = re.compile(r"\bPMID\s*:?\s*(?P<pmid>\d{1,9})\b", re.IGNORECASE)
ENGLISH_CROSS_REFERENCE_PATTERN = re.compile(
    r"\b(?:(?:supplementary|supplemental)\s+(?:fig(?:ure)?|table|material)"
    r"|(?:fig(?:ure)?|table|appendix))\.?\s*(?:[A-Z]?\d+[A-Z]?|[A-Z])\b",
    re.IGNORECASE,
)
CHINESE_CROSS_REFERENCE_PATTERN = re.compile(
    r"(?:(?:补充|附)?(?:图|表)|补充材料|附录)\s*"
    r"(?:[A-Za-z]?\d+[A-Za-z]?|[A-Za-z])"
)
CATEGORY_RULES = {
    "numbers": "invariant.numbers_changed",
    "citations": "invariant.citations_changed",
    "cross_references": "invariant.cross_references_changed",
    "protected_terms": "invariant.protected_terms_changed",
}


def normalize_source(text: str) -> str:
    """Normalize compatibility characters without erasing reported precision."""

    return unicodedata.normalize("NFKC", text).translate(CHARACTER_TRANSLATION)


def canonical_number(token: str) -> str:
    value = re.sub(r"\s+", "", token).casefold()
    grouped = re.fullmatch(
        r"[+-]?\d{1,3}(?:,\d{3})+(?:\.\d+)?(?:e[+-]?\d+)?(?:%|‰)?",
        value,
    )
    return value.replace(",", "") if grouped else value


def extract_numbers(text: str) -> Counter[str]:
    normalized = normalize_source(text)
    return Counter(
        canonical_number(match.group(0))
        for match in NUMBER_PATTERN.finditer(normalized)
    )


def trim_doi(value: str) -> str:
    value = value.rstrip(".,;:。")
    for opener, closer in (("(", ")"), ("<", ">")):
        while value.endswith(closer) and value.count(closer) > value.count(opener):
            value = value[:-1]
    return value.casefold()


def extract_citations(text: str) -> Counter[str]:
    normalized = normalize_source(text)
    values: list[str] = []
    for match in NUMERIC_CITATION_PATTERN.finditer(normalized):
        body = re.sub(r"\s+", "", match.group("body")).replace(";", ",")
        values.append(f"numeric:[{body}]")
    for match in AUTHOR_YEAR_PATTERN.finditer(normalized):
        authors = re.sub(r"[^a-z0-9]+", "", match.group("authors").casefold())
        values.append(f"author-year:{authors}:{match.group('year').casefold()}")
    for match in DOI_PATTERN.finditer(normalized):
        values.append(f"doi:{trim_doi(match.group(0))}")
    for match in PMID_PATTERN.finditer(normalized):
        values.append(f"pmid:{match.group('pmid')}")
    return Counter(values)


def canonical_cross_reference(value: str) -> str:
    normalized = value.casefold().replace("supplemental", "supplementary")
    normalized = re.sub(r"fig(?:ure)?\.?", "figure", normalized)
    return re.sub(r"[\s.]+", "", normalized)


def extract_cross_references(text: str) -> Counter[str]:
    normalized = normalize_source(text)
    matches = [
        *ENGLISH_CROSS_REFERENCE_PATTERN.finditer(normalized),
        *CHINESE_CROSS_REFERENCE_PATTERN.finditer(normalized),
    ]
    return Counter(canonical_cross_reference(match.group(0)) for match in matches)


def extract_protected_terms(text: str, protected_terms: Iterable[str]) -> Counter[str]:
    values: Counter[str] = Counter()
    for term in protected_terms:
        if not term:
            raise ValueError("--protected-term cannot be empty")
        count = text.count(term)
        if count:
            values[term] = count
    return values


def counter_delta(before: Counter[str], after: Counter[str]) -> dict[str, object]:
    removed = before - after
    added = after - before

    def records(values: Counter[str]) -> list[dict[str, object]]:
        return [
            {"value": value, "count": values[value]}
            for value in sorted(values, key=str.casefold)
        ]

    return {
        "changed": bool(removed or added),
        "original_total": sum(before.values()),
        "revised_total": sum(after.values()),
        "removed": records(removed),
        "added": records(added),
    }


def compare_texts(
    original: str,
    revised: str,
    protected_terms: Iterable[str] = (),
) -> dict[str, object]:
    protected_terms = tuple(protected_terms)
    extractors: dict[str, Callable[[str], Counter[str]]] = {
        "numbers": extract_numbers,
        "citations": extract_citations,
        "cross_references": extract_cross_references,
        "protected_terms": lambda text: extract_protected_terms(text, protected_terms),
    }
    categories = {
        name: counter_delta(extractor(original), extractor(revised))
        for name, extractor in extractors.items()
    }
    findings = [
        {
            "level": "REVIEW_REQUIRED",
            "rule": CATEGORY_RULES[name],
            "category": name,
            "removed": result["removed"],
            "added": result["added"],
        }
        for name, result in categories.items()
        if result["changed"]
    ]
    status = "REVIEW_REQUIRED" if findings else "PASS"
    return {
        "ok": status == "PASS",
        "status": status,
        "categories": categories,
        "findings": findings,
        "limitations": [
            "不变量相同只能说明所检查项目的多重集相同，不能证明语义、因果强度或结论方向未变。",
            "交换两个数值的位置可能仍会通过；必须结合原文位置、授权范围和证据来源复核。",
            "脚本发现的授权修改仍显示为 REVIEW_REQUIRED，由任务范围或 revision-state.json 记录决定能否接受。",
        ],
    }


def read_text(path: Path) -> str:
    payload = path.read_bytes()
    if b"\x00" in payload:
        raise ValueError("input appears to be a binary file")
    return payload.decode("utf-8-sig")


def check_files(
    original_path: Path,
    revised_path: Path,
    protected_terms: Iterable[str] = (),
) -> dict[str, object]:
    result = compare_texts(
        read_text(original_path),
        read_text(revised_path),
        protected_terms,
    )
    result["inputs"] = {
        "original": str(original_path),
        "revised": str(revised_path),
    }
    return result


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original", type=Path, help="original UTF-8 text or Markdown file")
    parser.add_argument("revised", type=Path, help="revised UTF-8 text or Markdown file")
    parser.add_argument("--protected-term", action="append", default=[])
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser.parse_args(argv)


def configure_utf8_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="replace")


def main(argv: list[str] | None = None) -> int:
    configure_utf8_output()
    args = parse_args(argv)
    try:
        result = check_files(args.original, args.revised, args.protected_term)
    except (OSError, UnicodeError, ValueError) as error:
        result = {
            "ok": False,
            "status": "ERROR",
            "error": {
                "type": type(error).__name__,
                "message": str(error),
            },
        }
        exit_code = 2
    else:
        exit_code = 0 if result["ok"] else 1

    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif result["status"] == "ERROR":
        print(f"Revision invariant check ERROR: {result['error']['message']}", file=sys.stderr)
    else:
        print(f"Revision invariant check {result['status']}")
        for finding in result["findings"]:
            print(
                f"[{finding['level']}] {finding['category']}: "
                f"removed={finding['removed']} added={finding['added']}"
            )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
