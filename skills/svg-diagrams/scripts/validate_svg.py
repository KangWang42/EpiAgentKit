#!/usr/bin/env python3
"""Validate structural and portability properties of an SVG diagram."""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


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
    parser.add_argument("--expected-ratio", type=float)
    parser.add_argument("--ratio-tolerance", type=float, default=0.03)
    parser.add_argument("--require-text", action="append", default=[])
    parser.add_argument("--forbid-text", action="append", default=[])
    parser.add_argument("--max-circles", type=int)
    return parser.parse_args()


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
