"""Safe, PPTX-only ZIP package input and output helpers."""

from __future__ import annotations

import os
import shutil
import tempfile
import zipfile
from pathlib import Path, PurePosixPath


def safe_extract_pptx(source: Path, destination: Path) -> None:
    if not source.is_file() or source.suffix.lower() != ".pptx":
        raise ValueError("input must be an existing .pptx file")
    if destination.exists() and not destination.is_dir():
        raise ValueError("destination must be an absent path or an empty directory")
    if destination.exists() and any(destination.iterdir()):
        raise ValueError("destination must be absent or empty")
    root = destination.resolve()
    with zipfile.ZipFile(source) as package:
        members: list[tuple[zipfile.ZipInfo, Path]] = []
        for info in package.infolist():
            member = PurePosixPath(info.filename)
            if member.is_absolute() or ".." in member.parts:
                raise ValueError(f"unsafe package member: {info.filename}")
            target = (destination / Path(*member.parts)).resolve()
            if target != root and root not in target.parents:
                raise ValueError(f"package member escapes destination: {info.filename}")
            members.append((info, target))
        destination.mkdir(parents=True, exist_ok=True)
        for info, target in members:
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with package.open(info) as incoming, target.open("wb") as outgoing:
                shutil.copyfileobj(incoming, outgoing)


def pack_pptx(source_dir: Path, output: Path, *, replace: bool = False) -> None:
    if not source_dir.is_dir():
        raise ValueError("input directory does not exist")
    if output.suffix.lower() != ".pptx":
        raise ValueError("output must use the .pptx extension")
    source_root = source_dir.resolve()
    output_path = output.resolve()
    if source_root in output_path.parents:
        raise ValueError("output must be outside the unpacked input directory")
    if output.exists() and not replace:
        raise FileExistsError("output already exists; use --replace after confirmation")
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output.stem}.", suffix=".pptx.tmp", dir=output.parent
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as package:
            for path in sorted(source_dir.rglob("*")):
                if path.is_symlink():
                    raise ValueError(f"symbolic links are not valid PPTX package parts: {path}")
                if path.is_file():
                    package.write(path, path.relative_to(source_dir).as_posix())
        os.replace(temporary, output)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
