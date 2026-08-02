#!/usr/bin/env python3
"""Run the project Python scripts in order and save an automatic run record."""

from __future__ import annotations

from datetime import datetime
from hashlib import sha256
from pathlib import Path
import json
import os
import platform
import subprocess
import sys


ROOT = Path(__file__).resolve().parent
if not (ROOT / "02_code").is_dir():
    raise SystemExit("run_pipeline.py must be located and run at the project root")

started = datetime.now().astimezone()
run_id = f"{started.strftime('%Y%m%dT%H%M%S%z')}_{os.getpid()}"
runs = ROOT / "results" / "runs"
runs.mkdir(parents=True, exist_ok=True)
log_path = runs / f"{run_id}.log"
environment_path = runs / f"{run_id}-environment.txt"
scripts = sorted((ROOT / "02_code").glob("[0-9][0-9]_*.py"))
environment = dict(os.environ)
environment["EPI_RUN_ID"] = run_id
exit_code = 0

with log_path.open("w", encoding="utf-8") as log:
    for script in scripts:
        relative = script.relative_to(ROOT).as_posix()
        log.write(f"\n===== {relative} =====\n")
        completed = subprocess.run(
            [sys.executable, str(script)],
            cwd=ROOT,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        log.write(completed.stdout)
        if completed.returncode:
            exit_code = completed.returncode
            break

environment_lines = [
    f"python={sys.version.replace(chr(10), ' ')}",
    f"executable={sys.executable}",
    f"platform={platform.platform()}",
]
for lock_name in ("requirements.txt", "pyproject.toml", "uv.lock", "poetry.lock"):
    lock_path = ROOT / lock_name
    if lock_path.is_file():
        environment_lines.append(f"declared_dependency_file={lock_name}")
environment_path.write_text("\n".join(environment_lines) + "\n", encoding="utf-8")

output_roots = [ROOT / name for name in ("results", "03_tables", "04_figures", "paper", "05_reports")]
files: dict[str, str] = {}
for output_root in output_roots:
    if not output_root.is_dir():
        continue
    for path in output_root.rglob("*"):
        if path.is_file() and runs not in path.parents:
            files[path.relative_to(ROOT).as_posix()] = sha256(path.read_bytes()).hexdigest()

run_record = {
    "run_id": run_id,
    "started_at": started.isoformat(timespec="seconds"),
    "finished_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    "status": "success" if exit_code == 0 else "failed",
    "exit_code": exit_code,
    "command": f"{Path(sys.executable).name} run_pipeline.py",
    "scripts": [path.relative_to(ROOT).as_posix() for path in scripts],
    "log": log_path.relative_to(ROOT).as_posix(),
    "environment": environment_path.relative_to(ROOT).as_posix(),
    "hash_algorithm": "sha256",
    "files": files,
}
record_text = json.dumps(run_record, ensure_ascii=False, indent=2) + "\n"
(runs / f"{run_id}.json").write_text(record_text, encoding="utf-8")
latest_tmp = runs / ".latest.json.tmp"
latest_tmp.write_text(record_text, encoding="utf-8")
os.replace(latest_tmp, runs / "latest.json")

if exit_code:
    raise SystemExit(f"project scripts failed; inspect {log_path.relative_to(ROOT)}")
print(f"project scripts completed; run ID: {run_id}")
