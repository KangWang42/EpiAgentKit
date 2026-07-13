#!/usr/bin/env bash
# PostToolUse(Bash)：检测 06_results/ 新写入的 .rds，提醒"表格化数据应存 xlsx，rds 仅限非表格对象"。
[ -d 06_results ] || exit 0
state_root="${EPIAGENTKIT_STATE_HOME:-${EPICLAUDE_STATE_HOME:-$HOME/.epiagentkit}}"
mkdir -p "$state_root" 2>/dev/null
state="$state_root/.rds_reminded"
touch "$state" 2>/dev/null
flag=""
while IFS= read -r f; do
  [ -n "$f" ] || continue
  mt=$(stat -c '%Y' "$f" 2>/dev/null || echo 0)
  key="$f|$mt"
  grep -qF "$key" "$state" 2>/dev/null || { echo "$key" >> "$state"; flag="$flag$f"$'\n'; }
done < <(find 06_results -type f -iname '*.rds' -newermt '-120 seconds' 2>/dev/null)

if [ -n "$flag" ]; then
  notice=$({
    echo "检测到 06_results/ 新写入 .rds："
    printf '%s' "$flag" | sed '/^$/d;s/^/  · /'
    echo "→ 仅非表格对象（拟合模型 / ggplot / MCA 等）可用 rds；**表格化数据必须存 .xlsx**（writexl::write_xlsx）。若上述是表格，请改存 xlsx。"
  })
  if [ "${EPIAGENTKIT_PLAIN_NOTICE:-${EPICLAUDE_PLAIN_NOTICE:-0}}" = "1" ]; then
    printf '%s\n' "$notice"
  else
    printf '%s\n' "$notice" | python "$(dirname "$0")/_emit_notice.py"
  fi
  exit $?
fi
exit 0
