#!/usr/bin/env python3
"""List unresolved placeholder markers in manuscript sources or Word files.

Exit code 0 means no marker was found, 1 means markers remain, 2 means an
input could not be read. Markers accepted by the author as open items must
still be reported to the user; this script does not decide acceptance.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree

# Current markers first, then legacy variants that older drafts may still contain.
PATTERNS = {
    "missing_info": r"[\[【]待补充[：:][^\]】]*[\]】]",
    "pending_citation": r"[\[【](?:待补充引用|引文待核验)[^\]】]*[\]】]",
    "unverified": r"[\[【](?:待核验|待确认)[^\]】]*[\]】]",
    "need_confirmation": r"\[NEED\s+CONFIRMATION[^\]]*\]",
    "legacy_ref": r"\[(?:ref|REF|citation needed|CITATION NEEDED)\]",
    "todo": r"\b(?:TODO|TBD|FIXME)\b",
}
COMPILED = {name: re.compile(pattern) for name, pattern in PATTERNS.items()}
TEXT_SUFFIXES = {".md", ".markdown", ".qmd", ".rmd", ".txt", ".tex"}
WORD_PARTS = re.compile(r"word/(?:document|footnotes|endnotes|header\d*|footer\d*|comments)\.xml$")
W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def docx_lines(path: Path) -> list[str]:
    lines: list[str] = []
    with zipfile.ZipFile(path) as package:
        for name in sorted(n for n in package.namelist() if WORD_PARTS.match(n)):
            root = ElementTree.fromstring(package.read(name))
            for paragraph in root.iter(f"{W_NS}p"):
                text = "".join(node.text or "" for node in paragraph.iter(f"{W_NS}t"))
                if text.strip():
                    lines.append(text)
    return lines


def read_lines(path: Path) -> list[str]:
    suffix = path.suffix.lower()
    if suffix == ".docx":
        return docx_lines(path)
    if suffix in TEXT_SUFFIXES:
        return path.read_text(encoding="utf-8-sig").splitlines()
    raise ValueError(f"unsupported file type: {path}")


def iter_inputs(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            files += sorted(
                p for p in path.rglob("*")
                if p.is_file() and (p.suffix.lower() in TEXT_SUFFIXES | {".docx"}) and not p.name.startswith("~$")
            )
        else:
            files.append(path)
    return files


def scan(paths: list[Path]) -> tuple[list[dict], list[str]]:
    findings: list[dict] = []
    errors: list[str] = []
    for path in iter_inputs(paths):
        try:
            lines = read_lines(path)
        except (OSError, ValueError, zipfile.BadZipFile, ElementTree.ParseError, UnicodeDecodeError) as error:
            errors.append(f"{path}: {error}")
            continue
        for number, line in enumerate(lines, 1):
            for kind, pattern in COMPILED.items():
                for match in pattern.finditer(line):
                    findings.append({"file": str(path), "line": number, "kind": kind, "marker": match.group(0)})
    return findings, errors


def main() -> int:
    parser = argparse.ArgumentParser(description="List unresolved placeholder markers in manuscripts.")
    parser.add_argument("paths", nargs="+", type=Path, help="Files or directories (.md/.qmd/.Rmd/.txt/.tex/.docx).")
    parser.add_argument("--json", action="store_true", help="Print findings as JSON.")
    args = parser.parse_args()

    findings, errors = scan(args.paths)
    if args.json:
        print(json.dumps({"findings": findings, "errors": errors}, ensure_ascii=False, indent=2))
    else:
        for item in findings:
            print(f"{item['file']}:{item['line']}: [{item['kind']}] {item['marker']}")
        for error in errors:
            print(f"ERROR {error}", file=sys.stderr)
        print(f"{len(findings)} marker(s) found")
    if errors:
        return 2
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
