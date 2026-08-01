#!/usr/bin/env python3
"""Compare DOCX files for scoped revisions or clean/marked equivalence."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import zipfile
from pathlib import Path
from typing import Any

from lxml import etree


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W14_NS = "http://schemas.microsoft.com/office/word/2010/wordml"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS = {"w": W_NS, "w14": W14_NS, "r": R_NS}
W = f"{{{W_NS}}}"
W14 = f"{{{W14_NS}}}"
VOLATILE_ATTR = re.compile(r"(?:^|\})rsid|(?:^|\})paraId|(?:^|\})textId", re.IGNORECASE)
STABLE_PARTS = (
    "word/styles.xml",
    "word/numbering.xml",
    "word/settings.xml",
    "word/fontTable.xml",
    "word/theme/theme1.xml",
)
PROTECTED_PART_PATTERNS = (
    re.compile(r"^\[Content_Types\]\.xml$"),
    re.compile(r"^_rels/\.rels$"),
    re.compile(r"^word/_rels/.*\.rels$"),
    re.compile(r"^word/(?:header|footer)\d+\.xml$"),
    re.compile(r"^word/(?:comments|footnotes|endnotes)\.xml$"),
)


def finding(level: str, rule: str, evidence: str, impact: str, action: str) -> dict[str, str]:
    return {
        "level": level,
        "rule": rule,
        "evidence": evidence,
        "impact": impact,
        "action": action,
    }


def read_zip(path: Path) -> dict[str, bytes]:
    try:
        with zipfile.ZipFile(path) as archive:
            archive.testzip()
            return {name: archive.read(name) for name in archive.namelist()}
    except (zipfile.BadZipFile, OSError) as error:
        raise ValueError(f"cannot read DOCX {path}: {type(error).__name__}") from error


def parse_document(parts: dict[str, bytes]) -> etree._Element:
    payload = parts.get("word/document.xml")
    if payload is None:
        raise ValueError("word/document.xml is missing")
    return etree.fromstring(payload)


def final_text(node: etree._Element) -> str:
    values = node.xpath(".//w:t[not(ancestor::w:del)]", namespaces=NS)
    return "".join(item.text or "" for item in values)


def normalize_xml(node: etree._Element, *, resolve_changes: bool = False) -> bytes:
    clone = etree.fromstring(etree.tostring(node))
    for item in clone.iter():
        for key in list(item.attrib):
            if VOLATILE_ATTR.search(key):
                del item.attrib[key]
    if resolve_changes:
        for deletion in clone.xpath(".//w:del", namespaces=NS):
            parent = deletion.getparent()
            if parent is not None:
                parent.remove(deletion)
        for insertion in clone.xpath(".//w:ins", namespaces=NS):
            parent = insertion.getparent()
            if parent is None:
                continue
            position = parent.index(insertion)
            parent.remove(insertion)
            for child in reversed(list(insertion)):
                parent.insert(position, child)
    return etree.tostring(clone, method="c14n")


def body_paragraphs(root: etree._Element) -> list[etree._Element]:
    return root.xpath("/w:document/w:body/w:p", namespaces=NS)


def body_tables(root: etree._Element) -> list[etree._Element]:
    return root.xpath("/w:document/w:body/w:tbl", namespaces=NS)


def table_cells(table: etree._Element) -> list[list[list[etree._Element]]]:
    rows: list[list[list[etree._Element]]] = []
    for row in table.xpath("./w:tr", namespaces=NS):
        cells: list[list[etree._Element]] = []
        for cell in row.xpath("./w:tc", namespaces=NS):
            cells.append(cell.xpath("./w:p", namespaces=NS))
        rows.append(cells)
    return rows


def media_hashes(parts: dict[str, bytes]) -> dict[str, str]:
    return {
        name: hashlib.sha256(payload).hexdigest()
        for name, payload in parts.items()
        if name.startswith("word/media/")
    }


def allow_set(values: list[str], *, insertion: bool = False) -> set[str]:
    allowed: set[str] = set()
    paragraph_patterns = (
        re.compile(r"paragraph:\d+$"),
        re.compile(r"paragraph-id:[0-9A-Fa-f]{8}$"),
    )
    patterns = paragraph_patterns if insertion else (*paragraph_patterns,
        re.compile(r"table:\d+$"),
        re.compile(r"table-cell:\d+:\d+:\d+$"),
    )
    for value in values:
        if not any(pattern.fullmatch(value) for pattern in patterns):
            raise ValueError(f"invalid --allow locator: {value}")
        allowed.add(value)
    return allowed


def paragraph_id(paragraph: etree._Element) -> str | None:
    value = paragraph.get(f"{W14}paraId")
    return value.upper() if value and re.fullmatch(r"[0-9A-Fa-f]{8}", value) else None


def paragraph_locators(index: int, paragraph: etree._Element) -> set[str]:
    locators = {f"paragraph:{index}"}
    if value := paragraph_id(paragraph):
        locators.add(f"paragraph-id:{value}")
    return locators


def paragraph_token(paragraph: etree._Element) -> str:
    if value := paragraph_id(paragraph):
        return f"id:{value}"
    return f"xml:{hashlib.sha256(normalize_xml(paragraph)).hexdigest()}"


def paragraph_authorized(index: int, paragraph: etree._Element, allowed: set[str]) -> bool:
    return bool(paragraph_locators(index, paragraph) & allowed)


def compare_paragraph_pair(
    before: etree._Element,
    after: etree._Element,
    original_index: int,
    allowed: set[str],
    findings: list[dict[str, str]],
) -> None:
    if paragraph_authorized(original_index, before, allowed):
        return
    if normalize_xml(before) != normalize_xml(after):
        findings.append(
            finding(
                "ERROR",
                "scope.paragraph_changed",
                f"paragraph:{original_index}",
                "Text or formatting changed outside the authorized revision scope.",
                "Restore this paragraph or add its exact locator to the approved scope.",
            )
        )


def compare_body_paragraphs(
    original: list[etree._Element],
    revised: list[etree._Element],
    allowed: set[str],
    insert_after: set[str],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    valid_anchors = {
        locator
        for index, paragraph in enumerate(original)
        for locator in paragraph_locators(index, paragraph)
    }
    for locator in sorted(insert_after - valid_anchors):
        findings.append(
            finding(
                "ERROR",
                "scope.insertion_anchor_missing",
                locator,
                "The authorized insertion anchor does not exist in the original document.",
                "Correct the anchor locator before accepting any inserted paragraph.",
            )
        )

    matcher = difflib.SequenceMatcher(
        a=[paragraph_token(item) for item in original],
        b=[paragraph_token(item) for item in revised],
        autojunk=False,
    )
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for offset in range(i2 - i1):
                compare_paragraph_pair(
                    original[i1 + offset],
                    revised[j1 + offset],
                    i1 + offset,
                    allowed,
                    findings,
                )
            continue
        if tag == "insert":
            anchor_index = i1 - 1
            anchor_allowed = anchor_index >= 0 and bool(
                paragraph_locators(anchor_index, original[anchor_index]) & insert_after
            )
            if not anchor_allowed:
                findings.append(
                    finding(
                        "ERROR",
                        "scope.paragraph_inserted",
                        f"after paragraph:{anchor_index}" if anchor_index >= 0 else "before paragraph:0",
                        f"{j2 - j1} paragraph(s) were inserted outside the authorized revision scope.",
                        "Restore the original structure or authorize the exact insertion anchor.",
                    )
                )
            continue
        if tag == "replace" and (i2 - i1) == (j2 - j1):
            for offset in range(i2 - i1):
                compare_paragraph_pair(
                    original[i1 + offset],
                    revised[j1 + offset],
                    i1 + offset,
                    allowed,
                    findings,
                )
            continue
        if tag == "replace" and 0 < (i2 - i1) < (j2 - j1):
            original_count = i2 - i1
            leading_anchor = i1 - 1
            leading_allowed = leading_anchor >= 0 and bool(
                paragraph_locators(leading_anchor, original[leading_anchor]) & insert_after
            )
            trailing_anchor = i2 - 1
            trailing_allowed = bool(
                paragraph_locators(trailing_anchor, original[trailing_anchor]) & insert_after
            )
            if leading_allowed:
                revised_start = j2 - original_count
            elif trailing_allowed:
                revised_start = j1
            else:
                revised_start = -1
            if revised_start >= 0:
                for offset in range(original_count):
                    compare_paragraph_pair(
                        original[i1 + offset],
                        revised[revised_start + offset],
                        i1 + offset,
                        allowed,
                        findings,
                    )
                continue
        findings.append(
            finding(
                "ERROR",
                "scope.paragraph_structure",
                f"original[{i1}:{i2}]->revised[{j1}:{j2}]",
                "Paragraph deletion or a mixed replacement-and-insertion changed the document structure.",
                "Use stable paraId locators, narrow the change, or restore the original paragraph structure.",
            )
        )
    return findings


def compare_scope(
    original_parts: dict[str, bytes],
    revised_parts: dict[str, bytes],
    allowed: set[str],
    insert_after: set[str] | None = None,
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    original_root = parse_document(original_parts)
    revised_root = parse_document(revised_parts)
    original_paragraphs = body_paragraphs(original_root)
    revised_paragraphs = body_paragraphs(revised_root)
    findings.extend(
        compare_body_paragraphs(
            original_paragraphs,
            revised_paragraphs,
            allowed,
            insert_after or set(),
        )
    )

    original_tables = body_tables(original_root)
    revised_tables = body_tables(revised_root)
    if len(original_tables) != len(revised_tables):
        findings.append(
            finding(
                "ERROR",
                "scope.table_count",
                f"{len(original_tables)}->{len(revised_tables)}",
                "Table insertion or deletion changed the document structure.",
                "Authorize the structural change explicitly or restore the table set.",
            )
        )
    for table_index, (before_table, after_table) in enumerate(zip(original_tables, revised_tables)):
        if f"table:{table_index}" in allowed:
            continue
        before_cells = table_cells(before_table)
        after_cells = table_cells(after_table)
        if len(before_cells) != len(after_cells) or any(
            len(before_row) != len(after_row)
            for before_row, after_row in zip(before_cells, after_cells)
        ):
            findings.append(
                finding(
                    "ERROR",
                    "scope.table_structure",
                    f"table:{table_index}",
                    "Rows or cells changed outside the authorized scope.",
                    "Restore the table structure or authorize the complete table.",
                )
            )
            continue
        for row_index, (before_row, after_row) in enumerate(zip(before_cells, after_cells)):
            for cell_index, (before_cell, after_cell) in enumerate(zip(before_row, after_row)):
                locator = f"table-cell:{table_index}:{row_index}:{cell_index}"
                if locator in allowed:
                    continue
                before_xml = b"".join(normalize_xml(paragraph) for paragraph in before_cell)
                after_xml = b"".join(normalize_xml(paragraph) for paragraph in after_cell)
                if before_xml != after_xml:
                    findings.append(
                        finding(
                            "ERROR",
                            "scope.table_cell_changed",
                            locator,
                            "Table text or formatting changed outside the authorized scope.",
                            "Restore the cell or add its exact locator to the approved scope.",
                        )
                    )

    if media_hashes(original_parts) != media_hashes(revised_parts):
        findings.append(
            finding(
                "ERROR",
                "scope.media_changed",
                "word/media",
                "An embedded image was added, removed, or modified outside the declared scope.",
                "Restore the media set or authorize and visually validate the image change.",
            )
        )

    for part in STABLE_PARTS:
        if original_parts.get(part) != revised_parts.get(part):
            findings.append(
                finding(
                    "ERROR",
                    "scope.global_format_changed",
                    part,
                    "A global style, numbering, setting, font, or theme part changed.",
                    "Restore the part unless a global format change was explicitly authorized.",
                )
            )

    protected_parts = {
        name
        for name in set(original_parts) | set(revised_parts)
        if any(pattern.fullmatch(name) for pattern in PROTECTED_PART_PATTERNS)
    }
    for part in sorted(protected_parts):
        if original_parts.get(part) != revised_parts.get(part):
            findings.append(
                finding(
                    "ERROR",
                    "scope.package_part_changed",
                    part,
                    "A relationship, header, footer, note, comment, or package contract changed outside the authorized scope.",
                    "Restore the protected package part or authorize and validate that structural change explicitly.",
                )
            )

    before_sections = original_root.xpath("/w:document/w:body/w:sectPr", namespaces=NS)
    after_sections = revised_root.xpath("/w:document/w:body/w:sectPr", namespaces=NS)
    if [normalize_xml(item) for item in before_sections] != [normalize_xml(item) for item in after_sections]:
        findings.append(
            finding(
                "ERROR",
                "scope.section_layout_changed",
                "word/document.xml:sectPr",
                "Page size, margins, columns, headers, footers, or pagination settings changed.",
                "Restore section properties unless the layout change was explicitly authorized.",
            )
        )
    return findings


def semantic_structure(root: etree._Element) -> dict[str, Any]:
    paragraphs = [final_text(item) for item in body_paragraphs(root)]
    tables = []
    for table in body_tables(root):
        rows = []
        for row in table_cells(table):
            rows.append([[final_text(paragraph) for paragraph in cell] for cell in row])
        tables.append(rows)
    drawings = root.xpath("count(.//w:drawing)", namespaces=NS)
    captions = root.xpath("count(.//w:fldSimple | .//w:instrText)", namespaces=NS)
    return {"paragraphs": paragraphs, "tables": tables, "drawings": drawings, "fields": captions}


def compare_equivalence(
    clean_parts: dict[str, bytes], marked_parts: dict[str, bytes]
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    clean = semantic_structure(parse_document(clean_parts))
    marked = semantic_structure(parse_document(marked_parts))
    if clean != marked:
        findings.append(
            finding(
                "ERROR",
                "derivation.visible_content_mismatch",
                "word/document.xml",
                "The clean and marked files do not resolve to the same visible text and structure.",
                "Regenerate both files from the same revision record.",
            )
        )
    if media_hashes(clean_parts) != media_hashes(marked_parts):
        findings.append(
            finding(
                "ERROR",
                "derivation.media_mismatch",
                "word/media",
                "The clean and marked files contain different embedded images.",
                "Regenerate both files from one content source.",
            )
        )
    return findings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original", type=Path)
    parser.add_argument("revised", type=Path)
    parser.add_argument("--mode", choices=("scope", "equivalence"), default="scope")
    parser.add_argument("--allow", action="append", default=[])
    parser.add_argument("--allow-insert-after", action="append", default=[])
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        original_parts = read_zip(args.original)
        revised_parts = read_zip(args.revised)
        if args.mode == "scope":
            findings = compare_scope(
                original_parts,
                revised_parts,
                allow_set(args.allow),
                allow_set(args.allow_insert_after, insertion=True),
            )
        else:
            if args.allow or args.allow_insert_after:
                raise ValueError("--allow and --allow-insert-after are only valid in scope mode")
            findings = compare_equivalence(original_parts, revised_parts)
    except (OSError, ValueError, etree.XMLSyntaxError) as error:
        findings = [
            finding(
                "ERROR",
                "comparison.unreadable",
                type(error).__name__,
                "The requested DOCX comparison could not be completed.",
                "Repair the files or locator arguments and rerun the comparison.",
            )
        ]
    errors = [item for item in findings if item["level"] == "ERROR"]
    payload = {"ok": not errors, "mode": args.mode, "findings": findings}
    if args.as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for item in findings:
            print(f"[{item['level']}] {item['rule']}: {item['evidence']}")
        print(f"DOCX comparison {'passed' if not errors else 'failed'}: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
