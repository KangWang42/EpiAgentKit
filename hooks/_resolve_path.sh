# 由各 hook source：把目标文件路径解析到 $files（每行一个）与兼容变量 $f/$fn。
# Claude 编辑工具提供 file_path；Codex apply_patch 把补丁放在 tool_input.command；
# Antigravity (agy) 提供 toolCall.args.Path / TargetFile，并在 cwd/workspacePaths 传入工作区路径。
files="${CLAUDE_TOOL_FILE_PATH:-}"
if [ -z "$files" ]; then
  files=$(python -c 'import os,sys,json,re
from pathlib import Path
try:
    d=json.load(sys.stdin)
except Exception:
    d={}
if not isinstance(d, dict):
    d={}
ti=d.get("tool_input") or {}
tr=d.get("tool_response") or {}
if not isinstance(ti, dict):
    ti={}
if not isinstance(tr, dict):
    tr={}
paths=[]
direct=ti.get("file_path") or tr.get("filePath")
if direct:
    paths.append(str(direct))
command=ti.get("command") or ""
paths.extend(re.findall(r"^\*\*\* (?:Add|Update|Delete) File: (.+)$", command, re.M))
tc=d.get("toolCall") or {}
if isinstance(tc, dict):
    args=tc.get("args") or {}
    if isinstance(args, dict):
        for key in ("Path", "path", "TargetFile", "target_file", "file_path"):
            val=args.get(key)
            if isinstance(val, str) and val.strip():
                paths.append(val)
base=""
cwd=d.get("cwd")
if isinstance(cwd, str) and cwd.strip():
    base=cwd.strip()
elif isinstance(d.get("workspacePaths"), list):
    for entry in d["workspacePaths"]:
        if isinstance(entry, str) and entry.strip():
            base=entry.strip()
            break
resolved=[]
for raw in dict.fromkeys(paths):
    p=Path(raw)
    if base and not p.is_absolute():
        resolved.append(str(Path(base) / p))
    else:
        resolved.append(raw)
print("\n".join(resolved))' 2>/dev/null)
fi
f=$(printf '%s\n' "$files" | sed -n '1p')
fn="${f//\\//}"   # 反斜杠归一为正斜杠，便于匹配
