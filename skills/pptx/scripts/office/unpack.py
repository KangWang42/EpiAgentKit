#!/usr/bin/env python3
"""Safely unpack a PPTX package for scoped editing."""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

try:
    from .package_io import safe_extract_pptx
except ImportError:  # Direct CLI execution from this directory.
    from package_io import safe_extract_pptx


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    try:
        if args.output_dir.exists() and any(args.output_dir.iterdir()):
            raise ValueError("output directory must be absent or empty")
        safe_extract_pptx(args.input, args.output_dir)
        xml_count = sum(
            1
            for path in args.output_dir.rglob("*")
            if path.is_file() and path.suffix.lower() in {".xml", ".rels"}
        )
        print(f"Unpacked {args.input} ({xml_count} XML files)")
        return 0
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
