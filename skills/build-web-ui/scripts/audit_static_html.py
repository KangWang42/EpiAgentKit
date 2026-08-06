#!/usr/bin/env python3
"""Audit deterministic HTML, accessibility, SEO, and asset basics without dependencies."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


IGNORED_PARTS = {".git", ".next", "node_modules", "__pycache__"}
VOID_CONTROLS = {"hidden", "button", "submit", "reset", "image"}


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    message: str
    line: int | None = None


class AuditParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.html_lang = ""
        self.in_head = False
        self.in_title = False
        self.title_parts: list[str] = []
        self.meta_name: dict[str, str] = {}
        self.meta_property: dict[str, str] = {}
        self.canonicals: list[tuple[str, int]] = []
        self.h1_lines: list[int] = []
        self.main_lines: list[int] = []
        self.ids: dict[str, int] = {}
        self.duplicate_ids: list[tuple[str, int]] = []
        self.images: list[tuple[dict[str, str | None], int]] = []
        self.assets: list[tuple[str, int, str]] = []
        self.scripts: list[tuple[dict[str, str | None], int, bool]] = []
        self.label_depth = 0
        self.label_fors: set[str] = set()
        self.controls: list[tuple[str, dict[str, str | None], int, bool]] = []

    @staticmethod
    def attrs_dict(attrs: list[tuple[str, str | None]]) -> dict[str, str | None]:
        return {key.lower(): value for key, value in attrs}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        values = self.attrs_dict(attrs)
        line = self.getpos()[0]

        if tag == "html":
            self.html_lang = (values.get("lang") or values.get("xml:lang") or "").strip()
        elif tag == "head":
            self.in_head = True
        elif tag == "title":
            self.in_title = True
        elif tag == "meta":
            content = (values.get("content") or "").strip()
            name = (values.get("name") or "").strip().lower()
            prop = (values.get("property") or "").strip().lower()
            if name:
                self.meta_name[name] = content
            if prop:
                self.meta_property[prop] = content
        elif tag == "link":
            rel = set((values.get("rel") or "").lower().split())
            href = (values.get("href") or "").strip()
            if "canonical" in rel:
                self.canonicals.append((href, line))
            if href and rel.intersection({"stylesheet", "icon", "preload", "modulepreload"}):
                self.assets.append((href, line, "link"))
        elif tag == "h1":
            self.h1_lines.append(line)
        elif tag == "main":
            self.main_lines.append(line)
        elif tag == "img":
            self.images.append((values, line))
            src = (values.get("src") or "").strip()
            if src:
                self.assets.append((src, line, "img"))
        elif tag == "source":
            src = (values.get("src") or "").strip()
            if src:
                self.assets.append((src, line, "source"))
            for candidate in split_srcset(values.get("srcset") or ""):
                self.assets.append((candidate, line, "source"))
        elif tag == "script":
            self.scripts.append((values, line, self.in_head))
            src = (values.get("src") or "").strip()
            if src:
                self.assets.append((src, line, "script"))
        elif tag == "label":
            self.label_depth += 1
            target = (values.get("for") or "").strip()
            if target:
                self.label_fors.add(target)
        elif tag in {"input", "select", "textarea"}:
            self.controls.append((tag, values, line, self.label_depth > 0))

        element_id = (values.get("id") or "").strip()
        if element_id:
            if element_id in self.ids:
                self.duplicate_ids.append((element_id, line))
            else:
                self.ids[element_id] = line

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "head":
            self.in_head = False
        elif tag == "title":
            self.in_title = False
        elif tag == "label" and self.label_depth:
            self.label_depth -= 1

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)

    @property
    def title(self) -> str:
        return " ".join("".join(self.title_parts).split())


def split_srcset(value: str) -> list[str]:
    return [part.strip().split()[0] for part in value.split(",") if part.strip()]


def is_external_or_dynamic(value: str) -> bool:
    if not value or any(marker in value for marker in ("{", "}", "<", ">")):
        return True
    if value.startswith(("#", "//", "data:", "blob:", "mailto:", "tel:", "javascript:")):
        return True
    return bool(urlsplit(value).scheme)


def resolve_asset(value: str, html_path: Path, site_root: Path) -> Path | None:
    if is_external_or_dynamic(value):
        return None
    clean = unquote(urlsplit(value).path)
    if not clean or clean.endswith("/"):
        return None
    if clean.startswith("/"):
        return site_root / clean.lstrip("/")
    return html_path.parent / clean


def audit_document(
    content: str,
    html_path: Path | None,
    site_root: Path | None,
    check_assets: bool,
) -> list[Finding]:
    parser = AuditParser()
    findings: list[Finding] = []
    try:
        parser.feed(content)
        parser.close()
    except Exception as error:
        return [Finding("ERROR", "html-parse", f"HTML parser error: {error}")]

    robots = parser.meta_name.get("robots", "").lower()
    noindex = "noindex" in robots

    if not parser.html_lang:
        findings.append(Finding("ERROR", "html-lang", "Missing html lang attribute"))
    if not parser.title:
        findings.append(Finding("ERROR", "title", "Missing non-empty title"))
    if "viewport" not in parser.meta_name:
        findings.append(Finding("ERROR", "viewport", "Missing viewport meta tag"))
    else:
        viewport = parser.meta_name["viewport"].lower().replace(" ", "")
        if "user-scalable=no" in viewport or "maximum-scale=1" in viewport:
            findings.append(Finding("ERROR", "viewport-zoom", "Viewport restricts user zoom"))
    if len(parser.h1_lines) != 1:
        findings.append(Finding("ERROR", "h1-count", f"Expected one h1, found {len(parser.h1_lines)}"))
    if len(parser.main_lines) != 1:
        findings.append(Finding("WARN", "main-count", f"Expected one main landmark, found {len(parser.main_lines)}"))

    description = parser.meta_name.get("description", "").strip()
    if not noindex and not description:
        findings.append(Finding("ERROR", "description", "Indexable page lacks meta description"))
    if not noindex:
        if len(parser.canonicals) != 1 or not parser.canonicals[0][0]:
            findings.append(Finding("WARN", "canonical", f"Expected one non-empty canonical link, found {len(parser.canonicals)}"))
        for prop in ("og:title", "og:description", "og:image"):
            if not parser.meta_property.get(prop, "").strip():
                findings.append(Finding("WARN", "open-graph", f"Missing {prop}"))

    for element_id, line in parser.duplicate_ids:
        findings.append(Finding("ERROR", "duplicate-id", f"Duplicate id '{element_id}'", line))

    for attrs, line in parser.images:
        if "alt" not in attrs:
            findings.append(Finding("ERROR", "image-alt", "Image lacks alt attribute", line))
        if not (attrs.get("width") and attrs.get("height")):
            findings.append(Finding("WARN", "image-size", "Image lacks intrinsic width and height", line))
        if (attrs.get("loading") or "").lower() == "lazy" and (attrs.get("fetchpriority") or "").lower() == "high":
            findings.append(Finding("WARN", "image-priority", "Image combines loading=lazy with fetchpriority=high", line))

    for tag, attrs, line, wrapped in parser.controls:
        control_type = (attrs.get("type") or "text").lower() if tag == "input" else tag
        if control_type in VOID_CONTROLS:
            continue
        element_id = (attrs.get("id") or "").strip()
        named = bool(
            wrapped
            or (element_id and element_id in parser.label_fors)
            or (attrs.get("aria-label") or "").strip()
            or (attrs.get("aria-labelledby") or "").strip()
        )
        if not named:
            findings.append(Finding("ERROR", "control-name", f"{tag} control lacks an accessible label", line))

    for attrs, line, in_head in parser.scripts:
        src = (attrs.get("src") or "").strip()
        script_type = (attrs.get("type") or "").lower()
        if src and in_head and "defer" not in attrs and "async" not in attrs and script_type != "module":
            findings.append(Finding("WARN", "blocking-script", "Head script lacks defer, async, or type=module", line))

    if check_assets and html_path is not None and site_root is not None:
        seen: set[Path] = set()
        for value, line, kind in parser.assets:
            candidate = resolve_asset(value, html_path, site_root)
            if candidate is None:
                continue
            candidate = candidate.resolve()
            if candidate in seen:
                continue
            seen.add(candidate)
            if not candidate.is_file():
                findings.append(Finding("ERROR", "missing-asset", f"Missing local {kind} asset: {value}", line))

    return findings


def collect_html(inputs: list[str]) -> list[Path]:
    paths: list[Path] = []
    for raw in inputs:
        path = Path(raw).expanduser().resolve()
        if path.is_file() and path.suffix.lower() in {".html", ".htm"}:
            paths.append(path)
        elif path.is_dir():
            paths.extend(
                item
                for item in path.rglob("*")
                if item.is_file()
                and item.suffix.lower() in {".html", ".htm"}
                and not IGNORED_PARTS.intersection(item.relative_to(path).parts)
            )
    return sorted(set(paths))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="HTML files/directories, or '-' for stdin")
    parser.add_argument("--root", type=Path, help="Site root used to resolve root-relative assets")
    parser.add_argument("--no-assets", action="store_true", help="Skip local asset existence checks")
    parser.add_argument("--strict", action="store_true", help="Return non-zero when warnings exist")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    reports: list[dict[str, object]] = []

    if "-" in args.paths:
        content = sys.stdin.read()
        findings = audit_document(content, None, None, False)
        reports.append({"path": "<stdin>", "findings": [asdict(item) for item in findings]})

    file_inputs = [value for value in args.paths if value != "-"]
    files = collect_html(file_inputs)
    if file_inputs and not files:
        reports.append({
            "path": "<inputs>",
            "findings": [asdict(Finding("ERROR", "no-html", "No HTML files found"))],
        })

    explicit_root = args.root.expanduser().resolve() if args.root else None
    for path in files:
        site_root = explicit_root or path.parent
        try:
            content = path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError) as error:
            findings = [Finding("ERROR", "read", f"Cannot read UTF-8 HTML: {error}")]
        else:
            findings = audit_document(content, path, site_root, not args.no_assets)
        reports.append({"path": str(path), "findings": [asdict(item) for item in findings]})

    error_count = sum(
        item["severity"] == "ERROR"
        for report in reports
        for item in report["findings"]
    )
    warning_count = sum(
        item["severity"] == "WARN"
        for report in reports
        for item in report["findings"]
    )

    if args.json:
        print(json.dumps({
            "ok": error_count == 0 and (warning_count == 0 or not args.strict),
            "files": len(reports),
            "errors": error_count,
            "warnings": warning_count,
            "reports": reports,
        }, ensure_ascii=False, indent=2))
    else:
        for report in reports:
            findings = report["findings"]
            if not findings:
                print(f"[PASS] {report['path']}")
                continue
            for item in findings:
                location = f":{item['line']}" if item["line"] else ""
                print(f"[{item['severity']}] {report['path']}{location} {item['code']}: {item['message']}")
        print(f"Audited {len(reports)} document(s): {error_count} error(s), {warning_count} warning(s)")

    if error_count:
        return 1
    if args.strict and warning_count:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
