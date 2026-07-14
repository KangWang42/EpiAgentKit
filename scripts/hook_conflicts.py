#!/usr/bin/env python3
"""Remove local hook registrations that overlap EpiAgentKit hooks."""

from __future__ import annotations

import json
import os
import re
import shutil
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 compatibility
    tomllib = None


RAW_DOMAIN = "raw" + "data_protection"
DOMAIN_NAMES = {
    RAW_DOMAIN: {"protect_" + "raw" + "data", "protect_raw_data"},
    "r_syntax": {"check_r_syntax", "r_syntax_check"},
    "ai_trace": {"scan_ai_trace", "check_ai_trace", "ai_trace_scan"},
    "figure_check": {"fig_selfcheck", "figure_selfcheck", "check_figures"},
    "rds_check": {"check_results_rds", "results_rds_check", "check_rds"},
    "edit_checks": {"post_edit_checks"},
    "bash_checks": {"post_bash_checks"},
}
DOMAIN_TARGETS = {
    RAW_DOMAIN: ("PreToolUse", ("Edit", "Write", "MultiEdit", "apply_patch")),
    "r_syntax": ("PostToolUse", ("Edit", "Write", "MultiEdit", "apply_patch")),
    "ai_trace": ("PostToolUse", ("Edit", "Write", "MultiEdit", "apply_patch")),
    "figure_check": ("PostToolUse", ("Bash",)),
    "rds_check": ("PostToolUse", ("Bash",)),
}
SCRIPT_PATTERN = re.compile(
    r'''(?i)(?:"([^"]+\.(?:py|sh|cmd|ps1))"|'([^']+\.(?:py|sh|cmd|ps1))'|([^\s"']+\.(?:py|sh|cmd|ps1)))'''
)
OUTER_HOOK = re.compile(
    r"^\s*\[\[hooks\.([A-Za-z][A-Za-z0-9_]*)\]\]\s*(?:#.*)?$"
)
HANDLER_HOOK = re.compile(
    r"^\s*\[\[hooks\.([A-Za-z][A-Za-z0-9_]*)\.hooks\]\]\s*(?:#.*)?$"
)
ANY_TABLE = re.compile(r"^\s*\[+[^]]+\]+\s*(?:#.*)?$")
STATE_TABLE = re.compile(r"^\s*\[hooks\.state\.(.+)\]\s*(?:#.*)?$")
KEY_VALUE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+?)\s*$")


@dataclass(frozen=True)
class HookConflict:
    platform: str
    config_path: str
    event: str
    matcher: str
    command_files: tuple[str, ...]
    domains: tuple[str, ...]


def _commands(handler: dict) -> list[str]:
    return [
        value
        for key in ("command", "commandWindows", "command_windows")
        if isinstance((value := handler.get(key)), str) and value
    ]


def _script_paths(command: str, hooks_dir: Path) -> set[Path]:
    result: set[Path] = set()
    root = hooks_dir.resolve()
    for match in SCRIPT_PATTERN.finditer(command):
        raw = next(value for value in match.groups() if value)
        candidate = Path(os.path.expandvars(raw)).expanduser()
        if not candidate.is_absolute():
            candidate = hooks_dir / candidate.name
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        if resolved.parent == root:
            result.add(resolved)
    return result


def _read_hook_text(path: Path) -> str:
    last_error: UnicodeDecodeError | None = None
    for encoding in ("utf-8-sig", "utf-8", "gb18030", "utf-16"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError as error:
            last_error = error
    raise ValueError(f"Cannot decode local hook script {path}: {last_error}")


def _domains(command: str, hooks_dir: Path) -> set[str]:
    normalized = command.lower().replace("-", "_")
    paths = _script_paths(command, hooks_dir)
    stems = {path.stem.lower().replace("-", "_") for path in paths}
    stems.update(
        token.lower().replace("-", "_")
        for token in re.findall(r"[A-Za-z0-9_-]+(?=\.(?:py|sh|cmd|ps1)\b)", command)
    )
    result = {
        domain
        for domain, names in DOMAIN_NAMES.items()
        if names & stems or any(name in normalized for name in names)
    }
    if "edit_checks" in result:
        result.update(("r_syntax", "ai_trace"))
    if "bash_checks" in result:
        result.update(("figure_check", "rds_check"))

    content = ""
    for path in paths:
        if path.is_file():
            try:
                content += "\n" + _read_hook_text(path).lower()
            except OSError:
                pass
    raw_marker = "raw" + "data"
    if raw_marker in content and ("01_data" in content or "raw_roots" in content):
        result.add(RAW_DOMAIN)
    if "parse(file" in content or ("rscript" in content and "parse(" in content):
        result.add("r_syntax")
    trace_markers = ("emoji", "ai trace", "backlog.md", "生成过程痕迹")
    if sum(marker in content for marker in trace_markers) >= 2:
        result.add("ai_trace")
    if "04_figures" in content and (
        "publication-figures" in content or "fig_selfcheck" in content
    ):
        result.add("figure_check")
    if "06_results" in content and ".rds" in content:
        result.add("rds_check")
    return result - {"edit_checks", "bash_checks"}


def _matcher_overlaps(matcher: str, tools: tuple[str, ...]) -> bool:
    if not matcher or matcher == "*":
        return True
    try:
        return any(re.search(matcher, tool) for tool in tools)
    except re.error:
        return any(tool.lower() in matcher.lower() for tool in tools)


def _conflicting_domains(
    event: str, matcher: str, commands: list[str], hooks_dir: Path
) -> tuple[str, ...]:
    detected = (
        set().union(*(_domains(command, hooks_dir) for command in commands))
        if commands
        else set()
    )
    return tuple(
        sorted(
            domain
            for domain in detected
            if DOMAIN_TARGETS[domain][0] == event
            and _matcher_overlaps(matcher, DOMAIN_TARGETS[domain][1])
        )
    )


def _filter_groups(
    platform: str,
    config_path: Path,
    hooks: dict,
    hooks_dir: Path,
    protected_names: set[str],
) -> tuple[dict, list[HookConflict], set[Path]]:
    updated: dict = {}
    conflicts: list[HookConflict] = []
    candidates: set[Path] = set()
    for event, groups in hooks.items():
        if not isinstance(groups, list):
            updated[event] = groups
            continue
        retained_groups = []
        for group in groups:
            if not isinstance(group, dict) or not isinstance(group.get("hooks"), list):
                retained_groups.append(group)
                continue
            matcher = str(group.get("matcher", ""))
            retained_handlers = []
            for handler in group["hooks"]:
                commands = _commands(handler) if isinstance(handler, dict) else []
                referenced = (
                    set().union(
                        *(_script_paths(command, hooks_dir) for command in commands)
                    )
                    if commands
                    else set()
                )
                if any(path.name in protected_names for path in referenced):
                    retained_handlers.append(handler)
                    continue
                domains = _conflicting_domains(event, matcher, commands, hooks_dir)
                if not domains:
                    retained_handlers.append(handler)
                    continue
                conflicts.append(
                    HookConflict(
                        platform=platform,
                        config_path=str(config_path),
                        event=event,
                        matcher=matcher,
                        command_files=tuple(
                            sorted(
                                {
                                    path.name
                                    for command in commands
                                    for path in _script_paths(command, hooks_dir)
                                }
                            )
                        )
                        or ("<inline-command>",),
                        domains=domains,
                    )
                )
                for value in commands:
                    candidates.update(_script_paths(value, hooks_dir))
            if retained_handlers:
                retained = dict(group)
                retained["hooks"] = retained_handlers
                retained_groups.append(retained)
        updated[event] = retained_groups
    return updated, conflicts, candidates


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ValueError(f"Cannot update invalid JSON config {path}: {error}") from error
    if not isinstance(data, dict):
        raise ValueError(f"Config root must be a JSON object: {path}")
    return data


def _toml_value(raw: str) -> object:
    value = raw.strip()
    if value.startswith("'") and "'" in value[1:]:
        return value[1 : value.rfind("'")]
    if value.startswith('"'):
        try:
            return json.loads(value[: value.rfind('"') + 1])
        except json.JSONDecodeError:
            return value.strip('"')
    if value.split("#", 1)[0].strip().lower() in {"true", "false"}:
        return value.split("#", 1)[0].strip().lower() == "true"
    try:
        return int(value.split("#", 1)[0].strip())
    except ValueError:
        return value.split("#", 1)[0].strip()


def _inline_hooks(path: Path) -> dict:
    if not path.is_file():
        return {}
    if tomllib is not None:
        try:
            data = tomllib.loads(path.read_text(encoding="utf-8-sig"))
        except (tomllib.TOMLDecodeError, UnicodeDecodeError) as error:
            raise ValueError(f"Cannot update invalid TOML config {path}: {error}") from error
        hooks = data.get("hooks", {})
        if not isinstance(hooks, dict):
            raise ValueError(f"Existing 'hooks' setting must be a TOML table: {path}")
        return {event: groups for event, groups in hooks.items() if isinstance(groups, list)}

    hooks: dict[str, list[dict]] = {}
    current_group: dict | None = None
    current_handler: dict | None = None
    current_event = ""
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        outer = OUTER_HOOK.match(line)
        if outer:
            current_event = outer.group(1)
            current_group = {"hooks": []}
            hooks.setdefault(current_event, []).append(current_group)
            current_handler = None
            continue
        handler = HANDLER_HOOK.match(line)
        if handler and current_group is not None and handler.group(1) == current_event:
            current_handler = {}
            current_group["hooks"].append(current_handler)
            continue
        if ANY_TABLE.match(line):
            current_group = None
            current_handler = None
            current_event = ""
            continue
        setting = KEY_VALUE.match(line)
        if setting and current_group is not None:
            target = current_handler if current_handler is not None else current_group
            target[setting.group(1)] = _toml_value(setting.group(2))
    return hooks


def _strip_inline_hooks(text: str, config_path: Path) -> str:
    lines = text.splitlines(keepends=True)
    retained: list[str] = []
    index = 0
    path_markers = {str(config_path).lower(), config_path.as_posix().lower()}
    while index < len(lines):
        line = lines[index]
        if OUTER_HOOK.match(line):
            index += 1
            while index < len(lines):
                if OUTER_HOOK.match(lines[index]):
                    break
                if ANY_TABLE.match(lines[index]) and ".hooks]]" not in lines[index]:
                    break
                index += 1
            continue
        state = STATE_TABLE.match(line)
        if state and any(marker in state.group(1).lower() for marker in path_markers):
            index += 1
            while index < len(lines) and not ANY_TABLE.match(lines[index]):
                index += 1
            continue
        retained.append(line)
        index += 1
    return "".join(retained)


def _merge_groups(target: dict, additions: dict) -> None:
    hooks = target.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError("Existing 'hooks' setting must be a JSON object")
    for event, groups in additions.items():
        destination = hooks.setdefault(event, [])
        if not isinstance(destination, list):
            raise ValueError(f"Existing hooks.{event} setting must be a JSON array")
        fingerprints = {
            json.dumps(item, sort_keys=True, ensure_ascii=False) for item in destination
        }
        for group in groups:
            fingerprint = json.dumps(group, sort_keys=True, ensure_ascii=False)
            if fingerprint not in fingerprints:
                destination.append(group)
                fingerprints.add(fingerprint)


def _normalize_inline_groups(hooks: dict) -> None:
    for groups in hooks.values():
        for group in groups:
            if not isinstance(group, dict):
                continue
            for handler in group.get("hooks", []):
                if (
                    isinstance(handler, dict)
                    and "command_windows" in handler
                    and "commandWindows" not in handler
                ):
                    handler["commandWindows"] = handler.pop("command_windows")


def _referenced_scripts(config: dict, hooks_dir: Path) -> set[Path]:
    result: set[Path] = set()
    hooks = config.get("hooks", {})
    if not isinstance(hooks, dict):
        return result
    for groups in hooks.values():
        if not isinstance(groups, list):
            continue
        for group in groups:
            if not isinstance(group, dict):
                continue
            for handler in group.get("hooks", []):
                if isinstance(handler, dict):
                    for command in _commands(handler):
                        result.update(_script_paths(command, hooks_dir))
    return result


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".epi-{uuid.uuid4().hex[:8]}.tmp")
    temporary.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def _backup(path: Path) -> None:
    backup = path.with_name(f"{path.name}.epiagentkit.bak")
    legacy = path.with_name(f"{path.name}.epiclaude.bak")
    if legacy.is_file() and not backup.exists():
        print(f"RENAME {legacy} -> {backup}")
        legacy.replace(backup)
        return
    if path.is_file() and not backup.exists():
        print(f"BACKUP {path} -> {backup}")
        shutil.copyfile(path, backup)


def reconcile_hook_conflicts(
    *,
    platform: str,
    json_config: Path,
    hooks_dir: Path,
    home: Path,
    protected_names: set[str],
    dry_run: bool,
    inline_config: Path | None = None,
) -> Path | None:
    """Delete conflicting local hooks and consolidate Codex inline hooks."""
    current_json = _load_json(json_config)
    current_hooks = current_json.get("hooks", {})
    if not isinstance(current_hooks, dict):
        raise ValueError(f"Existing 'hooks' setting must be a JSON object: {json_config}")
    filtered, conflicts, candidates = _filter_groups(
        platform, json_config, current_hooks, hooks_dir, protected_names
    )
    updated_json = json.loads(json.dumps(current_json))
    if filtered or "hooks" in updated_json:
        updated_json["hooks"] = filtered

    updated_toml: str | None = None
    migrated_count = 0
    if inline_config and inline_config.is_file():
        inline = _inline_hooks(inline_config)
        retained, found, paths = _filter_groups(
            platform, inline_config, inline, hooks_dir, protected_names
        )
        conflicts.extend(found)
        candidates.update(paths)
        migrated_count = sum(len(groups) for groups in retained.values())
        _normalize_inline_groups(retained)
        _merge_groups(updated_json, retained)
        original_toml = inline_config.read_text(encoding="utf-8-sig")
        stripped = _strip_inline_hooks(original_toml, inline_config)
        if stripped != original_toml:
            updated_toml = stripped

    retained_scripts = _referenced_scripts(updated_json, hooks_dir)
    removable = {
        path
        for path in candidates - retained_scripts
        if path.name not in protected_names and path.is_file()
    }
    if not conflicts and not updated_toml:
        print(f"Hook conflict preflight ({platform}): no conflicts found.")
        return None

    for conflict in conflicts:
        print(
            f"CONFLICT hook {conflict.event}/{conflict.matcher or '*'}: "
            f"{', '.join(conflict.domains)} -> EpiAgentKit"
        )
    if migrated_count:
        print(f"MIGRATE {migrated_count} non-conflicting inline hook group(s) -> {json_config}")
    for path in sorted(removable):
        print(f"{'WOULD REMOVE' if dry_run else 'REMOVE'} {path}")

    run_id = (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        + "-"
        + uuid.uuid4().hex[:8]
    )
    manifest = (
        home.resolve()
        / ".epiagentkit"
        / "hook-conflict-reports"
        / run_id
        / "manifest.json"
    )
    if dry_run:
        print(f"Hook conflict report would be written under {manifest.parent}")
        return manifest

    if updated_json != current_json:
        _backup(json_config)
        _write_json(json_config, updated_json)
    if updated_toml is not None and inline_config is not None:
        _backup(inline_config)
        inline_config.write_text(updated_toml, encoding="utf-8")
    for path in removable:
        path.unlink()

    payload = {
        "schema": 1,
        "project": "EpiAgentKit",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "platform": platform,
        "conflicts": [asdict(item) for item in conflicts],
        "deleted_scripts": [str(path) for path in sorted(removable)],
        "migrated_inline_groups": migrated_count,
    }
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"WRITE  hook conflict report -> {manifest}")
    return manifest
