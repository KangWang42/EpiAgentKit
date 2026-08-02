#!/usr/bin/env python3
"""Build the deterministic EpiAgentKit release archive."""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


VERSION = "1.0"
PACKAGE_NAME = f"EpiAgentKit-release-{VERSION}"
INCLUDED_SKILLS = (
    "academic-humanizer",
    "academic-publishing",
    "biostat-principles",
    "consulting-delivery",
    "epi-project-audit",
    "epi-study-design",
    "evidence-research",
    "git-commit-helper",
    "manuscript-peer-review",
    "project-init",
    "publication-figures",
    "python-biostats",
    "r-biostats",
    "report-writing",
    "research-visuals",
    "skill-creator",
    "svg-diagrams",
)
PUBLICATION_FIGURE_FILES = (
    "SKILL.md",
    "references/chart-gallery.md",
    "references/manuscript-layout.md",
    "references/recipe-quarantine.md",
    "scripts/fig_setup.R",
)
IGNORED_NAMES = {".DS_Store", "Thumbs.db"}
IGNORED_PARTS = {"__pycache__", ".pytest_cache", ".mypy_cache"}
IGNORED_SUFFIXES = {".pyc", ".pyo"}
FORBIDDEN_NAMES = {
    ".env",
    "auth.json",
    "credentials.json",
    "settings.json",
    "settings.local.json",
}
TEXT_SUFFIXES = {
    ".css",
    ".csv",
    ".html",
    ".js",
    ".json",
    ".md",
    ".py",
    ".r",
    ".sh",
    ".toml",
    ".tsv",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)


class ReleaseError(RuntimeError):
    pass


@dataclass(frozen=True)
class BuildResult:
    archive: Path
    checksum_file: Path
    sha256: str
    source_commit: str
    skill_count: int


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_git(repo_root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo_root), *arguments],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise ReleaseError(f"Git command failed: {detail}")
    return completed.stdout.strip()


def git_state(repo_root: Path) -> tuple[str, str]:
    actual_root = Path(run_git(repo_root, "rev-parse", "--show-toplevel")).resolve()
    if actual_root != repo_root.resolve():
        raise ReleaseError(f"Repository root mismatch: {actual_root}")
    source_commit = run_git(repo_root, "rev-parse", "HEAD")
    if not re.fullmatch(r"[0-9a-f]{40}", source_commit):
        raise ReleaseError("SOURCE_COMMIT is not a full Git commit hash.")
    status = run_git(repo_root, "status", "--porcelain=v1", "--untracked-files=all")
    return source_commit, status


def is_ignored(path: Path) -> bool:
    return (
        path.name in IGNORED_NAMES
        or path.suffix.lower() in IGNORED_SUFFIXES
        or bool(set(path.parts) & IGNORED_PARTS)
    )


def collect_skill_files(repo_root: Path, skill_name: str) -> list[tuple[str, Path]]:
    skill_root = repo_root / "skills" / skill_name
    if not skill_root.is_dir() or not (skill_root / "SKILL.md").is_file():
        raise ReleaseError(f"Required skill is missing: {skill_name}")

    if skill_name == "publication-figures":
        candidates = [skill_root / relative for relative in PUBLICATION_FIGURE_FILES]
        missing = [path for path in candidates if not path.is_file()]
        if missing:
            raise ReleaseError(
                "Required publication-figures release file is missing: "
                + ", ".join(str(path.relative_to(repo_root)) for path in missing)
            )
    else:
        candidates = sorted(path for path in skill_root.rglob("*") if path.is_file())

    collected: list[tuple[str, Path]] = []
    for source in candidates:
        relative_source = source.relative_to(repo_root)
        if is_ignored(relative_source):
            continue
        if source.is_symlink():
            raise ReleaseError(f"Symbolic links are not allowed: {relative_source}")
        if source.name.lower() in FORBIDDEN_NAMES:
            raise ReleaseError(f"Sensitive filename is not allowed: {relative_source}")
        collected.append((relative_source.as_posix(), source))
    return collected


def collect_payload(repo_root: Path, source_commit: str) -> dict[str, bytes]:
    mapped_sources = {
        "CLAUDE.md": repo_root / "CLAUDE.md",
        "README_中文.md": repo_root / "docs" / "release-1.0-usage.md",
        "NOTICE_许可与外部依赖.md": repo_root / "docs" / "release-notice.md",
    }
    payload: dict[str, bytes] = {}
    for destination, source in mapped_sources.items():
        if not source.is_file():
            raise ReleaseError(f"Required release source is missing: {source}")
        payload[destination] = source.read_bytes()

    for skill_name in INCLUDED_SKILLS:
        for destination, source in collect_skill_files(repo_root, skill_name):
            payload[destination] = source.read_bytes()

    payload["VERSION"] = f"{VERSION}\n".encode()
    payload["SOURCE_COMMIT"] = f"{source_commit}\n".encode()
    payload["SKILLS_INCLUDED.txt"] = (
        "\n".join(INCLUDED_SKILLS) + "\n"
    ).encode("utf-8")
    validate_payload(repo_root, payload)

    checksums = [
        f"{sha256_bytes(payload[path])}  {path}"
        for path in sorted(payload)
    ]
    payload["SHA256SUMS"] = ("\n".join(checksums) + "\n").encode("utf-8")
    return payload


def validate_payload(repo_root: Path, payload: dict[str, bytes]) -> None:
    repo_markers = {
        str(repo_root.resolve()),
        str(repo_root.resolve()).replace("\\", "/"),
    }
    user_path_pattern = re.compile(
        r"(?i)(?:[A-Z]:[\\/]Users[\\/][^\\/\s]+|/Users/[^/\s]+|/home/[^/\s]+)"
    )

    for relative, data in payload.items():
        path = PurePosixPath(relative)
        if path.is_absolute() or ".." in path.parts or "\\" in relative:
            raise ReleaseError(f"Invalid archive path: {relative}")
        if set(path.parts) & {".git", "09_backup"}:
            raise ReleaseError(f"Forbidden archive path: {relative}")
        if path.name.lower() in FORBIDDEN_NAMES:
            raise ReleaseError(f"Sensitive filename is not allowed: {relative}")

        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {
            "CLAUDE.md",
            "VERSION",
            "SOURCE_COMMIT",
            "SKILLS_INCLUDED.txt",
        }:
            continue
        try:
            text = data.decode("utf-8-sig")
        except UnicodeDecodeError as error:
            raise ReleaseError(f"Release text file is not UTF-8: {relative}") from error
        if "license: Proprietary" in text:
            raise ReleaseError(f"Proprietary skill content is not allowed: {relative}")
        if any(marker and marker in text for marker in repo_markers):
            raise ReleaseError(f"Repository absolute path found in release text: {relative}")
        if user_path_pattern.search(text):
            raise ReleaseError(f"User-profile absolute path found in release text: {relative}")


def safe_remove_tree(path: Path, expected_parent: Path) -> None:
    resolved_parent = expected_parent.resolve()
    resolved_path = path.resolve()
    if resolved_path.parent != resolved_parent or not path.name.startswith(".build-"):
        raise ReleaseError(f"Refusing to remove unexpected build path: {resolved_path}")
    if path.exists():
        shutil.rmtree(path)


def write_staging_manifest(staging_root: Path, payload: dict[str, bytes]) -> Path:
    manifest_path = staging_root / "payload-manifest.txt"
    manifest_path.write_text(
        "\n".join(
            f"{sha256_bytes(data)}  {relative}"
            for relative, data in sorted(payload.items())
        )
        + "\n",
        encoding="utf-8",
    )
    return manifest_path


def write_deterministic_zip(archive_path: Path, payload: dict[str, bytes]) -> None:
    temporary_archive = archive_path.with_name(f".{archive_path.name}.tmp")
    if temporary_archive.exists():
        temporary_archive.unlink()
    with zipfile.ZipFile(
        temporary_archive,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for relative, data in sorted(payload.items()):
            member = f"{PACKAGE_NAME}/{relative}"
            info = zipfile.ZipInfo(member, date_time=FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            executable = PurePosixPath(relative).suffix.lower() in {".py", ".r", ".sh"}
            info.external_attr = ((0o100755 if executable else 0o100644) << 16)
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    with zipfile.ZipFile(temporary_archive, "r") as archive:
        broken_member = archive.testzip()
        if broken_member:
            raise ReleaseError(f"ZIP CRC validation failed: {broken_member}")
    os.replace(temporary_archive, archive_path)


def build_release(
    repo_root: Path,
    output_dir: Path | None = None,
    *,
    allow_dirty: bool = False,
    force: bool = False,
) -> BuildResult:
    repo_root = repo_root.resolve()
    output_dir = (output_dir or repo_root / "releases" / VERSION).resolve()
    source_commit, status = git_state(repo_root)
    if status and not allow_dirty:
        raise ReleaseError(
            "Working tree has uncommitted changes. Commit them or pass --allow-dirty after review."
        )

    archive_path = output_dir / f"{PACKAGE_NAME}.zip"
    checksum_path = output_dir / f"{PACKAGE_NAME}.zip.sha256"
    if not force and (archive_path.exists() or checksum_path.exists()):
        raise ReleaseError("Release target already exists. Pass --force after verification.")

    output_dir.mkdir(parents=True, exist_ok=True)
    staging_root = output_dir / f".build-{PACKAGE_NAME}"
    safe_remove_tree(staging_root, output_dir)
    staging_root.mkdir()
    try:
        payload = collect_payload(repo_root, source_commit)
        write_staging_manifest(staging_root, payload)
        write_deterministic_zip(archive_path, payload)
        archive_sha256 = sha256_file(archive_path)
        temporary_checksum = checksum_path.with_name(f".{checksum_path.name}.tmp")
        temporary_checksum.write_text(
            f"{archive_sha256}  {archive_path.name}\n",
            encoding="utf-8",
            newline="\n",
        )
        os.replace(temporary_checksum, checksum_path)
    finally:
        safe_remove_tree(staging_root, output_dir)

    return BuildResult(
        archive=archive_path,
        checksum_file=checksum_path,
        sha256=archive_sha256,
        source_commit=source_commit,
        skill_count=len(INCLUDED_SKILLS),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--allow-dirty", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = build_release(
            args.repo_root,
            args.output_dir,
            allow_dirty=args.allow_dirty,
            force=args.force,
        )
    except ReleaseError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    print(f"archive={result.archive}")
    print(f"checksum_file={result.checksum_file}")
    print(f"sha256={result.sha256}")
    print(f"source_commit={result.source_commit}")
    print(f"skills={result.skill_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
