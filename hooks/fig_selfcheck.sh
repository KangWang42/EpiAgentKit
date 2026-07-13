#!/usr/bin/env bash
# PostToolUse(Bash)：检测 04_figures/ 新生成或修改的图 → 注入 publication-figures §12ter
# 逐元素自检清单，逼主模型 Read 该图逐条判断。hook 不做视觉判断（命令看不了图），
# 只负责"逮住出图事件 + 强制自检"，判断交给视觉能力强的主模型。
[ -d 04_figures ] || exit 0                       # 无 04_figures（如非项目目录）直接跳过
state_root="${EPIAGENTKIT_STATE_HOME:-${EPICLAUDE_STATE_HOME:-$HOME/.epiagentkit}}"
mkdir -p "$state_root" 2>/dev/null
state="$state_root/.fig_selfcheck_state"          # 已提醒记录（path|mtime），避免重复提醒
touch "$state" 2>/dev/null

new=""
while IFS= read -r img; do
  [ -n "$img" ] || continue
  mt=$(stat -c '%Y' "$img" 2>/dev/null || echo 0)
  key="$img|$mt"
  if ! grep -qF "$key" "$state" 2>/dev/null; then  # 该图此版本未提醒过
    echo "$key" >> "$state"
    new="$new$img"$'\n'
  fi
done < <(find 04_figures -type f \( -iname '*.png' -o -iname '*.pdf' \) -newermt '-120 seconds' 2>/dev/null)

# 控制 state 文件大小
if [ "$(wc -l < "$state" 2>/dev/null || echo 0)" -gt 600 ]; then
  tail -n 300 "$state" > "$state.tmp" 2>/dev/null && mv "$state.tmp" "$state" 2>/dev/null
fi

if [ -n "$new" ]; then
  notice=$({
    echo "检测到新生成/修改的图，按 publication-figures §12ter 逐项自检（先 Read 该 PNG/PDF，逐条判，任一不过=回代码层改重出）："
    printf '%s' "$new" | sed '/^$/d;s/^/  · /'
    echo "① 图例/标签/注释不遮挡任何数据（线/点/柱/误差棒）；遮挡即不合格"
    echo "② 比例尺寸合适，无大片空边、无元素被裁切（轴/标题/图例/刻度完整）"
    echo "③ 每个元素清晰可读（嵌入尺寸下字号够大）"
    echo "④ 数值可溯源不硬编码、与 results.yaml 一致；无统计假象（全同值/恒 ±0.707 等）"
    echo "⑤ 图型匹配数据、与同篇其它图 theme/配色/布局一致、多结局不漏"
  })
  if [ "${EPIAGENTKIT_PLAIN_NOTICE:-${EPICLAUDE_PLAIN_NOTICE:-0}}" = "1" ]; then
    printf '%s\n' "$notice"
  else
    printf '%s\n' "$notice" | python "$(dirname "$0")/_emit_notice.py"
  fi
  exit $?
fi
exit 0
