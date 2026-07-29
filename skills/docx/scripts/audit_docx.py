#!/usr/bin/env python3
"""Audit DOCX structure, references, images, revisions, and anonymity risks."""

from __future__ import annotations

import argparse
import io
import json
import posixpath
import re
import struct
import zipfile
from pathlib import Path
from typing import Any

from lxml import etree


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PR_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
WP_NS = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
CP_NS = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
DC_NS = "http://purl.org/dc/elements/1.1/"
NS = {
    "w": W_NS,
    "r": R_NS,
    "pr": PR_NS,
    "wp": WP_NS,
    "a": A_NS,
    "cp": CP_NS,
    "dc": DC_NS,
}
W = f"{{{W_NS}}}"
R = f"{{{R_NS}}}"
EMU_PER_INCH = 914400
REF_PATTERN = re.compile(r"\bREF\s+([^\s\\]+)", re.IGNORECASE)


def finding(level: str, rule: str, evidence: str, impact: str, action: str) -> dict[str, str]:
    return {
        "level": level,
        "rule": rule,
        "evidence": evidence,
        "impact": impact,
        "action": action,
    }


def parse_xml(parts: dict[str, bytes], name: str) -> etree._Element | None:
    payload = parts.get(name)
    return etree.fromstring(payload) if payload is not None else None


def image_dimensions(payload: bytes, extension: str) -> tuple[int, int] | None:
    extension = extension.lower()
    if extension == ".png" and payload.startswith(b"\x89PNG\r\n\x1a\n") and len(payload) >= 24:
        return struct.unpack(">II", payload[16:24])
    if extension in {".jpg", ".jpeg"} and payload.startswith(b"\xff\xd8"):
        stream = io.BytesIO(payload)
        stream.read(2)
        while True:
            marker = stream.read(1)
            if not marker:
                return None
            if marker != b"\xff":
                continue
            code = stream.read(1)
            while code == b"\xff":
                code = stream.read(1)
            if code in {b"\xd8", b"\xd9"}:
                continue
            size_raw = stream.read(2)
            if len(size_raw) != 2:
                return None
            size = struct.unpack(">H", size_raw)[0]
            if code and code[0] in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}:
                data = stream.read(5)
                if len(data) != 5:
                    return None
                height, width = struct.unpack(">HH", data[1:5])
                return width, height
            stream.seek(max(size - 2, 0), io.SEEK_CUR)
    return None


def relationship_targets(parts: dict[str, bytes], rel_name: str) -> dict[str, tuple[str, str]]:
    root = parse_xml(parts, rel_name)
    if root is None:
        return {}
    if rel_name == "_rels/.rels":
        source_part = ""
    elif "/_rels/" in rel_name:
        source_part = rel_name.split("/_rels/", 1)[0]
    else:
        source_part = posixpath.dirname(rel_name)
    mapping: dict[str, tuple[str, str]] = {}
    for item in root.xpath("./pr:Relationship", namespaces=NS):
        rel_id = item.get("Id")
        target = item.get("Target")
        rel_type = item.get("Type", "")
        if not rel_id or not target or item.get("TargetMode") == "External":
            continue
        resolved = posixpath.normpath(posixpath.join(source_part, target))
        mapping[rel_id] = (resolved, rel_type)
    return mapping


def location(part: str, node: etree._Element | None = None) -> str:
    if node is not None and node.sourceline:
        return f"{part}:{node.sourceline}"
    return part


def audit(
    path: Path,
    *,
    anonymous: bool = False,
    minimum_dpi: float = 300.0,
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    try:
        with zipfile.ZipFile(path) as archive:
            bad_member = archive.testzip()
            if bad_member:
                return [
                    finding(
                        "ERROR",
                        "package.crc",
                        bad_member,
                        "The DOCX package contains a corrupt ZIP member.",
                        "Recover or regenerate the document before editing or submission.",
                    )
                ]
            parts = {name: archive.read(name) for name in archive.namelist()}
    except (OSError, zipfile.BadZipFile) as error:
        return [
            finding(
                "ERROR",
                "package.unreadable",
                f"{path.name}:{type(error).__name__}",
                "The file is not a readable DOCX package.",
                "Recover or regenerate the document before continuing.",
            )
        ]

    document = parse_xml(parts, "word/document.xml")
    if document is None:
        return [
            finding(
                "ERROR",
                "package.document_missing",
                "word/document.xml",
                "The DOCX package lacks its main document part.",
                "Recover or regenerate the file.",
            )
        ]

    for rel_name in [name for name in parts if name.endswith(".rels")]:
        for rel_id, (target, _rel_type) in relationship_targets(parts, rel_name).items():
            if target not in parts:
                findings.append(
                    finding(
                        "ERROR",
                        "relationships.target_missing",
                        f"{rel_name}:{rel_id}->{target}",
                        "A relationship points to a missing embedded part.",
                        "Restore the target part or remove the stale relationship and reference.",
                    )
                )

    bookmarks = {
        item.get(W + "name")
        for item in document.xpath(".//w:bookmarkStart", namespaces=NS)
        if item.get(W + "name")
    }
    field_nodes = document.xpath(".//w:instrText | .//w:fldSimple", namespaces=NS)
    referenced: list[tuple[str, etree._Element]] = []
    for node in field_nodes:
        instruction = node.text if node.tag == W + "instrText" else node.get(W + "instr", "")
        for match in REF_PATTERN.finditer(instruction or ""):
            referenced.append((match.group(1), node))
    for name, node in referenced:
        if name not in bookmarks:
            findings.append(
                finding(
                    "ERROR",
                    "references.bookmark_missing",
                    f"{location('word/document.xml', node)}:{name}",
                    "A cross-reference points to a missing bookmark.",
                    "Repair the field/bookmark pair and update fields in Word or LibreOffice.",
                )
            )

    bookmark_ids = [
        item.get(W + "id")
        for item in document.xpath(".//w:bookmarkStart", namespaces=NS)
        if item.get(W + "id") is not None
    ]
    end_ids = {
        item.get(W + "id")
        for item in document.xpath(".//w:bookmarkEnd", namespaces=NS)
        if item.get(W + "id") is not None
    }
    for bookmark_id in bookmark_ids:
        if bookmark_id not in end_ids:
            findings.append(
                finding(
                    "ERROR",
                    "references.bookmark_unpaired",
                    f"word/document.xml:bookmark:{bookmark_id}",
                    "A bookmark start has no matching end marker.",
                    "Repair the bookmark structure before updating cross-references.",
                )
            )

    change_nodes = document.xpath(".//w:ins | .//w:del | .//w:moveFrom | .//w:moveTo", namespaces=NS)
    if change_nodes:
        level = "ERROR" if anonymous else "WARN"
        findings.append(
            finding(
                level,
                "anonymity.tracked_changes",
                f"word/document.xml:{len(change_nodes)} change element(s)",
                "Tracked changes can expose revision history or produce an unintended submission view.",
                "Use the marked file only when requested; accept changes and re-audit the anonymous clean file.",
            )
        )

    comments = parse_xml(parts, "word/comments.xml")
    comment_nodes = comments.xpath(".//w:comment", namespaces=NS) if comments is not None else []
    if comment_nodes:
        level = "ERROR" if anonymous else "WARN"
        findings.append(
            finding(
                level,
                "anonymity.comments",
                f"word/comments.xml:{len(comment_nodes)} comment(s)",
                "Comments can expose author identity or internal review discussion.",
                "Remove comments from the anonymous clean file and re-audit it.",
            )
        )

    hidden_nodes = document.xpath(".//w:rPr/w:vanish | .//w:pPr/w:rPr/w:vanish", namespaces=NS)
    if hidden_nodes:
        level = "ERROR" if anonymous else "WARN"
        findings.append(
            finding(
                level,
                "anonymity.hidden_text",
                location("word/document.xml", hidden_nodes[0]),
                "Hidden text may reveal internal notes or undisclosed content.",
                "Inspect and remove unintended hidden text before submission.",
            )
        )

    core = parse_xml(parts, "docProps/core.xml")
    if core is not None:
        for xpath, key in (("./dc:creator", "creator"), ("./cp:lastModifiedBy", "lastModifiedBy")):
            nodes = core.xpath(xpath, namespaces=NS)
            if any((node.text or "").strip() for node in nodes):
                level = "ERROR" if anonymous else "WARN"
                findings.append(
                    finding(
                        level,
                        "anonymity.core_property",
                        f"docProps/core.xml:{key}=set",
                        "A document property may disclose an author or workstation identity.",
                        "Clear identifying core properties in the anonymous clean file and re-audit it.",
                    )
                )

    document_rels = relationship_targets(parts, "word/_rels/document.xml.rels")
    for drawing in document.xpath(".//w:drawing", namespaces=NS):
        extents = drawing.xpath(".//wp:extent", namespaces=NS)
        blips = drawing.xpath(".//a:blip", namespaces=NS)
        if not extents or not blips:
            findings.append(
                finding(
                    "WARN",
                    "images.structure_incomplete",
                    location("word/document.xml", drawing),
                    "An embedded drawing lacks a measurable extent or image relationship.",
                    "Inspect the drawing visually and repair its OOXML relationship if needed.",
                )
            )
            continue
        extent = extents[0]
        rel_id = blips[0].get(R + "embed")
        target = document_rels.get(rel_id or "", ("", ""))[0]
        payload = parts.get(target)
        if payload is None:
            continue
        extension = Path(target).suffix.lower()
        width_in = int(extent.get("cx", "0")) / EMU_PER_INCH
        height_in = int(extent.get("cy", "0")) / EMU_PER_INCH
        pixels = image_dimensions(payload, extension)
        if extension in {".svg", ".emf", ".wmf"}:
            findings.append(
                finding(
                    "INFO",
                    "images.vector",
                    f"{target}:{width_in:.2f}x{height_in:.2f}in",
                    "The image uses a vector-capable embedded format.",
                    "Confirm text and line weights in the final rendered page.",
                )
            )
        elif pixels and width_in > 0 and height_in > 0:
            dpi_x = pixels[0] / width_in
            dpi_y = pixels[1] / height_in
            effective = min(dpi_x, dpi_y)
            level = "WARN" if effective < minimum_dpi else "INFO"
            findings.append(
                finding(
                    level,
                    "images.effective_dpi",
                    f"{target}:{pixels[0]}x{pixels[1]}px;{width_in:.2f}x{height_in:.2f}in;{effective:.0f}dpi",
                    "Low effective resolution can make labels and lines unreadable in the final layout." if level == "WARN" else "Raster resolution meets the configured threshold.",
                    "Replace the source image or reduce its display size, then inspect the rendered page." if level == "WARN" else "Retain the source and confirm final-size readability visually.",
                )
            )
        else:
            findings.append(
                finding(
                    "WARN",
                    "images.dimensions_unknown",
                    target,
                    "Effective resolution could not be calculated for the embedded image.",
                    "Inspect the source pixels, embedded format, display size, and final rendered labels manually.",
                )
            )

    table_count = int(document.xpath("count(.//w:tbl)", namespaces=NS))
    field_count = len(field_nodes)
    findings.append(
        finding(
            "INFO",
            "document.structure_summary",
            f"tables={table_count};fields={field_count};bookmarks={len(bookmarks)};images={len(document.xpath('.//w:drawing', namespaces=NS))}",
            "The structural inventory defines the items that require content and visual review.",
            "Use it to reconcile tables, captions, cross-references, and rendered pages.",
        )
    )
    return findings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("document", type=Path)
    parser.add_argument("--anonymous", action="store_true")
    parser.add_argument("--minimum-dpi", type=float, default=300.0)
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    findings = audit(args.document, anonymous=args.anonymous, minimum_dpi=args.minimum_dpi)
    errors = [item for item in findings if item["level"] == "ERROR"]
    payload: dict[str, Any] = {"ok": not errors, "document": str(args.document), "findings": findings}
    if args.as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for item in findings:
            print(f"[{item['level']}] {item['rule']}: {item['evidence']}")
            print(f"  Impact: {item['impact']}")
            print(f"  Action: {item['action']}")
        print(f"DOCX audit {'passed' if not errors else 'failed'}: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
