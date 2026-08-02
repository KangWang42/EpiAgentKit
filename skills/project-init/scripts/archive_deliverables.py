#!/usr/bin/env python3
"""Plan or execute recoverable archival of exact formal-project deliverables."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Any


GLOB_CHARS = set("*?[]")
TIMESTAMP_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{4}$")


class ArchiveError(ValueError):
    """Raised when an archive target or operation is unsafe or ambiguous."""


def inside(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


def relative(path: Path, root: Path) -> Path:
    try:
        return path.relative_to(root)
    except ValueError as error:
        raise ArchiveError(f"path is outside the project: {path}") from error


def safe_label(value: str, field: str) -> str:
    cleaned = re.sub(r"[\\/:*?\"<>|\s]+", "_", value.strip()).strip("._")
    if not cleaned or cleaned in {".", ".."}:
        raise ArchiveError(f"{field} must contain a usable label")
    return cleaned


def resolve_project_path(project: Path, raw: str, *, must_exist: bool) -> Path:
    if not raw.strip() or any(char in raw for char in GLOB_CHARS):
        raise ArchiveError(f"targets must be exact paths without globs: {raw!r}")
    candidate = Path(raw)
    target = (candidate if candidate.is_absolute() else project / candidate).resolve(strict=False)
    relative(target, project)
    if must_exist and not target.exists():
        raise ArchiveError(f"target does not exist: {relative(target, project)}")
    return target


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def inventory(target: Path, project: Path) -> list[dict[str, Any]]:
    items = [target] if target.is_file() else sorted(path for path in target.rglob("*") if path.is_file())
    return [
        {
            "path": relative(path, project).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
        for path in items
    ]


def choose_batch(archive: Path, timestamp: str, topic: str, stage: str) -> Path:
    base = archive / f"{timestamp}_{topic}_{stage}"
    candidate = base
    counter = 2
    while candidate.exists():
        candidate = archive / f"{base.name}_{counter:02d}"
        counter += 1
    return candidate


def validate_targets(project: Path, backup: Path, targets: list[Path]) -> list[Path]:
    protected = [project, backup, (project / "01_data" / "rawdata").resolve(strict=False)]
    unique: list[Path] = []
    for target in targets:
        if any(target == item for item in protected):
            raise ArchiveError(f"refusing broad or protected target: {relative(target, project)}")
        if inside(target, backup) or inside(target, protected[2]):
            raise ArchiveError(f"refusing backup or raw-data target: {relative(target, project)}")
        if target not in unique:
            unique.append(target)
    for parent in unique:
        for child in unique:
            if parent != child and inside(child, parent):
                raise ArchiveError(
                    f"overlapping targets are ambiguous: {relative(parent, project)} and {relative(child, project)}"
                )
    return sorted(unique, key=lambda path: relative(path, project).as_posix())


def manifest_text(
    project: Path,
    batch: Path,
    targets: list[Path],
    current: list[Path],
    reason: str,
    inventories: dict[Path, list[dict[str, Any]]],
) -> str:
    lines = [
        "# Archive manifest",
        "",
        f"- Batch: `{relative(batch, project).as_posix()}`",
        f"- Reason: {reason}",
        "- Operation: exact-path move; original relative paths preserved",
        "",
        "## Archived targets",
        "",
        "| Original path | Archive path | Files |",
        "| --- | --- | ---: |",
    ]
    for target in targets:
        rel = relative(target, project)
        lines.append(
            f"| `{rel.as_posix()}` | `{(relative(batch, project) / rel).as_posix()}` | {len(inventories[target])} |"
        )
    lines.extend(["", "## Current deliverables", ""])
    if current:
        lines.extend(f"- `{relative(path, project).as_posix()}`" for path in current)
    else:
        lines.append("- None recorded; create or identify the current stable deliverable set before sign-off.")
    lines.extend(
        [
            "",
            "## File integrity",
            "",
            "| Original path | Bytes | SHA-256 |",
            "| --- | ---: | --- |",
        ]
    )
    for target in targets:
        for item in inventories[target]:
            lines.append(f"| `{item['path']}` | {item['bytes']} | `{item['sha256']}` |")
    return "\n".join(lines) + "\n"


def update_index_text(
    existing: str,
    *,
    timestamp: str,
    topic: str,
    stage: str,
    batch: Path,
    project: Path,
    current: list[Path],
    reason: str,
) -> str:
    header = (
        "# Archive index\n\n"
        "| Time | Topic | Stage | Archive batch | Current deliverables | Reason |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
    )
    current_text = "<br>".join(f"`{relative(path, project).as_posix()}`" for path in current) or "Pending"
    row = (
        f"| {timestamp.replace('_', ' ')} | {topic} | {stage} | "
        f"`{relative(batch, project).as_posix()}` | {current_text} | {reason} |\n"
    )
    if not existing.strip():
        return header + row
    lines = existing.splitlines(keepends=True)
    separator = next(
        (
            index
            for index, line in enumerate(lines)
            if re.match(r"^\|\s*:?-{3,}", line)
        ),
        None,
    )
    if separator is None:
        raise ArchiveError("09_backup/INDEX.md lacks the expected archive table")
    lines.insert(separator + 1, row)
    return "".join(lines)


def execute_archive(
    project: Path,
    backup: Path,
    batch: Path,
    targets: list[Path],
    current: list[Path],
    reason: str,
    timestamp: str,
    topic: str,
    stage: str,
) -> None:
    inventories = {target: inventory(target, project) for target in targets}
    index_path = backup / "INDEX.md"
    old_index = index_path.read_text(encoding="utf-8-sig") if index_path.is_file() else ""
    moved: list[tuple[Path, Path]] = []
    batch.mkdir(parents=True, exist_ok=False)
    try:
        for target in targets:
            destination = batch / relative(target, project)
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists():
                raise ArchiveError(f"archive destination already exists: {destination}")
            shutil.move(str(target), str(destination))
            moved.append((target, destination))
        (batch / "MANIFEST.md").write_text(
            manifest_text(project, batch, targets, current, reason, inventories),
            encoding="utf-8",
        )
        index_path.write_text(
            update_index_text(
                old_index,
                timestamp=timestamp,
                topic=topic,
                stage=stage,
                batch=batch,
                project=project,
                current=current,
                reason=reason,
            ),
            encoding="utf-8",
        )
    except Exception:
        for original, destination in reversed(moved):
            if destination.exists() and not original.exists():
                original.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(destination), str(original))
        if index_path.exists():
            if old_index:
                index_path.write_text(old_index, encoding="utf-8")
            else:
                index_path.unlink(missing_ok=True)
        if batch.exists():
            shutil.rmtree(batch)
        raise


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--target", action="append", required=True)
    parser.add_argument("--current", action="append", default=[])
    parser.add_argument("--topic", required=True)
    parser.add_argument("--stage", required=True)
    parser.add_argument("--reason", required=True)
    parser.add_argument("--timestamp")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        project = args.project.expanduser().resolve(strict=True)
        if not project.is_dir():
            raise ArchiveError("project must be a directory")
        backup = (project / "09_backup").resolve(strict=False)
        if not backup.is_dir():
            raise ArchiveError("09_backup must already exist; do not upgrade a lightweight task implicitly")
        archive = (backup / "archive").resolve(strict=False)
        if not archive.is_dir():
            raise ArchiveError("09_backup/archive must already exist; do not rewrite a legacy project implicitly")
        timestamp = args.timestamp or dt.datetime.now().strftime("%Y-%m-%d_%H%M")
        if not TIMESTAMP_PATTERN.fullmatch(timestamp):
            raise ArchiveError("timestamp must use YYYY-MM-DD_HHMM")
        topic = safe_label(args.topic, "topic")
        stage = safe_label(args.stage, "stage")
        if not args.reason.strip():
            raise ArchiveError("reason must be non-empty")
        targets = validate_targets(
            project,
            backup,
            [resolve_project_path(project, raw, must_exist=True) for raw in args.target],
        )
        current = [resolve_project_path(project, raw, must_exist=False) for raw in args.current]
        if any(inside(path, backup) or path == project for path in current):
            raise ArchiveError("current deliverable paths must stay in the active project tree")
        batch = choose_batch(archive, timestamp, topic, stage)
        plan = {
            "ok": True,
            "mode": "execute" if args.execute else "plan",
            "batch": relative(batch, project).as_posix(),
            "targets": [relative(path, project).as_posix() for path in targets],
            "current": [relative(path, project).as_posix() for path in current],
        }
        if args.execute:
            execute_archive(
                project,
                backup,
                batch,
                targets,
                current,
                args.reason.strip(),
                timestamp,
                topic,
                stage,
            )
        if args.as_json:
            print(json.dumps(plan, ensure_ascii=False, indent=2))
        else:
            print(f"Archive {plan['mode']}: {plan['batch']}")
            for target in plan["targets"]:
                print(f"  {target} -> {plan['batch']}/{target}")
        return 0
    except (OSError, ArchiveError) as error:
        payload = {"ok": False, "error": type(error).__name__, "detail": str(error)}
        if args.as_json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(f"ERROR: {type(error).__name__}: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
