#!/usr/bin/env python3
"""Report high-confidence assistant/process traces and disallowed emoji."""

from __future__ import annotations

import re
import sys
from pathlib import Path


TRACE_PATTERNS = (
    (re.compile(r"作为(?:一个)?\s*(?:AI|人工智能)(?:助手|助理|模型)?", re.IGNORECASE), "助手自述"),
    (re.compile(r"以下是我(?:为你|替你)?(?:生成|整理|撰写|改写)的", re.IGNORECASE), "生成过程"),
    (re.compile(r"(?:希望|盼望)(?:以上|这些|这)(?:内容)?(?:能|可以)(?:够)?帮到你"), "对话式收尾"),
    (re.compile(r"如有需要[，,]?我(?:还)?可以(?:继续)?(?:帮你|为你)"), "助手式邀约"),
    (re.compile(r"\bas an AI (?:assistant|model)\b", re.IGNORECASE), "assistant self-reference"),
    (re.compile(r"\bI hope (?:this|that) helps\b", re.IGNORECASE), "assistant sign-off"),
    (re.compile(r"\bhere(?:'s| is) (?:the|a) .* I (?:generated|wrote|rewrote) for you\b", re.IGNORECASE), "generation process"),
)
SCIENTIFIC_SYMBOLS = set("→↔↑↓±×≥≤℃")
EMOJI_RANGES = (
    (0x1F1E6, 0x1F1FF),
    (0x1F300, 0x1FAFF),
    (0x2600, 0x26FF),
    (0x2700, 0x27BF),
    (0x2B00, 0x2BFF),
)


def is_emoji(character: str) -> bool:
    if character in SCIENTIFIC_SYMBOLS:
        return False
    codepoint = ord(character)
    return any(start <= codepoint <= end for start, end in EMOJI_RANGES)


def allowed_backlog_check(path: Path, line: str, position: int) -> bool:
    if path.name.casefold() != "backlog.md" or line[position] != "✅":
        return False
    pipes = [index for index, character in enumerate(line) if character == "|"]
    if len(pipes) < 5 or not (pipes[3] < position < pipes[4]):
        return False
    status = line[pipes[3] + 1 : pipes[4]]
    return bool(re.fullmatch(r"\s*✅\s+\d{4}-\d{2}-\d{2}\s*", status))


def scan(path: Path) -> list[str]:
    issues: list[str] = []
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    for line_number, line in enumerate(text.splitlines(), start=1):
        for pattern, label in TRACE_PATTERNS:
            if pattern.search(line):
                issues.append(f"{path}:{line_number}: 过程痕迹({label})")
        seen_emoji: set[str] = set()
        for position, character in enumerate(line):
            if (
                is_emoji(character)
                and not allowed_backlog_check(path, line, position)
                and character not in seen_emoji
            ):
                issues.append(
                    f"{path}:{line_number}: 禁止字符(U+{ord(character):04X})"
                )
                seen_emoji.add(character)
    return issues


def main() -> int:
    if len(sys.argv) != 2:
        return 0
    path = Path(sys.argv[1])
    if not path.is_file():
        return 0
    for issue in scan(path):
        print(issue)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
