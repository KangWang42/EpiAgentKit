#!/usr/bin/env python3
"""Validate and pack an unpacked PPTX directory without overwriting by default."""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
import zipfile
from pathlib import Path

try:
    from .package_io import pack_pptx
    from .validate import validate
    from .validators import PPTXSchemaValidator
except ImportError:  # Direct CLI execution from this directory.
    from package_io import pack_pptx
    from validate import validate
    from validators import PPTXSchemaValidator


def pack_verified(
    input_directory: Path,
    output: Path,
    original: Path | None = None,
    *,
    replace: bool = False,
) -> int:
    if not input_directory.is_dir():
        raise ValueError("input directory does not exist")
    if output.suffix.lower() != ".pptx":
        raise ValueError("output must use the .pptx extension")
    if output.exists() and not replace:
        raise FileExistsError("output already exists; use --replace after confirmation")
    repairs = PPTXSchemaValidator(input_directory, original).repair()
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, candidate_name = tempfile.mkstemp(
        prefix=f".{output.stem}.", suffix=".candidate.pptx", dir=output.parent
    )
    os.close(descriptor)
    candidate = Path(candidate_name)
    candidate.unlink()
    try:
        pack_pptx(input_directory, candidate)
        if not validate(candidate, original):
            raise ValueError("packed candidate failed validation")
        os.replace(candidate, output)
        return repairs
    finally:
        candidate.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_directory", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--original", type=Path)
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    try:
        repairs = pack_verified(
            args.input_directory,
            args.output,
            args.original,
            replace=args.replace,
        )
        if repairs:
            print(f"Auto-repaired {repairs} whitespace issue(s)")
        print(f"Successfully packed {args.input_directory} to {args.output}")
        return 0
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
