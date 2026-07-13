#!/usr/bin/env bash
# PostToolUse(Bash)：聚合图件与结果格式检查，只向客户端发送一条非阻断提醒。
hook_dir=$(cd "$(dirname "$0")" && pwd)
notice=""

collect_notice() {
  local script="$1" out rc
  out=$(EPIAGENTKIT_PLAIN_NOTICE=1 bash "$hook_dir/$script")
  rc=$?
  [ "$rc" -eq 0 ] || return "$rc"
  if [ -n "$out" ]; then
    if [ -n "$notice" ]; then
      notice="$notice"$'\n\n'"$out"
    else
      notice="$out"
    fi
  fi
  return 0
}

collect_notice "fig_selfcheck.sh" || exit $?
collect_notice "check_results_rds.sh" || exit $?

if [ -n "$notice" ]; then
  printf '%s\n' "$notice" | python "$hook_dir/_emit_notice.py"
fi
exit $?
