#!/usr/bin/env python3
"""Emit a successful, client-specific PostToolUse notice."""

from __future__ import annotations

import json
import os
import sys


def main() -> int:
    message = sys.stdin.read().strip()
    client = os.environ.get(
        "EPIAGENTKIT_HOOK_CLIENT",
        os.environ.get("EPICLAUDE_HOOK_CLIENT", "claude"),
    ).lower()
    if client == "codex":
        payload = {"systemMessage": message}
    else:
        payload = {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": message,
            }
        }
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
