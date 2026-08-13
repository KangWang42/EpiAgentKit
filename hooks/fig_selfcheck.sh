#!/usr/bin/env bash
# PostToolUse(Bash)：按项目隔离的内容指纹检测 04_figures/ 新生成或修改的图。
# hook 只提示本次修改的最少检查，不把预览保存升级为完整交付检查。
hook_dir=$(cd "$(dirname "$0")" && pwd)
new=$(python "$hook_dir/_file_state.py" \
  --kind figures --root 04_figures --extension .png --extension .pdf)

if [ -n "$new" ]; then
  notice=$({
    echo "检测到新生成/修改的图："
    printf '%s' "$new" | sed '/^$/d;s/^/  · /'
    echo "只检查本次修改可能造成的错误：局部改图核对目标变化、其余内容未被误改，以及实际使用该图的成品已更新；无关检查不执行。"
  })
  if [ "${EPIAGENTKIT_PLAIN_NOTICE:-${EPICLAUDE_PLAIN_NOTICE:-0}}" = "1" ]; then
    printf '%s\n' "$notice"
  else
    printf '%s\n' "$notice" | python "$(dirname "$0")/_emit_notice.py"
  fi
  exit $?
fi
exit 0
