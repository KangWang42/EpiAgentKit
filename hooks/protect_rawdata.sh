#!/usr/bin/env bash
# PreToolUse(Edit|Write|apply_patch)：拦截可确定解析的原始数据编辑路径。
# 该 hook 不解析任意 shell/Python/PowerShell 代码，不能替代文件权限与任务终检。
hook_dir=$(cd "$(dirname "$0")" && { pwd -W 2>/dev/null || pwd; })
payload=$(cat)
if ! protected=$(printf '%s' "$payload" | python "$hook_dir/_path_guard.py"); then
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"原始数据路径保护规则解析失败。请先修复 hook 或 .epiagentkit-raw-roots，再执行文件修改。"}}\n'
  exit 0
fi
if [ -n "$protected" ]; then
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"目标位于只读原始数据根。请改写派生目录；如原始根声明有误，先核对项目 .epiagentkit-raw-roots。"}}\n'
  exit 0
fi
exit 0
