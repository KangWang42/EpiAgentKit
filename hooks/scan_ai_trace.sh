#!/usr/bin/env bash
# PostToolUse(Edit|Write|apply_patch)：扫文本里的高确定性助手口吻、过程痕迹与明确 emoji。
# 科研符号 → ↔ ↑ ↓ ± × ≥ ≤ ℃ 允许；✅ 仅允许在 BACKLOG 状态列。
source "$(dirname "$0")/_resolve_path.sh"
hook_dir=$(cd "$(dirname "$0")" && pwd)
while IFS= read -r f; do
  fn="${f//\\//}"
  case "$fn" in
    */.claude/*|*/.codex/*|*/.agents/*) continue ;;
  esac
  case "$fn" in
    *.md|*.R|*.r|*.txt|*.csv|*.yaml|*.yml|*.py)
      [ -f "$f" ] || continue
      issues=$(python "$hook_dir/_scan_text.py" "$f")
      if [ -n "$issues" ]; then
        echo "检测到助手口吻、过程痕迹或禁止字符：" >&2
        printf '%s\n' "$issues" >&2
        exit 2
      fi
      ;;
  esac
done <<< "$files"
exit 0
