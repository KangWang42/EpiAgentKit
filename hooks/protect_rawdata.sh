#!/usr/bin/env bash
# PreToolUse(Edit|Write|apply_patch)：拦截对 01_data/rawdata 原始数据的修改（EpiAgentKit 红线）。
source "$(dirname "$0")/_resolve_path.sh"
while IFS= read -r f; do
  fn="${f//\\//}"
  case "$fn" in
    01_data/rawdata/*|rawdata/*|*/01_data/rawdata/*|*/rawdata/*)
      printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"01_data/rawdata 是只读原始数据，禁止修改。如确需变更请改派生数据或先与用户确认。"}}\n'
      exit 0
      ;;
  esac
done <<< "$files"
exit 0
