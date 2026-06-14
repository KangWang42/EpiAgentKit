#!/usr/bin/env bash
# PreToolUse(Bash)：拦截"多行 Rscript -e"——本环境用 -e 传多行 R 脚本会 segfault。
# 多行 R 一律写成 .R 文件再 Rscript 文件.R 跑；-e 仅用于一行小命令（放行）。
cmd=$(python -c 'import sys,json
try: d=json.load(sys.stdin)
except Exception: d={}
print((d.get("tool_input") or {}).get("command") or "")' 2>/dev/null)

has_e=0; multiline=0
case "$cmd" in *Rscript*-e*) has_e=1 ;; esac
case "$cmd" in *$'\n'*) multiline=1 ;; esac

if [ "$has_e" = 1 ] && [ "$multiline" = 1 ]; then
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"本环境用 Rscript -e 传多行脚本会 segfault（非脚本本身问题）。请把脚本写成 .R 文件再用 Rscript 文件.R 运行；-e 仅用于一行小命令。"}}\n'
fi
exit 0
