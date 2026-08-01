#!/usr/bin/env python3
"""Derive clean and tracked DOCX files from one exact revision record."""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import json
import os
import re
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from lxml import etree


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W14_NS = "http://schemas.microsoft.com/office/word/2010/wordml"
XML_NS = "http://www.w3.org/XML/1998/namespace"
NS = {"w": W_NS, "w14": W14_NS}
W = f"{{{W_NS}}}"
W14 = f"{{{W14_NS}}}"
ALLOWED_HIGHLIGHTS = {
    "black",
    "blue",
    "cyan",
    "darkBlue",
    "darkCyan",
    "darkGray",
    "darkGreen",
    "darkMagenta",
    "darkRed",
    "darkYellow",
    "green",
    "lightGray",
    "magenta",
    "none",
    "red",
    "white",
    "yellow",
}


class RevisionError(ValueError):
    """Raised when an exact, format-preserving revision cannot be guaranteed."""


def load_record(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise RevisionError("revision record root must be an object")
    if payload.get("schema_version") != 1:
        raise RevisionError("revision record schema_version must be 1")
    changes = payload.get("changes")
    if not isinstance(changes, list) or not changes:
        raise RevisionError("revision record must contain a non-empty changes list")
    ids = [item.get("id") for item in changes if isinstance(item, dict)]
    if len(ids) != len(changes) or not all(isinstance(value, str) and value.strip() for value in ids):
        raise RevisionError("every change must have a non-empty id")
    if len(set(ids)) != len(ids):
        raise RevisionError("change ids must be unique")
    return payload


def validate_previous_locks(current: dict[str, Any], previous: dict[str, Any] | None) -> None:
    if previous is None:
        return
    current_locked = current.get("locked_decisions")
    previous_locked = previous.get("locked_decisions")
    current_locked = current_locked if isinstance(current_locked, dict) else {}
    previous_locked = previous_locked if isinstance(previous_locked, dict) else {}
    supersedes = current.get("supersedes")
    supersedes = supersedes if isinstance(supersedes, list) else []
    overrides = {
        item.get("key"): item
        for item in supersedes
        if isinstance(item, dict)
        and isinstance(item.get("key"), str)
        and isinstance(item.get("source"), str)
        and item.get("source").strip()
        and isinstance(item.get("reason"), str)
        and item.get("reason").strip()
    }
    for key, old_entry in previous_locked.items():
        if key not in current_locked:
            raise RevisionError(f"locked decision dropped without override: {key}")
        old_value = old_entry.get("value") if isinstance(old_entry, dict) else None
        new_entry = current_locked[key]
        new_value = new_entry.get("value") if isinstance(new_entry, dict) else None
        if new_value == old_value:
            continue
        override = overrides.get(key)
        if not override or override.get("previous_value") != old_value or override.get("new_value") != new_value:
            raise RevisionError(f"locked decision changed without traceable supersedes entry: {key}")


def read_part(path: Path, part: str) -> bytes:
    try:
        with zipfile.ZipFile(path) as archive:
            return archive.read(part)
    except (zipfile.BadZipFile, KeyError) as error:
        raise RevisionError(f"cannot read {part} from DOCX: {type(error).__name__}") from error


def body_paragraph(root: etree._Element, index: int) -> etree._Element:
    items = root.xpath("/w:document/w:body/w:p", namespaces=NS)
    if index < 0 or index >= len(items):
        raise RevisionError(f"paragraph index out of range: {index}")
    return items[index]


def paragraph_by_id(root: etree._Element, value: Any) -> etree._Element:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9A-Fa-f]{8}", value):
        raise RevisionError("paragraph para_id must be exactly eight hexadecimal characters")
    expected = value.upper()
    items = [
        item
        for item in root.xpath(".//w:p[@w14:paraId]", namespaces=NS)
        if item.get(f"{W14}paraId", "").upper() == expected
    ]
    if len(items) != 1:
        raise RevisionError(f"paragraph para_id must identify exactly one paragraph; found {len(items)}")
    return items[0]


def table_cell_paragraph(root: etree._Element, locator: dict[str, Any]) -> etree._Element:
    coordinates = {}
    for key in ("table", "row", "cell", "paragraph"):
        value = locator.get(key)
        if not isinstance(value, int) or value < 0:
            raise RevisionError(f"table-cell-paragraph locator requires a non-negative {key}")
        coordinates[key] = value
    tables = root.xpath("/w:document/w:body/w:tbl", namespaces=NS)
    try:
        table = tables[coordinates["table"]]
        row = table.xpath("./w:tr", namespaces=NS)[coordinates["row"]]
        cell = row.xpath("./w:tc", namespaces=NS)[coordinates["cell"]]
        return cell.xpath("./w:p", namespaces=NS)[coordinates["paragraph"]]
    except IndexError as error:
        rendered = ":".join(str(coordinates[key]) for key in coordinates)
        raise RevisionError(f"table-cell-paragraph locator out of range: {rendered}") from error


def locate_paragraph(root: etree._Element, locator: Any) -> etree._Element:
    if not isinstance(locator, dict):
        raise RevisionError("change locator must be an object")
    kind = locator.get("kind")
    if kind == "paragraph":
        index = locator.get("index")
        para_id = locator.get("para_id")
        if para_id is None and not isinstance(index, int):
            raise RevisionError("paragraph locator requires para_id or an integer index")
        selected = paragraph_by_id(root, para_id) if para_id is not None else None
        if index is not None:
            if not isinstance(index, int):
                raise RevisionError("paragraph index must be an integer")
            indexed = body_paragraph(root, index)
            if selected is not None and selected is not indexed:
                raise RevisionError("paragraph para_id and index resolve to different targets")
            selected = indexed
        if selected is None:
            raise RevisionError("paragraph locator did not resolve a target")
        return selected
    if kind == "table-cell-paragraph":
        return table_cell_paragraph(root, locator)
    raise RevisionError(f"unsupported locator kind: {kind!r}")


def text_nodes(paragraph: etree._Element) -> list[etree._Element]:
    return paragraph.xpath(".//w:t[not(ancestor::w:del)]", namespaces=NS)


def visible_text(paragraph: etree._Element) -> str:
    return "".join(node.text or "" for node in text_nodes(paragraph))


def node_span(paragraph: etree._Element, old: str) -> tuple[etree._Element, int, int]:
    if not old:
        raise RevisionError("old text must be non-empty")
    text = visible_text(paragraph)
    count = text.count(old)
    if count != 1:
        raise RevisionError(f"exact target must occur once in the selected paragraph; found {count}")
    start = text.index(old)
    end = start + len(old)
    offset = 0
    for node in text_nodes(paragraph):
        value = node.text or ""
        next_offset = offset + len(value)
        if start >= offset and end <= next_offset:
            run = node.getparent()
            if run is None or run.tag != W + "r":
                raise RevisionError("target text is not contained in a normal Word run")
            if run.xpath("ancestor::w:ins | ancestor::w:del", namespaces=NS):
                raise RevisionError("target text is inside pre-existing tracked changes")
            non_text_children = [child for child in run if child.tag not in {W + "rPr", W + "t"}]
            if non_text_children or len(run.xpath("./w:t", namespaces=NS)) != 1:
                raise RevisionError("target run contains fields, drawings, breaks, or multiple text nodes")
            return node, start - offset, end - offset
        offset = next_offset
    raise RevisionError("target spans differently structured runs; narrow the target or choose another locator")


def set_text(node: etree._Element, value: str) -> None:
    node.text = value
    attr = f"{{{XML_NS}}}space"
    if value[:1].isspace() or value[-1:].isspace():
        node.set(attr, "preserve")
    else:
        node.attrib.pop(attr, None)


def clone_run(run: etree._Element, text: str, *, deleted: bool = False, highlight: str | None = None) -> etree._Element:
    clone = etree.Element(W + "r")
    properties = run.find(W + "rPr")
    if properties is not None:
        properties = copy.deepcopy(properties)
        clone.append(properties)
    if highlight and highlight != "none":
        properties = clone.find(W + "rPr")
        if properties is None:
            properties = etree.Element(W + "rPr")
            clone.insert(0, properties)
        existing = properties.find(W + "highlight")
        if existing is None:
            existing = etree.SubElement(properties, W + "highlight")
        existing.set(W + "val", highlight)
    node = etree.SubElement(clone, W + ("delText" if deleted else "t"))
    set_text(node, text)
    return clone


def next_change_id(root: etree._Element) -> int:
    values = []
    for node in root.xpath(".//w:ins | .//w:del", namespaces=NS):
        raw = node.get(W + "id")
        if raw and raw.isdigit():
            values.append(int(raw))
    return max(values, default=-1) + 1


def apply_clean_change(root: etree._Element, change: dict[str, Any]) -> None:
    paragraph = locate_paragraph(root, change.get("locator"))
    old = change.get("old")
    new = change.get("new")
    if not isinstance(old, str) or not isinstance(new, str):
        raise RevisionError(f"change {change.get('id')} requires string old and new values")
    node, start, end = node_span(paragraph, old)
    value = node.text or ""
    set_text(node, value[:start] + new + value[end:])


def apply_marked_change(
    root: etree._Element,
    change: dict[str, Any],
    *,
    author: str,
    changed_at: str,
    highlight: str | None,
    change_id: int,
) -> int:
    paragraph = locate_paragraph(root, change.get("locator"))
    old = change.get("old")
    new = change.get("new")
    if not isinstance(old, str) or not isinstance(new, str):
        raise RevisionError(f"change {change.get('id')} requires string old and new values")
    node, start, end = node_span(paragraph, old)
    run = node.getparent()
    parent = run.getparent()
    if parent is None:
        raise RevisionError("target run has no parent")
    position = parent.index(run)
    value = node.text or ""
    replacement: list[etree._Element] = []
    if value[:start]:
        replacement.append(clone_run(run, value[:start]))
    deletion = etree.Element(W + "del")
    deletion.set(W + "id", str(change_id))
    deletion.set(W + "author", author)
    deletion.set(W + "date", changed_at)
    deletion.append(clone_run(run, old, deleted=True))
    replacement.append(deletion)
    insertion = etree.Element(W + "ins")
    insertion.set(W + "id", str(change_id + 1))
    insertion.set(W + "author", author)
    insertion.set(W + "date", changed_at)
    insertion.append(clone_run(run, new, highlight=highlight))
    replacement.append(insertion)
    if value[end:]:
        replacement.append(clone_run(run, value[end:]))
    parent.remove(run)
    for offset, item in enumerate(replacement):
        parent.insert(position + offset, item)
    return change_id + 2


def write_docx(source: Path, output: Path, document_xml: bytes) -> None:
    if output.exists():
        raise RevisionError(f"refusing to overwrite existing output: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=output.stem + "_", suffix=".docx", dir=output.parent)
    os.close(fd)
    temporary = Path(temporary_name)
    try:
        with zipfile.ZipFile(source) as incoming, zipfile.ZipFile(temporary, "w") as outgoing:
            for info in incoming.infolist():
                payload = document_xml if info.filename == "word/document.xml" else incoming.read(info.filename)
                outgoing.writestr(info, payload)
        temporary.replace(output)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("record", type=Path)
    parser.add_argument("--clean-out", type=Path, required=True)
    parser.add_argument("--marked-out", type=Path, required=True)
    parser.add_argument("--previous-record", type=Path)
    parser.add_argument("--author", default="Reviewer")
    parser.add_argument("--highlight", choices=sorted(ALLOWED_HIGHLIGHTS), default="yellow")
    parser.add_argument("--date", dest="changed_at")
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if not args.input.is_file() or args.input.suffix.lower() != ".docx":
            raise RevisionError("input must be an existing DOCX file")
        if args.clean_out.resolve(strict=False) == args.marked_out.resolve(strict=False):
            raise RevisionError("clean and marked outputs must be different paths")
        if not args.author.strip():
            raise RevisionError("tracked-change author must be non-empty")
        for output in (args.clean_out, args.marked_out):
            if output.exists():
                raise RevisionError(f"refusing to overwrite existing output: {output}")
        record = load_record(args.record)
        previous = load_record(args.previous_record) if args.previous_record else None
        validate_previous_locks(record, previous)
        original_xml = read_part(args.input, "word/document.xml")
        clean_root = etree.fromstring(original_xml)
        marked_root = etree.fromstring(original_xml)
        changed_at = args.changed_at or dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        next_id = next_change_id(marked_root)
        for change in record["changes"]:
            apply_clean_change(clean_root, change)
            next_id = apply_marked_change(
                marked_root,
                change,
                author=args.author,
                changed_at=changed_at,
                highlight=args.highlight,
                change_id=next_id,
            )
        clean_xml = etree.tostring(clean_root, xml_declaration=True, encoding="UTF-8", standalone=True)
        marked_xml = etree.tostring(marked_root, xml_declaration=True, encoding="UTF-8", standalone=True)
        created: list[Path] = []
        try:
            write_docx(args.input, args.clean_out, clean_xml)
            created.append(args.clean_out)
            write_docx(args.input, args.marked_out, marked_xml)
            created.append(args.marked_out)
        except Exception:
            for output in created:
                output.unlink(missing_ok=True)
            raise
        payload = {
            "ok": True,
            "input_sha256": sha256(args.input),
            "record_sha256": sha256(args.record),
            "clean_sha256": sha256(args.clean_out),
            "marked_sha256": sha256(args.marked_out),
            "changes": [item["id"] for item in record["changes"]],
        }
        if args.as_json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(f"Derived clean and marked DOCX files from {len(record['changes'])} exact change(s).")
        return 0
    except (OSError, json.JSONDecodeError, zipfile.BadZipFile, etree.XMLSyntaxError, RevisionError) as error:
        payload = {"ok": False, "error": type(error).__name__, "detail": str(error)}
        if args.as_json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(f"ERROR: {type(error).__name__}: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
