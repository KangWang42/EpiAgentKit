#!/usr/bin/env bash
# PostToolUse(Edit|Write|apply_patch|write_file|edit_file|...)：聚合 R 语法与文本规范检查，客户端只注册一个 hook。
hook_dir=$(cd "$(dirname "$0")" && { pwd -W 2>/dev/null || pwd; })
client=$(printf '%s' "${EPIAGENTKIT_HOOK_CLIENT:-${EPICLAUDE_HOOK_CLIENT:-claude}}" | tr '[:upper:]' '[:lower:]')
payload=$(cat)

run_check() {
  local script="$1" out rc
  out=$(printf '%s' "$payload" | bash "$hook_dir/$script" 2>&1)
  rc=$?
  if [ "$rc" -ne 0 ]; then
    [ -n "$out" ] && printf '%s\n' "$out" >&2
    return "$rc"
  fi
  return 0
}

run_check "check_r_syntax.sh" || exit $?
run_check "scan_ai_trace.sh" || exit $?
if [ "$client" = "agy" ]; then
  printf '{}\n'
fi
exit 0
