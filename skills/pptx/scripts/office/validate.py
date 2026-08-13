#!/usr/bin/env python3
"""Validate a packed or unpacked PPTX package."""

from __future__ import annotations

import argparse
import sys
import tempfile
import zipfile
from pathlib import Path

try:
    from .package_io import safe_extract_pptx
    from .validators import PPTXSchemaValidator
except ImportError:  # Direct CLI execution from this directory.
    from package_io import safe_extract_pptx
    from validators import PPTXSchemaValidator


def validate(path: Path, original: Path | None = None, *, repair: bool = False, verbose: bool = False) -> bool:
    if original is not None and (not original.is_file() or original.suffix.lower() != ".pptx"):
        raise ValueError("--original must be an existing .pptx file")
    if path.is_file():
        if path.suffix.lower() != ".pptx":
            raise ValueError("packed input must be a .pptx file")
        with tempfile.TemporaryDirectory(prefix="pptx-validate-") as directory:
            unpacked = Path(directory)
            safe_extract_pptx(path, unpacked)
            return validate(unpacked, original, repair=repair, verbose=verbose)
    if not path.is_dir():
        raise ValueError("input must be a .pptx file or an unpacked directory")
    validator = PPTXSchemaValidator(path, original, verbose=verbose)
    if repair:
        repairs = validator.repair()
        if repairs:
            print(f"Auto-repaired {repairs} issue(s)")
    return validator.validate()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--original", type=Path)
    parser.add_argument("--auto-repair", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    try:
        success = validate(
            args.path,
            args.original,
            repair=args.auto_repair,
            verbose=args.verbose,
        )
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    if success:
        print("All validations PASSED!")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
