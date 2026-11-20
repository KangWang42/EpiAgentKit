#!/usr/bin/env bash
# PostToolUse(Bash|run_command)：聚合图件与结果格式检查，只向客户端发送一条非阻断提醒。
hook_dir=$(cd "$(dirname "$0")" && { pwd -W 2>/dev/null || pwd; })
client=$(printf '%s' "${EPIAGENTKIT_HOOK_CLIENT:-${EPICLAUDE_HOOK_CLIENT:-claude}}" | tr '[:upper:]' '[:lower:]')
payload=""
if [ ! -t 0 ]; then
  payload=$(cat)
fi
if [ -n "$payload" ]; then
  payload_root=$(printf '%s' "$payload" | python -c 'import sys,json
try:
    d=json.load(sys.stdin)
except Exception:
    d={}
if isinstance(d, dict):
    cwd=d.get("cwd")
    if isinstance(cwd, str) and cwd.strip():
        print(cwd.strip())
    elif isinstance(d.get("workspacePaths"), list):
        for entry in d["workspacePaths"]:
            if isinstance(entry, str) and entry.strip():
                print(entry.strip())
                break' 2>/dev/null)
  if [ -n "$payload_root" ]; then
    export EPIAGENTKIT_PROJECT_ROOT="$payload_root"
  fi
fi
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
  exit $?
fi
if [ "$client" = "agy" ]; then
  printf '{}\n'
fi
exit 0
