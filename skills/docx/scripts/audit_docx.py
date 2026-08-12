#!/usr/bin/env python3
"""Audit DOCX structure, references, images, revisions, and delivery requirements."""

from __future__ import annotations

import argparse
import io
import json
import posixpath
import re
import struct
import sys
import zipfile
from pathlib import Path
from collections.abc import Callable
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
ACTIVE_TEXT_PART = re.compile(
    r"^word/(?:document|header\d+|footer\d+|footnotes|endnotes)\.xml$"
)


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


def normalized_text(node: etree._Element) -> str:
    """Return final-visible Word text with insignificant whitespace collapsed."""
    return re.sub(
        r"\s+",
        " ",
        "".join(node.xpath(".//w:t/text()", namespaces=NS)),
    ).strip()


def color_token(
    node: etree._Element,
    *,
    value_attribute: str,
    theme_attribute: str,
) -> str:
    theme = node.get(W + theme_attribute)
    if theme:
        return f"THEME:{theme.upper()}"
    value = node.get(W + value_attribute, "AUTO")
    return value.removeprefix("#").upper()


def normalize_allowed_color(value: str) -> str:
    value = value.strip().removeprefix("#").upper()
    if value.startswith("THEME:"):
        return value
    return value


def style_state(
    parts: dict[str, bytes],
) -> tuple[
    etree._Element | None,
    dict[str, etree._Element],
    dict[str, str],
]:
    root = parse_xml(parts, "word/styles.xml")
    styles: dict[str, etree._Element] = {}
    defaults: dict[str, str] = {}
    if root is None:
        return None, styles, defaults
    for node in root.xpath("./w:style", namespaces=NS):
        style_id = node.get(W + "styleId")
        style_type = node.get(W + "type")
        if not style_id:
            continue
        styles[style_id] = node
        if style_type and node.get(W + "default") in {"1", "true", "on"}:
            defaults[style_type] = style_id
    return root, styles, defaults


def inherited_style_property(
    styles: dict[str, etree._Element],
    style_id: str | None,
    xpath: str,
) -> etree._Element | None:
    seen: set[str] = set()
    current = style_id
    while current and current not in seen:
        seen.add(current)
        style = styles.get(current)
        if style is None:
            return None
        values = style.xpath(xpath, namespaces=NS)
        if values:
            return values[0]
        based_on = style.xpath("./w:basedOn/@w:val", namespaces=NS)
        current = based_on[0] if based_on else None
    return None


def paragraph_style_id(
    paragraph: etree._Element,
    defaults: dict[str, str],
) -> str | None:
    values = paragraph.xpath("./w:pPr/w:pStyle/@w:val", namespaces=NS)
    return values[0] if values else defaults.get("paragraph")


def effective_run_color(
    run: etree._Element,
    styles_root: etree._Element | None,
    styles: dict[str, etree._Element],
    defaults: dict[str, str],
) -> str:
    direct = run.xpath("./w:rPr/w:color", namespaces=NS)
    if direct:
        return color_token(
            direct[0], value_attribute="val", theme_attribute="themeColor"
        )

    run_style = run.xpath("./w:rPr/w:rStyle/@w:val", namespaces=NS)
    styled = inherited_style_property(
        styles,
        run_style[0] if run_style else None,
        "./w:rPr/w:color",
    )
    if styled is not None:
        return color_token(
            styled, value_attribute="val", theme_attribute="themeColor"
        )

    paragraph = next(iter(run.iterancestors(W + "p")), None)
    if paragraph is not None:
        paragraph_run = paragraph.xpath("./w:pPr/w:rPr/w:color", namespaces=NS)
        if paragraph_run:
            return color_token(
                paragraph_run[0],
                value_attribute="val",
                theme_attribute="themeColor",
            )
        styled = inherited_style_property(
            styles,
            paragraph_style_id(paragraph, defaults),
            "./w:rPr/w:color",
        )
        if styled is not None:
            return color_token(
                styled, value_attribute="val", theme_attribute="themeColor"
            )

    if styles_root is not None:
        doc_default = styles_root.xpath(
            "./w:docDefaults/w:rPrDefault/w:rPr/w:color", namespaces=NS
        )
        if doc_default:
            return color_token(
                doc_default[0],
                value_attribute="val",
                theme_attribute="themeColor",
            )
    return "000000"


def effective_paragraph_alignment(
    paragraph: etree._Element,
    styles_root: etree._Element | None,
    styles: dict[str, etree._Element],
    defaults: dict[str, str],
) -> str:
    direct = paragraph.xpath("./w:pPr/w:jc/@w:val", namespaces=NS)
    if direct:
        return direct[0].lower()
    styled = inherited_style_property(
        styles,
        paragraph_style_id(paragraph, defaults),
        "./w:pPr/w:jc",
    )
    if styled is not None:
        return styled.get(W + "val", "left").lower()
    if styles_root is not None:
        doc_default = styles_root.xpath(
            "./w:docDefaults/w:pPrDefault/w:pPr/w:jc/@w:val", namespaces=NS
        )
        if doc_default:
            return doc_default[0].lower()
    return "left"


def active_text_roots(parts: dict[str, bytes]) -> dict[str, etree._Element]:
    roots: dict[str, etree._Element] = {}
    for name in parts:
        if ACTIVE_TEXT_PART.match(name):
            root = parse_xml(parts, name)
            if root is not None:
                roots[name] = root
    return roots


def used_style_nodes(
    roots: dict[str, etree._Element],
    styles: dict[str, etree._Element],
    defaults: dict[str, str],
) -> dict[str, etree._Element]:
    style_ids = set(defaults.values())
    for root in roots.values():
        style_ids.update(
            root.xpath(
                ".//w:pStyle/@w:val | .//w:rStyle/@w:val | .//w:tblStyle/@w:val",
                namespaces=NS,
            )
        )
    return {style_id: styles[style_id] for style_id in style_ids if style_id in styles}


def requirements_error(rule: str, evidence: str, action: str) -> dict[str, str]:
    return finding(
        "ERROR",
        rule,
        evidence,
        "The generated Word file does not match the confirmed delivery requirements.",
        action,
    )


def audit_delivery_requirements(
    parts: dict[str, bytes],
    document: etree._Element,
    requirements: dict[str, Any],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if not isinstance(requirements, dict) or requirements.get("schema_version") != 1:
        return [
            requirements_error(
                "requirements.schema",
                "schema_version must equal 1",
                "Correct the UTF-8 JSON requirements file before auditing the document.",
            )
        ]

    roots = active_text_roots(parts)
    styles_root, styles, defaults = style_state(parts)
    used_styles = used_style_nodes(roots, styles, defaults)

    def allowed_colors(key: str) -> set[str] | None:
        raw = requirements.get(key)
        if raw is None:
            return None
        if not isinstance(raw, list) or not raw or not all(
            isinstance(item, str) and item.strip() for item in raw
        ):
            findings.append(
                requirements_error(
                    "requirements.schema",
                    f"{key} must be a non-empty string list",
                    "Correct the color requirement before auditing the document.",
                )
            )
            return None
        return {normalize_allowed_color(item) for item in raw}

    text_colors = allowed_colors("allowed_text_colors")
    fill_colors = allowed_colors("allowed_fill_colors")
    border_colors = allowed_colors("allowed_border_colors")

    if text_colors is not None:
        seen: set[tuple[str, int | None, str]] = set()
        for part_name, root in roots.items():
            for run in root.xpath(".//w:r[.//w:t]", namespaces=NS):
                token = effective_run_color(run, styles_root, styles, defaults)
                key = (part_name, run.sourceline, token)
                if token not in text_colors and key not in seen:
                    seen.add(key)
                    findings.append(
                        requirements_error(
                            "requirements.text_color",
                            f"{location(part_name, run)}:{token}",
                            "Apply an allowed text color to the visible run or its effective style.",
                        )
                    )
        for style_id, style in used_styles.items():
            for node in style.xpath(".//w:rPr/w:color", namespaces=NS):
                token = color_token(
                    node, value_attribute="val", theme_attribute="themeColor"
                )
                if token not in text_colors:
                    findings.append(
                        requirements_error(
                            "requirements.text_color",
                            f"word/styles.xml:{style_id}:{token}",
                            "Remove the unapproved color from the active style or authorize it explicitly.",
                        )
                    )

    def audit_color_nodes(
        allowed: set[str] | None,
        rule: str,
        xpath: str,
        *,
        value_attribute: str,
        theme_attribute: str,
        active_predicate: Callable[[etree._Element], bool] | None = None,
    ) -> None:
        if allowed is None:
            return
        nodes: list[tuple[str, etree._Element]] = []
        for part_name, root in roots.items():
            nodes.extend((part_name, node) for node in root.xpath(xpath, namespaces=NS))
        for style_id, style in used_styles.items():
            nodes.extend(
                (f"word/styles.xml:{style_id}", node)
                for node in style.xpath(xpath, namespaces=NS)
            )
        for part_name, node in nodes:
            if active_predicate is not None and not active_predicate(node):
                continue
            token = color_token(
                node,
                value_attribute=value_attribute,
                theme_attribute=theme_attribute,
            )
            if token not in allowed:
                findings.append(
                    requirements_error(
                        rule,
                        f"{location(part_name, node)}:{token}",
                        "Apply an allowed color or update the confirmed requirements explicitly.",
                    )
                )

    audit_color_nodes(
        fill_colors,
        "requirements.fill_color",
        ".//w:shd",
        value_attribute="fill",
        theme_attribute="themeFill",
        active_predicate=lambda node: node.get(W + "val", "clear")
        not in {"nil", "none"},
    )
    audit_color_nodes(
        border_colors,
        "requirements.border_color",
        ".//w:tblBorders/* | .//w:tcBorders/* | .//w:pBdr/*",
        value_attribute="color",
        theme_attribute="themeColor",
        active_predicate=lambda node: node.get(W + "val", "single")
        not in {"nil", "none"},
    )

    all_visible_text = "\n".join(normalized_text(root) for root in roots.values())
    for key, should_exist in (("forbidden_text", False), ("required_text", True)):
        values = requirements.get(key, [])
        if not isinstance(values, list) or not all(
            isinstance(item, str) and item for item in values
        ):
            findings.append(
                requirements_error(
                    "requirements.schema",
                    f"{key} must be a string list",
                    "Correct the text requirement before auditing the document.",
                )
            )
            continue
        for value in values:
            present = value in all_visible_text
            if present != should_exist:
                rule = "requirements.required_text" if should_exist else "requirements.forbidden_text"
                action = (
                    "Restore the confirmed required text."
                    if should_exist
                    else "Remove the task-specific prohibited text without deleting scientific limitations or required disclosures."
                )
                findings.append(requirements_error(rule, value[:80], action))

    body = document.find(W + "body")
    blocks: list[dict[str, Any]] = []
    table_index = 0
    if body is not None:
        for node in body:
            if node.tag == W + "p":
                drawings = node.xpath(".//w:drawing", namespaces=NS)
                blocks.append(
                    {
                        "kind": "paragraph",
                        "node": node,
                        "text": normalized_text(node),
                        "drawings": drawings,
                    }
                )
            elif node.tag == W + "tbl":
                table_index += 1
                blocks.append({"kind": "table", "node": node, "table_index": table_index})

    tables = requirements.get("tables", [])
    if not isinstance(tables, list):
        findings.append(
            requirements_error(
                "requirements.schema",
                "tables must be a list",
                "Correct the table requirements before auditing the document.",
            )
        )
        tables = []
    matched_positions: list[int] = []
    for index, item in enumerate(tables, 1):
        required_fields = ("id", "role", "source", "placement", "caption", "alignment")
        if not isinstance(item, dict) or any(
            not isinstance(item.get(field), str) or not item[field].strip()
            for field in required_fields
        ):
            findings.append(
                requirements_error(
                    "requirements.schema",
                    f"tables[{index - 1}] lacks id/role/source/placement/caption/alignment",
                    "Complete the report table inventory before generating the Word file.",
                )
            )
            continue
        caption = re.sub(r"\s+", " ", item["caption"]).strip()
        matches = [
            position
            for position, block in enumerate(blocks)
            if block["kind"] == "paragraph" and block["text"] == caption
        ]
        if len(matches) != 1:
            findings.append(
                requirements_error(
                    "requirements.caption_match",
                    f"{item['id']}:matches={len(matches)}:{caption[:80]}",
                    "Generate exactly one caption matching the confirmed table inventory.",
                )
            )
            continue
        position = matches[0]
        matched_positions.append(position)
        following = position + 1
        while (
            following < len(blocks)
            and blocks[following]["kind"] == "paragraph"
            and not blocks[following]["text"]
        ):
            following += 1
        if following >= len(blocks) or blocks[following]["kind"] != "table":
            findings.append(
                requirements_error(
                    "requirements.caption_target",
                    f"{item['id']}:{caption[:80]}",
                    "Place the intended table immediately after its caption, allowing only empty paragraphs between them.",
                )
            )
        expected_alignment = item["alignment"].strip().lower()
        alignment_alias = {"both": "justify", "distribute": "justify"}
        actual_alignment = effective_paragraph_alignment(
            blocks[position]["node"], styles_root, styles, defaults
        )
        actual_alignment = alignment_alias.get(actual_alignment, actual_alignment)
        if expected_alignment not in {"left", "center", "right", "justify"}:
            findings.append(
                requirements_error(
                    "requirements.schema",
                    f"{item['id']}:alignment={expected_alignment}",
                    "Use left, center, right, or justify in the table inventory.",
                )
            )
        elif actual_alignment != expected_alignment:
            findings.append(
                requirements_error(
                    "requirements.caption_alignment",
                    f"{item['id']}:expected={expected_alignment};actual={actual_alignment}",
                    "Set the caption's effective paragraph alignment to the confirmed value.",
                )
            )
        references = item.get("references", [])
        if not isinstance(references, list) or not all(
            isinstance(value, str) and value for value in references
        ):
            findings.append(
                requirements_error(
                    "requirements.schema",
                    f"{item['id']}:references must be a string list",
                    "Correct the table-reference inventory before auditing the document.",
                )
            )
        else:
            other_paragraphs = "\n".join(
                block["text"]
                for block_position, block in enumerate(blocks)
                if block["kind"] == "paragraph" and block_position != position
            )
            for reference in references:
                if reference not in other_paragraphs:
                    findings.append(
                        requirements_error(
                            "requirements.table_reference",
                            f"{item['id']}:{reference}",
                            "Add or correct the confirmed body reference to this table.",
                        )
                    )

    if matched_positions != sorted(matched_positions):
        findings.append(
            requirements_error(
                "requirements.caption_order",
                f"positions={matched_positions}",
                "Reorder captions and their tables to match the confirmed table inventory.",
            )
        )
    if requirements.get("require_all_tables_listed") is True and table_index != len(tables):
        findings.append(
            requirements_error(
                "requirements.table_count",
                f"document={table_index};inventory={len(tables)}",
                "List every formal table or remove an unintended layout/data table before delivery.",
            )
        )

    figures = requirements.get("figures", [])
    if not isinstance(figures, list):
        findings.append(
            requirements_error(
                "requirements.schema",
                "figures must be a list",
                "Correct the figure requirements before auditing the document.",
            )
        )
        figures = []
    matched_figure_positions: list[int] = []
    for index, item in enumerate(figures, 1):
        required_fields = ("id", "role", "source", "placement", "caption", "alignment")
        if not isinstance(item, dict) or any(
            not isinstance(item.get(field), str) or not item[field].strip()
            for field in required_fields
        ):
            findings.append(
                requirements_error(
                    "requirements.schema",
                    f"figures[{index - 1}] lacks id/role/source/placement/caption/alignment",
                    "Complete the report figure inventory before generating the Word file.",
                )
            )
            continue
        caption = re.sub(r"\s+", " ", item["caption"]).strip()
        matches = [
            position
            for position, block in enumerate(blocks)
            if block["kind"] == "paragraph" and block["text"] == caption
        ]
        if len(matches) != 1:
            findings.append(
                requirements_error(
                    "requirements.figure_caption_match",
                    f"{item['id']}:matches={len(matches)}:{caption[:80]}",
                    "Generate exactly one caption matching the confirmed figure inventory.",
                )
            )
            continue
        position = matches[0]
        matched_figure_positions.append(position)
        preceding = position - 1
        while (
            preceding >= 0
            and blocks[preceding]["kind"] == "paragraph"
            and not blocks[preceding]["text"]
            and not blocks[preceding].get("drawings")
        ):
            preceding -= 1
        figure_drawings = (
            blocks[preceding].get("drawings", [])
            if preceding >= 0 and blocks[preceding]["kind"] == "paragraph"
            else []
        )
        if len(figure_drawings) != 1:
            findings.append(
                requirements_error(
                    "requirements.figure_caption_target",
                    f"{item['id']}:{caption[:80]}:drawings={len(figure_drawings)}",
                    "Place exactly one intended figure in the preceding non-empty paragraph.",
                )
            )
        expected_alignment = item["alignment"].strip().lower()
        alignment_alias = {"both": "justify", "distribute": "justify"}
        actual_alignment = effective_paragraph_alignment(
            blocks[position]["node"], styles_root, styles, defaults
        )
        actual_alignment = alignment_alias.get(actual_alignment, actual_alignment)
        if expected_alignment not in {"left", "center", "right", "justify"}:
            findings.append(
                requirements_error(
                    "requirements.schema",
                    f"{item['id']}:alignment={expected_alignment}",
                    "Use left, center, right, or justify in the figure inventory.",
                )
            )
        elif actual_alignment != expected_alignment:
            findings.append(
                requirements_error(
                    "requirements.figure_caption_alignment",
                    f"{item['id']}:expected={expected_alignment};actual={actual_alignment}",
                    "Set the figure caption's effective paragraph alignment to the confirmed value.",
                )
            )
        references = item.get("references", [])
        if not isinstance(references, list) or not all(
            isinstance(value, str) and value for value in references
        ):
            findings.append(
                requirements_error(
                    "requirements.schema",
                    f"{item['id']}:references must be a string list",
                    "Correct the figure-reference inventory before auditing the document.",
                )
            )
        else:
            other_paragraphs = "\n".join(
                block["text"]
                for block_position, block in enumerate(blocks)
                if block["kind"] == "paragraph" and block_position != position
            )
            for reference in references:
                if reference not in other_paragraphs:
                    findings.append(
                        requirements_error(
                            "requirements.figure_reference",
                            f"{item['id']}:{reference}",
                            "Add or correct the confirmed body reference to this figure.",
                        )
                    )
        alt_text = item.get("alt_text")
        if alt_text is not None:
            if not isinstance(alt_text, str) or not alt_text.strip():
                findings.append(
                    requirements_error(
                        "requirements.schema",
                        f"{item['id']}:alt_text must be a non-empty string",
                        "Correct or remove the optional figure alt-text requirement.",
                    )
                )
            elif len(figure_drawings) == 1:
                descriptions = figure_drawings[0].xpath(
                    ".//wp:docPr/@descr | .//wp:docPr/@title", namespaces=NS
                )
                if alt_text.strip() not in {value.strip() for value in descriptions if value.strip()}:
                    findings.append(
                        requirements_error(
                            "requirements.figure_alt_text",
                            f"{item['id']}:{alt_text[:80]}",
                            "Set the embedded figure's title or description to the confirmed alt text.",
                        )
                    )

    if matched_figure_positions != sorted(matched_figure_positions):
        findings.append(
            requirements_error(
                "requirements.figure_caption_order",
                f"positions={matched_figure_positions}",
                "Reorder figures and captions to match the confirmed figure inventory.",
            )
        )
    drawing_count = sum(
        len(block.get("drawings", []))
        for block in blocks
        if block["kind"] == "paragraph"
    )
    if requirements.get("require_all_figures_listed") is True and drawing_count != len(figures):
        findings.append(
            requirements_error(
                "requirements.figure_count",
                f"document={drawing_count};inventory={len(figures)}",
                "List every formal embedded figure or remove an unintended drawing before delivery.",
            )
        )

    findings.append(
        finding(
            "INFO",
            "requirements.summary",
            f"tables={len(tables)};figures={len(figures)};visible_parts={len(roots)}",
            "The task-specific Word requirements were applied to the generated file.",
            "Reconcile these static checks with the report content review and page rendering evidence.",
        )
    )
    return findings


def audit(
    path: Path,
    *,
    anonymous: bool = False,
    minimum_dpi: float = 300.0,
    requirements: dict[str, Any] | None = None,
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
    if requirements is not None:
        findings.extend(audit_delivery_requirements(parts, document, requirements))
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
    parser.add_argument(
        "--requirements",
        type=Path,
        help="UTF-8 JSON file with task-specific colors, captions, tables, and text requirements",
    )
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser.parse_args()


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    args = parse_args()
    requirements: dict[str, Any] | None = None
    requirements_findings: list[dict[str, str]] = []
    if args.requirements is not None:
        try:
            loaded = json.loads(args.requirements.read_text(encoding="utf-8"))
            if not isinstance(loaded, dict):
                raise ValueError("requirements root must be an object")
            requirements = loaded
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
            requirements_findings.append(
                requirements_error(
                    "requirements.unreadable",
                    f"{args.requirements}:{type(error).__name__}",
                    "Provide a readable UTF-8 JSON requirements file.",
                )
            )
    findings = requirements_findings + audit(
        args.document,
        anonymous=args.anonymous,
        minimum_dpi=args.minimum_dpi,
        requirements=requirements,
    )
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
