#!/usr/bin/env python3
"""Validate structure, editorial styling, and portability of an SVG diagram."""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path


PALETTE = {
    "biology": {"fill": "#EAF2FB", "stroke": "#BBD6F0", "title": "#2E5C8A"},
    "exposure": {"fill": "#FDF6E3", "stroke": "#F0DA9E", "title": "#9C7A1E"},
    "covariate": {"fill": "#F2F2F2", "stroke": "#D0D0D0", "title": "#444444"},
    "risk": {"fill": "#FBEAEA", "stroke": "#F0B8B8", "title": "#B0413E"},
    "outcome": {"fill": "#E9F6F0", "stroke": "#B7E0CB", "title": "#2F7A52"},
    "nonlinear": {"fill": "#FDF0E4", "stroke": "#F3C99A", "title": "#B8641A"},
}
JOURNAL_FLOW = {
    "canvas": "#FFFFFF",
    "main_fill": "#EAF2FB",
    "main_stroke": "#2E5C8A",
    "exclusion_fill": "#F2F2F2",
    "exclusion_stroke": "#8A8A8A",
    "text": "#444444",
    "connector": "#909090",
}
PAPER_EDITORIAL_COLORS = {
    "#FFFFFF",
    "#F2F2F2",
    "#EAF2FB",
    "#D0D0D0",
    "#8A8A8A",
    "#BBD6F0",
    "#2E5C8A",
    "#909090",
    "#444444",
}
PAPER_NODE_FILLS = {"#FFFFFF", "#F2F2F2", "#EAF2FB"}
PAPER_NODE_STROKES = {"#D0D0D0", "#8A8A8A", "#BBD6F0", "#2E5C8A"}
PAPER_TITLE_COLORS = {"#444444", "#2E5C8A"}
NEUTRALS = {"#FFFFFF", "#FDFDFB", "#8A8A8A", "#909090", "#444444"}
ALLOWED_COLORS = NEUTRALS | {
    color for category in PALETTE.values() for color in category.values()
}
COLOR_RE = re.compile(r"#[0-9A-Fa-f]{3,8}\b")
NUMBER_RE = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?")
PATH_TOKEN_RE = re.compile(r"[A-Za-z]|[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?")


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_viewbox(root: ET.Element) -> tuple[float, float, float, float]:
    raw = root.get("viewBox")
    if not raw:
        raise ValueError("root <svg> must define viewBox")
    values = [float(value) for value in re.split(r"[\s,]+", raw.strip())]
    if len(values) != 4 or values[2] <= 0 or values[3] <= 0:
        raise ValueError(f"invalid viewBox: {raw!r}")
    return values[0], values[1], values[2], values[3]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("svg", type=Path)
    parser.add_argument("--profile", choices=("editorial", "journal-flow"))
    parser.add_argument("--purpose", choices=("ppt", "paper", "report"))
    parser.add_argument("--expected-ratio", type=float)
    parser.add_argument("--ratio-tolerance", type=float, default=0.03)
    parser.add_argument("--require-text", action="append", default=[])
    parser.add_argument("--forbid-text", action="append", default=[])
    parser.add_argument("--max-circles", type=int)
    parser.add_argument("--min-font-size", type=float)
    parser.add_argument("--max-semantic-categories", type=int)
    parser.add_argument("--allow-gradient", action="store_true")
    parser.add_argument("--allow-filter", action="store_true")
    parser.add_argument("--allow-image", action="store_true")
    parser.add_argument("--allow-diagonal-connectors", action="store_true")
    return parser.parse_args()


def style_map(element: ET.Element) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in (element.get("style") or "").split(";"):
        if ":" not in item:
            continue
        key, value = item.split(":", 1)
        result[key.strip()] = value.strip()
    return result


def prop(element: ET.Element, name: str) -> str | None:
    return element.get(name) or style_map(element).get(name)


def number(value: str | None) -> float | None:
    if value is None:
        return None
    match = NUMBER_RE.search(value)
    return float(match.group()) if match else None


def color(value: str | None) -> str | None:
    if value is None:
        return None
    match = COLOR_RE.fullmatch(value.strip())
    if not match or len(match.group()) != 7:
        return None
    return match.group().upper()


def element_label(element: ET.Element) -> str:
    identifier = element.get("id")
    role = element.get("data-role")
    suffix = identifier or role or "unnamed"
    return f"<{local_name(element.tag)}> {suffix}"


def point_pairs(raw: str) -> list[tuple[float, float]] | None:
    values = [float(value) for value in NUMBER_RE.findall(raw)]
    if len(values) < 4 or len(values) % 2:
        return None
    return list(zip(values[0::2], values[1::2]))


def orthogonal_points(points: list[tuple[float, float]]) -> bool:
    return all(
        abs(x1 - x2) < 1e-9 or abs(y1 - y2) < 1e-9
        for (x1, y1), (x2, y2) in zip(points, points[1:])
    )


def orthogonal_path(raw: str) -> bool:
    tokens = PATH_TOKEN_RE.findall(raw)
    if not tokens:
        return False
    index = 0
    command = ""
    current: tuple[float, float] | None = None
    start: tuple[float, float] | None = None
    while index < len(tokens):
        token = tokens[index]
        if token.isalpha():
            command = token
            index += 1
            if command not in {"M", "L", "H", "V"}:
                return False
        if not command:
            return False
        try:
            if command in {"M", "L"}:
                x = float(tokens[index])
                y = float(tokens[index + 1])
                index += 2
                point = (x, y)
                if command == "M":
                    current = point
                    start = point
                    command = "L"
                else:
                    if current is None or not orthogonal_points([current, point]):
                        return False
                    current = point
            elif command == "H":
                x = float(tokens[index])
                index += 1
                if current is None:
                    return False
                current = (x, current[1])
            elif command == "V":
                y = float(tokens[index])
                index += 1
                if current is None:
                    return False
                current = (current[0], y)
        except (IndexError, ValueError):
            return False
    return current is not None and start is not None


def connector_is_orthogonal(element: ET.Element) -> bool:
    name = local_name(element.tag)
    if name == "line":
        x1, y1 = number(element.get("x1")), number(element.get("y1"))
        x2, y2 = number(element.get("x2")), number(element.get("y2"))
        return None not in {x1, y1, x2, y2} and (
            abs(x1 - x2) < 1e-9 or abs(y1 - y2) < 1e-9
        )
    if name in {"polyline", "polygon"}:
        points = point_pairs(element.get("points") or "")
        return bool(points and orthogonal_points(points))
    if name == "path":
        return orthogonal_path(element.get("d") or "")
    return False


def validate_editorial(
    root: ET.Element,
    purpose: str | None,
    min_font_size: float | None,
    max_categories: int | None,
    allow_gradient: bool,
    allow_filter: bool,
    allow_image: bool,
    allow_diagonal: bool,
) -> list[str]:
    problems: list[str] = []
    categories: set[str] = set()
    layer_cards: dict[str, list[tuple[float, float, str]]] = defaultdict(list)
    node_titles: dict[str, float] = {}
    semantic_nodes = 0
    canvases = 0
    inherited_font = prop(root, "font-family") or ""

    for element in root.iter():
        name = local_name(element.tag)
        role = element.get("data-role")
        category = element.get("data-category")
        label = element_label(element)

        if name in {"linearGradient", "radialGradient"} and not allow_gradient:
            problems.append(f"gradient is not allowed in editorial profile: {label}")
        if name == "filter" and not allow_filter:
            problems.append(f"filter is not allowed in editorial profile: {label}")
        if name == "image" and not allow_image:
            problems.append(f"embedded image is not allowed in editorial profile: {label}")
        if name == "style":
            problems.append("<style> is not allowed; use inline semantic attributes")
        if prop(element, "filter") and not allow_filter:
            problems.append(f"filter attribute is not allowed: {label}")

        for attribute in ("fill", "stroke", "color", "stop-color"):
            raw = prop(element, attribute)
            if not raw:
                continue
            matches = COLOR_RE.findall(raw)
            for match in matches:
                normalized = match.upper()
                if len(normalized) != 7 or normalized not in ALLOWED_COLORS:
                    problems.append(f"color outside editorial palette on {label}: {match}")
                if purpose == "paper" and normalized not in PAPER_EDITORIAL_COLORS:
                    problems.append(
                        f"paper editorial allows only white/gray and one blue hue on {label}: {match}"
                    )
            if re.search(r"\b(?:rgb|rgba|hsl|hsla)\s*\(", raw, re.I):
                problems.append(f"non-hex color is not allowed on {label}: {raw}")

        if category:
            if category not in PALETTE:
                problems.append(f"unknown data-category on {label}: {category}")
            else:
                categories.add(category)

        if role == "canvas":
            canvases += 1
            expected = {"#FFFFFF"} if purpose == "paper" else {"#FFFFFF", "#FDFDFB"}
            actual = color(prop(element, "fill"))
            if actual not in expected:
                problems.append(f"canvas fill must be one of {sorted(expected)}: {label}")

        if role in {"card", "nested-layer"}:
            semantic_nodes += 1
            if category not in PALETTE:
                problems.append(f"semantic node lacks valid data-category: {label}")
                continue
            actual_fill = color(prop(element, "fill"))
            actual_stroke = color(prop(element, "stroke"))
            if purpose == "paper":
                if actual_fill not in PAPER_NODE_FILLS:
                    problems.append(f"paper node fill must be white, gray, or pale blue on {label}")
                if actual_stroke not in PAPER_NODE_STROKES:
                    problems.append(f"paper node stroke must be neutral or blue on {label}")
            else:
                expected = PALETTE[category]
                if actual_fill != expected["fill"]:
                    problems.append(f"category fill mismatch on {label}")
                if actual_stroke != expected["stroke"]:
                    problems.append(f"category stroke mismatch on {label}")
            stroke_width = number(prop(element, "stroke-width"))
            if stroke_width is None or not 0.8 <= stroke_width <= 1.5:
                problems.append(f"card border must be 0.8 to 1.5 px on {label}")
            width = number(element.get("width"))
            height = number(element.get("height"))
            radius = number(element.get("rx"))
            if None in {width, height}:
                problems.append(f"semantic node needs numeric width and height: {label}")
            elif radius is None or radius < 0 or radius > (4 if purpose == "paper" else 10):
                problems.append(f"semantic node radius is missing or excessive: {label}")
            if role == "card":
                layer = element.get("data-layer")
                if not layer:
                    problems.append(f"card lacks data-layer: {label}")
                elif width is not None and height is not None:
                    layer_cards[layer].append((width, height, label))

        if role == "node-title":
            if category not in PALETTE:
                problems.append(f"node title lacks valid data-category: {label}")
            else:
                actual_title = color(prop(element, "fill"))
                if purpose == "paper" and actual_title not in PAPER_TITLE_COLORS:
                    problems.append(f"paper title must be neutral or blue on {label}")
                elif purpose != "paper" and actual_title != PALETTE[category]["title"]:
                    problems.append(f"title color mismatch on {label}")
            weight = number(prop(element, "font-weight"))
            if weight is None or not 550 <= weight <= 700:
                problems.append(f"node title weight must be 550 to 700 on {label}")
            size = number(prop(element, "font-size"))
            if size is None:
                problems.append(f"node title lacks numeric font-size: {label}")
            node_id = element.get("data-node")
            if node_id and size is not None:
                node_titles[node_id] = size
            if not "".join(element.itertext()).strip():
                problems.append(f"node title is empty: {label}")

        if role == "node-subtitle":
            if color(prop(element, "fill")) != "#8A8A8A":
                problems.append(f"subtitle color must be #8A8A8A on {label}")
            weight = number(prop(element, "font-weight"))
            if weight is not None and not 350 <= weight <= 450:
                problems.append(f"subtitle weight must be regular on {label}")
            size = number(prop(element, "font-size"))
            node_id = element.get("data-node")
            if node_id and size is not None and node_id in node_titles:
                if size >= node_titles[node_id]:
                    problems.append(f"subtitle must be smaller than title on {label}")

        if name == "text":
            size = number(prop(element, "font-size"))
            if min_font_size is not None and (size is None or size < min_font_size):
                problems.append(f"font size below {min_font_size:g} on {label}")
            family = prop(element, "font-family") or inherited_font
            if "sans-serif" not in family.lower():
                problems.append(f"text does not declare a sans-serif fallback: {label}")

        if role in {"connector", "axis", "axis-tick"}:
            if color(prop(element, "stroke")) != "#909090":
                problems.append(f"connector stroke must be #909090 on {label}")
            stroke_width = number(prop(element, "stroke-width"))
            if stroke_width is None or not 1.5 <= stroke_width <= 2.0:
                problems.append(f"connector width must be 1.5 to 2 px on {label}")
            if not allow_diagonal and not connector_is_orthogonal(element):
                problems.append(f"connector is not orthogonal: {label}")
            arrow_default = role in {"connector", "axis"}
            has_arrow = element.get("data-arrow", str(arrow_default).lower()).lower() == "true"
            if has_arrow and not element.get("marker-end"):
                problems.append(f"arrow connector lacks marker-end: {label}")

        if purpose == "paper" and role == "decoration":
            problems.append(f"paper figure cannot contain decoration: {label}")

    if canvases != 1:
        problems.append(f"editorial profile requires exactly one data-role='canvas'; found {canvases}")
    if semantic_nodes == 0:
        problems.append("editorial profile requires at least one semantic card or nested layer")
    if max_categories is not None and len(categories) > max_categories:
        problems.append(
            f"semantic category count {len(categories)} exceeds maximum {max_categories}"
        )

    for layer, cards in layer_cards.items():
        widths = {round(width, 6) for width, _, _ in cards}
        heights = {round(height, 6) for _, height, _ in cards}
        if len(widths) > 1 or len(heights) > 1:
            labels = ", ".join(label for _, _, label in cards)
            problems.append(f"cards in data-layer={layer!r} are not equal-sized: {labels}")

    return problems


def validate_journal_flow(
    root: ET.Element,
    purpose: str | None,
    min_font_size: float | None,
    allow_diagonal: bool,
) -> list[str]:
    """Validate restrained journal-style cohort and participant flow diagrams."""
    problems: list[str] = []
    canvases = 0
    flow_nodes = 0
    main_centers: list[tuple[float, str]] = []
    layer_nodes: dict[tuple[str, str], list[tuple[float, float, str]]] = defaultdict(list)
    inherited_font = prop(root, "font-family") or ""
    allowed = set(JOURNAL_FLOW.values())

    for element in root.iter():
        name = local_name(element.tag)
        role = element.get("data-role")
        label = element_label(element)

        if name in {"linearGradient", "radialGradient"}:
            problems.append(f"gradient is not allowed in journal-flow profile: {label}")
        if name == "filter" or prop(element, "filter"):
            problems.append(f"filter is not allowed in journal-flow profile: {label}")
        if name == "image":
            problems.append(f"embedded image is not allowed in journal-flow profile: {label}")
        if name == "style":
            problems.append("<style> is not allowed; use inline semantic attributes")

        for attribute in ("fill", "stroke", "color", "stop-color"):
            raw = prop(element, attribute)
            if not raw or raw.lower() in {"none", "currentcolor"}:
                continue
            if re.search(r"\b(?:rgb|rgba|hsl|hsla)\s*\(", raw, re.I):
                problems.append(f"non-hex color is not allowed on {label}: {raw}")
            for match in COLOR_RE.findall(raw):
                normalized = match.upper()
                if len(normalized) != 7 or normalized not in allowed:
                    problems.append(f"color outside journal-flow palette on {label}: {match}")

        if role == "canvas":
            canvases += 1
            if color(prop(element, "fill")) != JOURNAL_FLOW["canvas"]:
                problems.append(f"journal-flow canvas must be #FFFFFF: {label}")

        if role in {"flow-main", "flow-exclusion", "flow-terminal"}:
            flow_nodes += 1
            if name != "rect":
                problems.append(f"flow node must be a <rect>: {label}")
                continue
            width = number(element.get("width"))
            height = number(element.get("height"))
            x = number(element.get("x"))
            radius = number(element.get("rx")) or 0.0
            stroke_width = number(prop(element, "stroke-width"))
            if None in {width, height, x}:
                problems.append(f"flow node needs numeric x, width, and height: {label}")
                continue
            if not 0 <= radius <= 2:
                problems.append(f"flow node radius must be 0 to 2 px on {label}")
            if stroke_width is None or not 1.0 <= stroke_width <= 1.5:
                problems.append(f"flow node border must be 1 to 1.5 px on {label}")

            if role == "flow-exclusion":
                expected_fill = JOURNAL_FLOW["exclusion_fill"]
                expected_stroke = JOURNAL_FLOW["exclusion_stroke"]
            else:
                expected_fill = JOURNAL_FLOW["main_fill"]
                expected_stroke = JOURNAL_FLOW["main_stroke"]
            if color(prop(element, "fill")) != expected_fill:
                problems.append(f"flow node fill mismatch on {label}")
            if color(prop(element, "stroke")) != expected_stroke:
                problems.append(f"flow node stroke mismatch on {label}")

            layer = element.get("data-layer")
            if not layer:
                problems.append(f"flow node lacks data-layer: {label}")
            else:
                layer_nodes[(role, layer)].append((width, height, label))
            if role == "flow-main":
                main_centers.append((x + width / 2, label))

        if name == "text":
            if color(prop(element, "fill")) != JOURNAL_FLOW["text"]:
                problems.append(f"journal-flow text must use #444444: {label}")
            size = number(prop(element, "font-size"))
            if min_font_size is not None and (size is None or size < min_font_size):
                problems.append(f"font size below {min_font_size:g} on {label}")
            weight = number(prop(element, "font-weight"))
            if weight is not None and not 400 <= weight <= 550:
                problems.append(f"journal-flow text weight must be 400 to 550 on {label}")
            family = prop(element, "font-family") or inherited_font
            if "sans-serif" not in family.lower():
                problems.append(f"text does not declare a sans-serif fallback: {label}")

        if role == "connector":
            if color(prop(element, "stroke")) != JOURNAL_FLOW["connector"]:
                problems.append(f"connector stroke must be #909090 on {label}")
            stroke_width = number(prop(element, "stroke-width"))
            if stroke_width is None or not 1.5 <= stroke_width <= 2.0:
                problems.append(f"connector width must be 1.5 to 2 px on {label}")
            if not allow_diagonal and not connector_is_orthogonal(element):
                problems.append(f"connector is not orthogonal: {label}")
            has_arrow = element.get("data-arrow", "true").lower() == "true"
            if has_arrow and not element.get("marker-end"):
                problems.append(f"arrow connector lacks marker-end: {label}")

        if purpose == "paper" and role == "decoration":
            problems.append(f"paper figure cannot contain decoration: {label}")

    if canvases != 1:
        problems.append(
            f"journal-flow profile requires exactly one data-role='canvas'; found {canvases}"
        )
    if flow_nodes == 0:
        problems.append("journal-flow profile requires at least one flow node")
    if main_centers:
        centers = {round(center, 6) for center, _ in main_centers}
        if len(centers) > 1:
            labels = ", ".join(label for _, label in main_centers)
            problems.append(f"flow-main nodes do not share one vertical centerline: {labels}")

    for (role, layer), nodes in layer_nodes.items():
        widths = {round(width, 6) for width, _, _ in nodes}
        heights = {round(height, 6) for _, height, _ in nodes}
        if len(widths) > 1 or len(heights) > 1:
            labels = ", ".join(label for _, _, label in nodes)
            problems.append(
                f"{role} nodes in data-layer={layer!r} are not equal-sized: {labels}"
            )

    return problems


def main() -> int:
    args = parse_args()
    problems: list[str] = []
    path = args.svg
    if path.suffix.lower() != ".svg":
        problems.append("file extension must be .svg")
    if not path.is_file():
        problems.append(f"file not found: {path}")
        return report(problems)

    try:
        tree = ET.parse(path)
    except ET.ParseError as error:
        return report([f"XML parse failed: {error}"])

    root = tree.getroot()
    if local_name(root.tag) != "svg":
        problems.append("root element must be <svg>")

    try:
        _, _, width, height = parse_viewbox(root)
        ratio = width / height
        if args.expected_ratio is not None:
            delta = abs(ratio - args.expected_ratio) / args.expected_ratio
            if delta > args.ratio_tolerance:
                problems.append(
                    f"aspect ratio {ratio:.6f} differs from expected "
                    f"{args.expected_ratio:.6f} by {delta:.2%}"
                )
    except (TypeError, ValueError) as error:
        problems.append(str(error))
        width = height = ratio = float("nan")

    ids: set[str] = set()
    duplicates: set[str] = set()
    circle_count = 0
    text_chunks: list[str] = []
    for element in root.iter():
        name = local_name(element.tag)
        identifier = element.get("id")
        if identifier:
            if identifier in ids:
                duplicates.add(identifier)
            ids.add(identifier)
        if name == "circle":
            circle_count += 1
        if name == "text":
            text_chunks.append("".join(element.itertext()).strip())
        if name == "foreignObject":
            problems.append("foreignObject is not allowed for Office portability")
        for attr, value in element.attrib.items():
            if local_name(attr) == "href" and re.match(r"https?://", value):
                problems.append(f"external network resource is not allowed: {value}")

    if duplicates:
        problems.append("duplicate ids: " + ", ".join(sorted(duplicates)))
    if args.max_circles is not None and circle_count > args.max_circles:
        problems.append(
            f"circle count {circle_count} exceeds allowed maximum {args.max_circles}"
        )

    all_text = "\n".join(text_chunks)
    for required in args.require_text:
        if required not in all_text:
            problems.append(f"required text missing: {required!r}")
    for forbidden in args.forbid_text:
        if forbidden in all_text:
            problems.append(f"forbidden text present: {forbidden!r}")

    if args.profile == "editorial":
        problems.extend(
            validate_editorial(
                root,
                args.purpose,
                args.min_font_size,
                args.max_semantic_categories,
                args.allow_gradient,
                args.allow_filter,
                args.allow_image,
                args.allow_diagonal_connectors,
            )
        )
    elif args.profile == "journal-flow":
        problems.extend(
            validate_journal_flow(
                root,
                args.purpose,
                args.min_font_size,
                args.allow_diagonal_connectors,
            )
        )

    if problems:
        return report(problems)

    print(
        f"SVG validation passed: {path} | viewBox={width:g}x{height:g} "
        f"| ratio={ratio:.6f} | text={len(text_chunks)} | circles={circle_count}"
    )
    return 0


def report(problems: list[str]) -> int:
    print("SVG validation failed:", file=sys.stderr)
    for problem in problems:
        print(f"- {problem}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
