#!/usr/bin/env bash
# PostToolUse(Bash)：按项目隔离的内容指纹检测 06_results/ 新写入或修改的 .rds。
hook_dir=$(cd "$(dirname "$0")" && { pwd -W 2>/dev/null || pwd; })
flag=$(python "$hook_dir/_file_state.py" \
  --kind results_rds --root 06_results --extension .rds)

if [ -n "$flag" ]; then
  notice=$({
    echo "检测到 06_results/ 新写入 .rds："
    printf '%s' "$flag" | sed '/^$/d;s/^/  · /'
    echo "→ 仅非表格对象（拟合模型 / ggplot / MCA 等）可用 rds；**表格化数据必须存 .xlsx**（writexl::write_xlsx）。若上述是表格，请改存 xlsx。"
  })
  if [ "${EPIAGENTKIT_PLAIN_NOTICE:-${EPICLAUDE_PLAIN_NOTICE:-0}}" = "1" ]; then
    printf '%s\n' "$notice"
  else
    printf '%s\n' "$notice" | python "$hook_dir/_emit_notice.py"
  fi
  exit $?
fi
exit 0
