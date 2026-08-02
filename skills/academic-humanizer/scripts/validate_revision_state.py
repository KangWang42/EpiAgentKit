#!/usr/bin/env python3
"""Validate a submission-revision state card and reviewer-response closure."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ALLOWED_REVIEW_STATUSES = {
    "pending",
    "modified_pending_validation",
    "closed",
    "needs_user_decision",
}
REQUIRED_LISTS = ("input_candidates", "allowed_scope", "forbidden_scope", "pending_materials")
REQUIRED_DELIVERABLES = ("clean", "marked", "response")
INTERACTION_BOOLEAN_FIELDS = ("answer_only", "create_document", "one_issue_at_a_time")
INTERACTION_ENUMS = {
    "response_style": {"direct", "default"},
    "highlight_policy": {"specified_items_only", "all_changes", "none"},
}


def make_finding(
    level: str,
    rule: str,
    evidence: str,
    impact: str,
    action: str,
) -> dict[str, str]:
    return {
        "level": level,
        "rule": rule,
        "evidence": evidence,
        "impact": impact,
        "action": action,
    }


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _locked_value(entry: Any) -> Any:
    return entry.get("value") if isinstance(entry, dict) else None


def _approved_supersedes(state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    supersedes = state.get("supersedes")
    supersedes = supersedes if isinstance(supersedes, list) else []
    return {
        item.get("key"): item
        for item in supersedes
        if isinstance(item, dict)
        and _nonempty(item.get("key"))
        and _nonempty(item.get("source"))
        and _nonempty(item.get("reason"))
    }


def validate_state(
    state: dict[str, Any],
    previous: dict[str, Any] | None = None,
    *,
    signoff: bool = False,
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    if state.get("schema_version") != 1:
        findings.append(
            make_finding(
                "ERROR",
                "state.schema",
                "schema_version",
                "The revision record cannot be interpreted reliably.",
                "Set schema_version to 1 and validate the state card again.",
            )
        )

    for key in ("round", "format_contract"):
        if not _nonempty(state.get(key)):
            findings.append(
                make_finding(
                    "ERROR",
                    "state.required_field",
                    key,
                    "The active revision contract is incomplete.",
                    f"Record a non-empty {key} before editing.",
                )
            )

    for key in REQUIRED_LISTS:
        value = state.get(key)
        if not isinstance(value, list) or not all(_nonempty(item) for item in value):
            findings.append(
                make_finding(
                    "ERROR",
                    "state.required_list",
                    key,
                    "The revision scope or input set is not machine-checkable.",
                    f"Record {key} as a list of non-empty strings.",
                )
            )

    interaction = state.get("interaction_contract")
    if interaction is not None:
        if not isinstance(interaction, dict):
            findings.append(
                make_finding(
                    "ERROR",
                    "interaction.invalid",
                    "interaction_contract",
                    "Persistent user instructions are not machine-checkable.",
                    "Record interaction_contract as an object or omit it for a single-turn task.",
                )
            )
            interaction = {}
        for key in INTERACTION_BOOLEAN_FIELDS:
            if not isinstance(interaction.get(key), bool):
                findings.append(
                    make_finding(
                        "ERROR",
                        "interaction.required_boolean",
                        f"interaction_contract.{key}",
                        "A persistent interaction instruction is missing or ambiguous.",
                        f"Record {key} as true or false.",
                    )
                )
        for key, allowed_values in INTERACTION_ENUMS.items():
            if interaction.get(key) not in allowed_values:
                findings.append(
                    make_finding(
                        "ERROR",
                        "interaction.invalid_value",
                        f"interaction_contract.{key}",
                        "A persistent interaction instruction uses an unsupported value.",
                        f"Use one of: {', '.join(sorted(allowed_values))}.",
                    )
                )
        if interaction.get("answer_only") is True and interaction.get("create_document") is True:
            findings.append(
                make_finding(
                    "ERROR",
                    "interaction.conflict",
                    "answer_only/create_document",
                    "The state simultaneously forbids and requires document creation.",
                    "Resolve the user instruction before continuing.",
                )
            )

    candidates = state.get("input_candidates")
    selected = state.get("selected_input")
    if isinstance(candidates, list) and candidates:
        if len(candidates) > 1 and not _nonempty(selected):
            findings.append(
                make_finding(
                    "ERROR",
                    "input.ambiguous",
                    "input_candidates",
                    "More than one plausible current manuscript exists.",
                    "Stop automatic selection and ask the user to choose one input.",
                )
            )
        elif _nonempty(selected) and selected not in candidates:
            findings.append(
                make_finding(
                    "ERROR",
                    "input.selection_invalid",
                    "selected_input",
                    "The chosen manuscript is not one of the recorded candidates.",
                    "Select exactly one recorded candidate or correct the candidate list.",
                )
            )
    elif isinstance(candidates, list):
        findings.append(
            make_finding(
                "ERROR",
                "input.missing",
                "input_candidates",
                "No manuscript input has been recorded.",
                "Record the exact candidate path before editing.",
            )
        )

    allowed = state.get("allowed_scope")
    forbidden = state.get("forbidden_scope")
    if isinstance(allowed, list) and isinstance(forbidden, list):
        overlap = sorted(set(allowed) & set(forbidden))
        if overlap:
            findings.append(
                make_finding(
                    "ERROR",
                    "scope.conflict",
                    ", ".join(overlap),
                    "The same target is both allowed and forbidden.",
                    "Resolve the scope conflict before editing.",
                )
            )

    deliverables = state.get("deliverables")
    if not isinstance(deliverables, dict):
        findings.append(
            make_finding(
                "ERROR",
                "deliverables.missing",
                "deliverables",
                "The current submission set is undefined.",
                "Record stable semantic paths for clean, marked, and response files.",
            )
        )
    else:
        for key in REQUIRED_DELIVERABLES:
            if not _nonempty(deliverables.get(key)):
                findings.append(
                    make_finding(
                        "ERROR",
                        "deliverables.required",
                        f"deliverables.{key}",
                        "The current submission set is incomplete.",
                        f"Record the stable {key} deliverable path.",
                    )
                )

    locked = state.get("locked_decisions")
    if not isinstance(locked, dict):
        findings.append(
            make_finding(
                "ERROR",
                "decisions.missing",
                "locked_decisions",
                "User-corrected definitions cannot be protected across rounds.",
                "Record locked_decisions as an object; use an empty object if none exist.",
            )
        )
        locked = {}
    else:
        for key, entry in locked.items():
            if not isinstance(entry, dict) or "value" not in entry or not _nonempty(entry.get("source")):
                findings.append(
                    make_finding(
                        "ERROR",
                        "decisions.invalid",
                        f"locked_decisions.{key}",
                        "A locked decision lacks a value or traceable source.",
                        "Record value and source for the locked decision.",
                    )
                )

    if previous is not None:
        approved = _approved_supersedes(state)
        previous_locked = previous.get("locked_decisions")
        previous_locked = previous_locked if isinstance(previous_locked, dict) else {}
        for key, old_entry in previous_locked.items():
            new_entry = locked.get(key)
            if new_entry is None:
                findings.append(
                    make_finding(
                        "ERROR",
                        "decisions.dropped",
                        f"locked_decisions.{key}",
                        "A decision locked in an earlier round disappeared.",
                        "Restore it or record an explicit supersedes entry from the user.",
                    )
                )
                continue
            if _locked_value(new_entry) != _locked_value(old_entry):
                override = approved.get(key)
                if not override or override.get("previous_value") != _locked_value(old_entry) or override.get("new_value") != _locked_value(new_entry):
                    findings.append(
                        make_finding(
                            "ERROR",
                            "decisions.silent_change",
                            f"locked_decisions.{key}",
                            "A locked definition changed without a traceable user correction.",
                            "Restore the previous value or record the explicit superseding decision.",
                        )
                    )

        previous_interaction = previous.get("interaction_contract")
        if isinstance(previous_interaction, dict):
            if not isinstance(interaction, dict) or not interaction:
                findings.append(
                    make_finding(
                        "ERROR",
                        "interaction.dropped",
                        "interaction_contract",
                        "User instructions locked in an earlier round disappeared.",
                        "Restore the interaction contract or record explicit superseding instructions.",
                    )
                )
            else:
                for key, old_value in previous_interaction.items():
                    new_value = interaction.get(key)
                    if new_value == old_value:
                        continue
                    override = approved.get(f"interaction_contract.{key}")
                    if not override or override.get("previous_value") != old_value or override.get("new_value") != new_value:
                        findings.append(
                            make_finding(
                                "ERROR",
                                "interaction.silent_change",
                                f"interaction_contract.{key}",
                                "A persistent user instruction changed without an explicit replacement.",
                                "Restore it or record a traceable supersedes entry from the user.",
                            )
                        )

    comments = state.get("review_comments", [])
    if not isinstance(comments, list):
        findings.append(
            make_finding(
                "ERROR",
                "review.invalid",
                "review_comments",
                "Reviewer-comment closure cannot be audited.",
                "Record review_comments as a list.",
            )
        )
        comments = []

    seen_ids: set[str] = set()
    for index, item in enumerate(comments):
        location = f"review_comments[{index}]"
        if not isinstance(item, dict) or not _nonempty(item.get("id")):
            findings.append(
                make_finding(
                    "ERROR",
                    "review.id_missing",
                    location,
                    "A reviewer point cannot be traced across artifacts.",
                    "Assign a stable unique comment id.",
                )
            )
            continue
        comment_id = item["id"]
        if comment_id in seen_ids:
            findings.append(
                make_finding(
                    "ERROR",
                    "review.id_duplicate",
                    comment_id,
                    "Two reviewer points share one identifier.",
                    "Give every reviewer point a unique id.",
                )
            )
        seen_ids.add(comment_id)
        status = item.get("status")
        if status not in ALLOWED_REVIEW_STATUSES:
            findings.append(
                make_finding(
                    "ERROR",
                    "review.status_invalid",
                    comment_id,
                    "The reviewer point has no auditable workflow state.",
                    "Use pending, modified_pending_validation, closed, or needs_user_decision.",
                )
            )
            continue
        if status == "closed":
            for key in ("action", "location", "before_after", "response"):
                if not _nonempty(item.get(key)):
                    findings.append(
                        make_finding(
                            "ERROR",
                            "review.closure_incomplete",
                            f"{comment_id}.{key}",
                            "The response claims closure without a traceable manuscript action.",
                            f"Record the {key} before marking the point closed.",
                        )
                    )
            evidence = item.get("evidence")
            if not isinstance(evidence, list) or not evidence or not all(_nonempty(value) for value in evidence):
                findings.append(
                    make_finding(
                        "ERROR",
                        "review.closure_incomplete",
                        f"{comment_id}.evidence",
                        "The closed response has no verifiable evidence source.",
                        "Record one or more evidence sources or locations.",
                    )
                )
        elif signoff:
            findings.append(
                make_finding(
                    "ERROR",
                    "review.unclosed",
                    f"{comment_id}:{status}",
                    "The submission response is not fully closed.",
                    "Complete validation or obtain the required user decision before sign-off.",
                )
            )
        else:
            findings.append(
                make_finding(
                    "WARN",
                    "review.open",
                    f"{comment_id}:{status}",
                    "The reviewer point remains open.",
                    "Carry it forward in the active state card and do not claim completion.",
                )
            )

    return findings


def load_state(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("revision state root must be an object")
    return payload


def validate_state_file(
    path: Path,
    previous_path: Path | None = None,
    *,
    signoff: bool = False,
) -> list[dict[str, str]]:
    state = load_state(path)
    previous = load_state(previous_path) if previous_path else None
    return validate_state(state, previous, signoff=signoff)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("state", type=Path)
    parser.add_argument("--previous", type=Path)
    parser.add_argument("--signoff", action="store_true")
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        findings = validate_state_file(args.state, args.previous, signoff=args.signoff)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        findings = [
            make_finding(
                "ERROR",
                "state.unreadable",
                f"{args.state}:{type(error).__name__}",
                "The revision state card cannot be read safely.",
                "Repair the JSON file before continuing.",
            )
        ]

    errors = [item for item in findings if item["level"] == "ERROR"]
    if args.as_json:
        print(json.dumps({"ok": not errors, "findings": findings}, ensure_ascii=False, indent=2))
    else:
        for item in findings:
            print(f"[{item['level']}] {item['rule']}: {item['evidence']}")
            print(f"  Impact: {item['impact']}")
            print(f"  Action: {item['action']}")
        print(f"Revision state {'passed' if not errors else 'failed'}: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
