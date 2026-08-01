#!/usr/bin/env python3
"""Run deterministic project checks before analysis or deliverable sign-off."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import re
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any, Iterator

from _path_guard import raw_roots


CHECK_CONTRACT_FILE = ".epiagentkit-check.json"
LAYOUT_MANIFEST = ".epiagentkit-layout.json"
DEFAULT_CONTRACT: dict[str, Any] = {
    "code_helper_files": [
        "config.R",
        "config.py",
        "registry.R",
        "registry.py",
        "conventions.R",
        "conventions.py",
        "lib.R",
        "lib.py",
        "modelling.R",
        "modelling.py",
        "run_pipeline.R",
        "run_pipeline.py",
    ],
    "code_helper_dirs": ["lib", "vendored"],
    "prune_dirs": [
        ".git",
        ".cache",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".Rproj.user",
        ".venv",
        "__pycache__",
        "node_modules",
        "renv/library",
        "venv",
        "09_backup",
    ],
    "provenance_receipt": "07_paper/results.provenance.json",
}
SCRIPT_PATTERN = re.compile(r"^(?P<number>\d{2})_(?P<stem>.+)\.(?:R|r|py)$")
TABLE_PATTERN = re.compile(
    r"^Table(?P<number>\d+)_(?P<stem>.+)\.(?P<ext>xlsx)$", re.IGNORECASE
)
FIGURE_PATTERN = re.compile(
    r"^Fig(?P<number>\d+)_(?P<stem>.+)\.(?P<ext>png|pdf|svg)$", re.IGNORECASE
)
OLD_NAME_PATTERN = re.compile(
    r"(?:^|[_.\-\s])(v\d+|new|final|latest|最新版|最终版|完善版|修改版)(?:$|[_.\-\s])",
    re.IGNORECASE,
)
LOG_PATTERN = re.compile(r"\b(error|warning|traceback|failed|nan)\b", re.IGNORECASE)
LOG_LEVELS = {
    "error": "ERROR",
    "traceback": "ERROR",
    "failed": "ERROR",
    "warning": "WARN",
    "nan": "WARN",
}
SECRET_KEY_PATTERN = re.compile(
    r"""(?ix)
    ["']?(api[_-]?key|access[_-]?token|refresh[_-]?token|secret|
    password|passwd|credential|authorization)["']?\s*[:=]\s*
    ["']?([A-Za-z0-9_./+=:-]{8,})
    """
)
KEY_PATH_PATTERN = re.compile(r"^\s*[\"']?([A-Za-z0-9_.-]+)[\"']?\s*[:=]")
TOKEN_PATTERN = re.compile(r"(?<![A-Za-z0-9])[A-Za-z0-9_./+=:-]{32,}(?![A-Za-z0-9])")
HEX_DIGEST_PATTERN = re.compile(r"(?:sha(?:1|224|256|384|512)[-:]?)?[a-f0-9]{32,128}", re.I)
UUID_PATTERN = re.compile(
    r"[a-f0-9]{8}-[a-f0-9]{4}-[1-5][a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}",
    re.I,
)
DOI_PATTERN = re.compile(r"10\.\d{4,9}/\S+", re.I)
LOCKFILE_NAMES = {
    "cargo.lock",
    "composer.lock",
    "package-lock.json",
    "pnpm-lock.yaml",
    "poetry.lock",
    "renv.lock",
    "uv.lock",
    "yarn.lock",
}
PLACEHOLDER_VALUES = {
    "change_me",
    "changeme",
    "example",
    "placeholder",
    "replace_me",
    "replace-with-secret",
    "redacted",
    "your-api-key",
    "your_api_key",
    "your-password",
    "your_password",
    "your-secret",
    "your_secret",
    "your-token",
    "your_token",
}
TEXT_SUFFIXES = {
    ".cfg",
    ".conf",
    ".env",
    ".ini",
    ".json",
    ".md",
    ".py",
    ".r",
    ".sh",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}


def finding(
    findings: list[dict[str, str]],
    level: str,
    check: str,
    path: Path | None = None,
    key: str | None = None,
) -> None:
    evidence = ""
    if path is not None:
        evidence = str(path)
    if key is not None:
        evidence = f"{evidence} [{key}]".strip()
    category = check.split(".", 1)[0]
    guidance = {
        "contract": (
            "The project-specific validation contract cannot be applied reliably.",
            "Repair the contract before sign-off.",
        ),
        "layout": (
            "A project path is undeclared, invalid, or inconsistent with its planned location.",
            "Declare the exact path and ownership before creation, or restore the declared layout.",
        ),
        "rawdata": (
            "Raw-data immutability or provenance may be compromised.",
            "Return to the authoritative source and resolve the provenance issue without modifying raw data.",
        ),
        "code": (
            "The reproducible analysis sequence is incomplete or ambiguous.",
            "Restore the declared numbered pipeline and rerun it.",
        ),
        "tables": (
            "Table numbering or identity is ambiguous.",
            "Reconcile the table registry, producer, and manuscript references.",
        ),
        "figures": (
            "Figure numbering or identity is ambiguous.",
            "Reconcile the figure registry, producer, and manuscript references.",
        ),
        "naming": (
            "A version-like active name can cause the wrong deliverable to be selected.",
            "Archive the replaced artifact and keep one stable semantic current name.",
        ),
        "results": (
            "The result source and its downstream artifacts may be out of sync.",
            "Return to the result producer, regenerate downstream artifacts, and verify provenance.",
        ),
        "provenance": (
            "File origin or synchronization cannot be proven deterministically.",
            "Regenerate or update the provenance receipt and investigate every mismatch.",
        ),
        "logs": (
            "The execution log contains a term that requires technical review.",
            "Inspect the full cited line and upstream step; fix blocking errors and explain non-blocking warnings.",
        ),
        "secrets": (
            "A possible credential or secret is present in the active project.",
            "Remove it safely, rotate exposed credentials, and keep only a configuration key reference.",
        ),
        "submission": (
            "The active manuscript revision or reviewer-response record is not ready for sign-off.",
            "Resolve the cited state-card issue and revalidate the submission set.",
        ),
        "project": (
            "The requested project cannot be checked.",
            "Provide an existing formal-project directory.",
        ),
    }.get(
        category,
        (
            "The project contract requires review at the cited evidence location.",
            "Inspect the evidence and apply the owning workflow's corrective action.",
        ),
    )
    item = {
        "level": level,
        "check": check,
        "rule": check,
        "evidence": evidence or check,
        "impact": guidance[0],
        "action": guidance[1],
    }
    if path is not None:
        item["path"] = str(path)
    if key is not None:
        item["key"] = key
    findings.append(item)


def layout_actual_paths(
    project: Path,
    roots: list[Path],
    contract: dict[str, Any],
) -> dict[Path, str]:
    actual: dict[Path, str] = {}
    backup = (project / "09_backup").resolve(strict=False)
    workbench = (backup / "workbench").resolve(strict=False)
    prune_names = {Path(value).name.casefold() for value in contract["prune_dirs"]}
    prune_names.discard("09_backup")
    for current_raw, directories, files in os.walk(project, topdown=True, followlinks=False):
        current = Path(current_raw).resolve(strict=False)
        if any(current == root for root in roots):
            directories[:] = []
            continue
        kept: list[str] = []
        if current == backup:
            for name in directories:
                child = (current / name).resolve(strict=False)
                if child == workbench:
                    actual[relative(child, project)] = "dir"
                    kept.append(name)
        elif current != workbench:
            for name in directories:
                child = (current / name).resolve(strict=False)
                if name.casefold() in prune_names or any(root in child.parents for root in roots):
                    continue
                rel = relative(child, project)
                actual[rel] = "dir"
                kept.append(name)
        directories[:] = kept
        for name in files:
            path = (current / name).resolve(strict=False)
            if any(root in path.parents for root in roots):
                continue
            actual[relative(path, project)] = "file"
    return actual


def layout_check(
    project: Path,
    roots: list[Path],
    contract: dict[str, Any],
    findings: list[dict[str, str]],
) -> None:
    manifest_path = project / LAYOUT_MANIFEST
    if not manifest_path.is_file():
        finding(findings, "WARN", "layout.manifest_missing", Path(LAYOUT_MANIFEST))
        return
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as error:
        finding(findings, "ERROR", "layout.manifest_invalid", Path(LAYOUT_MANIFEST), type(error).__name__)
        return
    entries = payload.get("entries") if isinstance(payload, dict) else None
    if (
        not isinstance(payload, dict)
        or payload.get("schema_version") != 1
        or payload.get("policy") != "declare-before-create"
        or not isinstance(entries, list)
    ):
        finding(findings, "ERROR", "layout.manifest_invalid", Path(LAYOUT_MANIFEST), "schema")
        return
    declared: dict[Path, tuple[str, str]] = {}
    required = ("path", "kind", "owner", "purpose", "producer", "consumer", "lifecycle")
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict) or any(not isinstance(entry.get(key), str) or not entry[key].strip() for key in required):
            finding(findings, "ERROR", "layout.entry_invalid", Path(LAYOUT_MANIFEST), f"entry@{index}")
            continue
        raw_path = entry["path"].replace("\\", "/")
        raw_parts = Path(raw_path).parts
        if Path(raw_path).is_absolute() or raw_path.startswith("/") or ".." in raw_parts:
            finding(findings, "ERROR", "layout.path_escape", Path(LAYOUT_MANIFEST), f"entry@{index}")
            continue
        candidate = (project / raw_path).resolve(strict=False)
        try:
            rel = relative(candidate, project)
        except ValueError:
            finding(findings, "ERROR", "layout.path_escape", Path(LAYOUT_MANIFEST), f"entry@{index}")
            continue
        if entry["kind"] not in {"file", "dir"} or entry["lifecycle"] not in {"planned", "active", "current_deliverable"}:
            finding(findings, "ERROR", "layout.entry_invalid", rel, "kind_or_lifecycle")
            continue
        if rel in declared:
            finding(findings, "ERROR", "layout.path_duplicate", rel)
            continue
        declared[rel] = (entry["kind"], entry["lifecycle"])

    actual = layout_actual_paths(project, roots, contract)
    for rel, kind in actual.items():
        if rel not in declared:
            finding(findings, "ERROR", "layout.path_undeclared", rel, kind)
        elif declared[rel][0] != kind:
            finding(findings, "ERROR", "layout.kind_mismatch", rel, f"declared={declared[rel][0]};actual={kind}")
    for rel, (kind, lifecycle) in declared.items():
        declared_path = (project / rel).resolve(strict=False)
        inside_raw_root = any(root == declared_path or root in declared_path.parents for root in roots)
        if lifecycle != "planned" and rel not in actual and not inside_raw_root:
            finding(findings, "WARN", "layout.declared_missing", rel, kind)


def submission_state_check(project: Path, findings: list[dict[str, str]]) -> None:
    state_path = project / "07_paper" / "submission" / "revision-state.json"
    if not state_path.is_file():
        return
    validator = (
        Path(__file__).resolve().parents[1]
        / "skills"
        / "academic-humanizer"
        / "scripts"
        / "validate_revision_state.py"
    )
    if not validator.is_file():
        finding(findings, "ERROR", "submission.validator_missing", relative(state_path, project))
        return
    try:
        spec = importlib.util.spec_from_file_location("epiagentkit_revision_state", validator)
        if spec is None or spec.loader is None:
            raise ImportError("validator loader unavailable")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        state_findings = module.validate_state_file(state_path, signoff=True)
    except Exception as error:
        finding(findings, "ERROR", "submission.state_unreadable", relative(state_path, project), type(error).__name__)
        return
    for item in state_findings:
        record = {
            "level": item.get("level", "ERROR"),
            "check": f"submission.{item.get('rule', 'state_invalid')}",
            "rule": item.get("rule", "state_invalid"),
            "evidence": item.get("evidence", str(relative(state_path, project))),
            "impact": item.get("impact", "The submission state is not ready for sign-off."),
            "action": item.get("action", "Repair and revalidate the revision state card."),
            "path": str(relative(state_path, project)),
        }
        findings.append(record)


def relative(path: Path, project: Path) -> Path:
    try:
        return path.resolve(strict=False).relative_to(project)
    except ValueError:
        return path.resolve(strict=False)


def inside(path: Path, roots: list[Path]) -> bool:
    resolved = path.resolve(strict=False)
    return any(resolved == root or root in resolved.parents for root in roots)


def load_contract(project: Path, findings: list[dict[str, str]]) -> dict[str, Any]:
    contract = {
        key: list(value) if isinstance(value, list) else value
        for key, value in DEFAULT_CONTRACT.items()
    }
    path = project / CHECK_CONTRACT_FILE
    if not path.is_file():
        return contract
    try:
        override = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as error:
        finding(findings, "ERROR", "contract.invalid", Path(CHECK_CONTRACT_FILE), type(error).__name__)
        return contract
    if not isinstance(override, dict):
        finding(findings, "ERROR", "contract.invalid", Path(CHECK_CONTRACT_FILE), "root_not_object")
        return contract
    for key in ("code_helper_files", "code_helper_dirs", "prune_dirs"):
        values = override.get(key, [])
        if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
            finding(findings, "ERROR", "contract.invalid", Path(CHECK_CONTRACT_FILE), key)
            continue
        contract[key] = list(dict.fromkeys([*contract[key], *values]))
    receipt = override.get("provenance_receipt")
    if receipt is not None:
        candidate = (
            (project / receipt.replace("\\", "/")).resolve(strict=False)
            if isinstance(receipt, str) and receipt.strip()
            else None
        )
        if candidate is not None and not relative(candidate, project).is_absolute():
            contract["provenance_receipt"] = receipt
        else:
            finding(
                findings,
                "ERROR",
                "contract.invalid",
                Path(CHECK_CONTRACT_FILE),
                "provenance_receipt",
            )
    return contract


def git_raw_check(project: Path, roots: list[Path], findings: list[dict[str, str]]) -> None:
    try:
        probe = subprocess.run(
            ["git", "-C", str(project), "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError as error:
        finding(findings, "WARN", "rawdata.git_unavailable", key=type(error).__name__)
        return
    if probe.returncode:
        finding(findings, "WARN", "rawdata.git_unavailable")
        return
    for root in roots:
        rel = relative(root, project)
        if rel.is_absolute():
            finding(findings, "WARN", "rawdata.outside_project", rel)
            continue
        try:
            status = subprocess.run(
                [
                    "git",
                    "-C",
                    str(project),
                    "status",
                    "--porcelain",
                    "--untracked-files=all",
                    "--",
                    rel.as_posix(),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except OSError as error:
            finding(
                findings,
                "ERROR",
                "rawdata.git_status_failed",
                rel,
                type(error).__name__,
            )
            continue
        if status.returncode:
            finding(findings, "ERROR", "rawdata.git_status_failed", rel)
        elif status.stdout.strip():
            for line in status.stdout.splitlines():
                changed = line[3:].strip() if len(line) > 3 else rel.as_posix()
                finding(findings, "ERROR", "rawdata.worktree_modified", Path(changed))


def artifact_sequence_check(
    directory: Path,
    pattern: re.Pattern[str],
    check: str,
    findings: list[dict[str, str]],
) -> None:
    if not directory.is_dir():
        return
    groups: dict[int, set[str]] = {}
    for path in directory.iterdir():
        if not path.is_file():
            continue
        match = pattern.match(path.name)
        if not match:
            continue
        number = int(match.group("number"))
        stem = match.groupdict().get("stem", path.stem).casefold()
        groups.setdefault(number, set()).add(stem)
    if not groups:
        return
    expected = set(range(1, max(groups) + 1))
    if set(groups) != expected:
        finding(findings, "ERROR", f"{check}.numbering_gap", relative(directory, directory.parent))
    for number, stems in sorted(groups.items()):
        if len(stems) > 1:
            finding(
                findings,
                "ERROR",
                f"{check}.duplicate_number",
                relative(directory, directory.parent),
                f"{number}:{','.join(sorted(stems))}",
            )


def code_check(
    project: Path, contract: dict[str, Any], findings: list[dict[str, str]]
) -> None:
    directory = project / "02_code"
    artifact_sequence_check(directory, SCRIPT_PATTERN, "code", findings)
    if not directory.is_dir():
        return
    helpers = {name.casefold() for name in contract["code_helper_files"]}
    numbered = 0
    for path in directory.iterdir():
        if not path.is_file() or path.suffix.casefold() not in {".r", ".py"}:
            continue
        if SCRIPT_PATTERN.match(path.name):
            numbered += 1
        elif path.name.casefold() not in helpers:
            finding(findings, "ERROR", "code.unnumbered_script", relative(path, project))
    if numbered > 10:
        finding(findings, "ERROR", "code.too_many_numbered_scripts", Path("02_code"), str(numbered))


def prune_directories(
    current: Path,
    directories: list[str],
    project: Path,
    roots: list[Path],
    contract: dict[str, Any],
) -> None:
    names = {Path(value).name.casefold() for value in contract["prune_dirs"]}
    relative_prunes = {
        Path(value.replace("\\", "/")).as_posix().casefold()
        for value in contract["prune_dirs"]
        if "/" in value.replace("\\", "/")
    }
    kept: list[str] = []
    for name in directories:
        child = (current / name).resolve(strict=False)
        rel = relative(child, project)
        rel_key = rel.as_posix().casefold() if not rel.is_absolute() else ""
        if name.casefold() in names or rel_key in relative_prunes or inside(child, roots):
            continue
        kept.append(name)
    directories[:] = kept


def active_files(
    project: Path, roots: list[Path], contract: dict[str, Any]
) -> Iterator[tuple[Path, Path]]:
    for current_raw, directories, files in os.walk(project, topdown=True, followlinks=False):
        current = Path(current_raw)
        prune_directories(current, directories, project, roots, contract)
        for name in files:
            path = current / name
            if inside(path, roots):
                continue
            yield path, relative(path, project)


def old_names_check(
    project: Path,
    roots: list[Path],
    contract: dict[str, Any],
    findings: list[dict[str, str]],
) -> None:
    for _path, rel in active_files(project, roots, contract):
        if any(OLD_NAME_PATTERN.search(part) for part in rel.parts):
            finding(findings, "ERROR", "naming.legacy_version", rel)


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def provenance_check(
    project: Path,
    receipt_path: Path,
    outputs: list[Path],
    findings: list[dict[str, str]],
) -> bool:
    if not receipt_path.is_file():
        return False
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8-sig"))
        files = receipt.get("files", {})
    except (OSError, json.JSONDecodeError, AttributeError) as error:
        finding(findings, "ERROR", "provenance.invalid", relative(receipt_path, project), type(error).__name__)
        return True
    if not isinstance(files, dict) or not files:
        finding(findings, "ERROR", "provenance.invalid", relative(receipt_path, project), "files")
        return True
    listed: set[str] = set()
    for raw_path, expected in files.items():
        if not isinstance(raw_path, str) or not isinstance(expected, str):
            finding(findings, "ERROR", "provenance.invalid", relative(receipt_path, project), "entry")
            continue
        target = (project / raw_path.replace("\\", "/")).resolve(strict=False)
        rel = relative(target, project)
        if rel.is_absolute() or not target.is_file():
            finding(findings, "ERROR", "provenance.file_missing", rel)
            continue
        listed.add(rel.as_posix())
        if not re.fullmatch(r"[a-fA-F0-9]{64}", expected) or sha256(target) != expected.casefold():
            finding(findings, "ERROR", "provenance.hash_mismatch", rel)
    for output in outputs:
        rel = relative(output, project)
        if rel.as_posix() not in listed:
            finding(findings, "WARN", "provenance.output_unlisted", rel)
    return True


def result_sync_check(
    project: Path, contract: dict[str, Any], findings: list[dict[str, str]]
) -> None:
    paper = project / "07_paper"
    if not paper.is_dir():
        return
    source = paper / "results.yaml"
    summary = paper / "0_result_summaries.md"
    if not source.is_file():
        finding(findings, "ERROR", "results.source_missing", Path("07_paper/results.yaml"))
        return
    if not summary.is_file():
        finding(findings, "ERROR", "results.summary_missing", Path("07_paper/0_result_summaries.md"))
    outputs = [
        path
        for directory in (project / "03_tables", project / "04_figures")
        if directory.is_dir()
        for path in directory.rglob("*")
        if path.is_file()
    ]
    receipt = (project / str(contract["provenance_receipt"])).resolve(strict=False)
    if provenance_check(project, receipt, [source, summary, *outputs], findings):
        return
    if summary.is_file() and summary.stat().st_mtime_ns < source.stat().st_mtime_ns:
        finding(findings, "WARN", "results.summary_mtime_stale", Path("07_paper/0_result_summaries.md"))
    if outputs and max(path.stat().st_mtime_ns for path in outputs) > source.stat().st_mtime_ns:
        finding(findings, "WARN", "results.source_mtime_older_than_outputs", Path("07_paper/results.yaml"))
    finding(findings, "WARN", "provenance.receipt_missing", relative(receipt, project))


def log_check(
    project: Path,
    roots: list[Path],
    contract: dict[str, Any],
    findings: list[dict[str, str]],
) -> None:
    for path, rel in active_files(project, roots, contract):
        if path.suffix.casefold() not in {".err", ".log", ".out"}:
            continue
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        for line_number, line in enumerate(text.splitlines(), start=1):
            terms = {match.group(1).casefold() for match in LOG_PATTERN.finditer(line)}
            for term in sorted(terms):
                finding(
                    findings,
                    LOG_LEVELS[term],
                    "logs.abnormal_term",
                    rel,
                    f"{term}@{line_number}",
                )


def entropy(value: str) -> float:
    counts = Counter(value)
    length = len(value)
    return -sum((count / length) * math.log2(count / length) for count in counts.values())


def benign_high_entropy(value: str, path: Path) -> bool:
    stripped = value.strip("\"'()[]{}<>,.;")
    return (
        path.name.casefold() in LOCKFILE_NAMES
        or bool(HEX_DIGEST_PATTERN.fullmatch(stripped))
        or bool(UUID_PATTERN.fullmatch(stripped))
        or bool(DOI_PATTERN.fullmatch(stripped))
        or stripped.casefold().startswith(("http://", "https://", "sha256-", "sha512-"))
    )


def benign_named_credential(value: str, path: Path) -> bool:
    stripped = value.strip("\"'()[]{}<>,.;").casefold()
    return (
        benign_high_entropy(value, path)
        or stripped in PLACEHOLDER_VALUES
        or stripped.startswith(
            (
                "config.",
                "env.",
                "getenv",
                "getpass.",
                "keyring.",
                "os.environ",
                "os.getenv",
                "process.env",
                "secrets.",
                "settings.",
                "sys.getenv",
            )
        )
    )


def secret_check(
    project: Path,
    roots: list[Path],
    contract: dict[str, Any],
    findings: list[dict[str, str]],
) -> None:
    reported: set[tuple[Path, str]] = set()
    for path, rel in active_files(project, roots, contract):
        if path.suffix.casefold() not in TEXT_SUFFIXES or path.stat().st_size > 2_000_000:
            continue
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        for line_number, line in enumerate(text.splitlines(), start=1):
            for match in SECRET_KEY_PATTERN.finditer(line):
                if benign_named_credential(match.group(2), path):
                    continue
                key_match = KEY_PATH_PATTERN.match(line)
                key_path = key_match.group(1) if key_match else match.group(1)
                marker = (rel, f"{key_path}@{line_number}")
                if marker not in reported:
                    finding(findings, "ERROR", "secrets.named_credential", rel, marker[1])
                    reported.add(marker)
            for match in TOKEN_PATTERN.finditer(line):
                value = match.group(0)
                if benign_high_entropy(value, path):
                    continue
                character_classes = sum(
                    (
                        any(char.islower() for char in value),
                        any(char.isupper() for char in value),
                        any(char.isdigit() for char in value),
                        any(not char.isalnum() for char in value),
                    )
                )
                if (
                    character_classes >= 3
                    and len(set(value)) >= 8
                    and entropy(value) >= 4.0
                ):
                    marker = (rel, f"high_entropy_candidate@{line_number}")
                    if marker not in reported:
                        finding(findings, "ERROR", "secrets.high_entropy", rel, marker[1])
                        reported.add(marker)


def run_checks(project: Path) -> list[dict[str, str]]:
    project = project.expanduser().resolve(strict=False)
    findings: list[dict[str, str]] = []
    if not project.is_dir():
        finding(findings, "ERROR", "project.not_directory", project)
        return findings
    contract = load_contract(project, findings)
    protected = raw_roots(project)
    git_raw_check(project, protected, findings)
    layout_check(project, protected, contract, findings)
    code_check(project, contract, findings)
    artifact_sequence_check(project / "03_tables", TABLE_PATTERN, "tables", findings)
    artifact_sequence_check(project / "04_figures", FIGURE_PATTERN, "figures", findings)
    old_names_check(project, protected, contract, findings)
    result_sync_check(project, contract, findings)
    log_check(project, protected, contract, findings)
    secret_check(project, protected, contract, findings)
    submission_state_check(project, findings)
    return findings


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", nargs="?", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    project = args.project.expanduser().resolve(strict=False)
    findings = run_checks(project)
    errors = [item for item in findings if item["level"] == "ERROR"]
    if args.as_json:
        print(
            json.dumps(
                {"ok": not errors, "project": str(project), "findings": findings},
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        for item in findings:
            detail = item.get("path", "")
            if item.get("key"):
                detail = f"{detail} [{item['key']}]".strip()
            print(f"[{item['level']}] {item['check']}: {detail}".rstrip())
            print(f"  Impact: {item['impact']}")
            print(f"  Action: {item['action']}")
        print(
            f"Final project check {'passed' if not errors else 'failed'}: "
            f"{len(errors)} error(s), "
            f"{sum(item['level'] == 'WARN' for item in findings)} warning(s)"
        )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
