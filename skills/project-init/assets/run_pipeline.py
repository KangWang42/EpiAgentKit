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

# List preparation and formal analysis separately. The readiness gate runs before analysis.
preparation_scripts = [
    ROOT / "02_code" / "01_data_cleaning.py",
]
analysis_scripts: list[Path] = []
scripts = [*preparation_scripts, *analysis_scripts]
readiness_helper = ROOT / "02_code" / "vendored" / "data_readiness.py"
missing_scripts = [path.relative_to(ROOT).as_posix() for path in scripts if not path.is_file()]
if analysis_scripts and not readiness_helper.is_file():
    missing_scripts.append(readiness_helper.relative_to(ROOT).as_posix())
if missing_scripts:
    raise SystemExit(f"formal analysis scripts are missing: {', '.join(missing_scripts)}")

started = datetime.now().astimezone()
run_id = f"{started.strftime('%Y%m%dT%H%M%S%z')}_{os.getpid()}"
runs = ROOT / "results" / "runs"
runs.mkdir(parents=True, exist_ok=True)
log_path = runs / f"{run_id}.log"
environment_path = runs / f"{run_id}-environment.txt"
environment = dict(os.environ)
environment["EPI_RUN_ID"] = run_id
exit_code = 0


def run_step(
    script: Path,
    log,
    *,
    arguments: list[str] | None = None,
    label: str | None = None,
) -> int:
    relative = label or script.relative_to(ROOT).as_posix()
    log.write(f"\n===== {relative} =====\n")
    completed = subprocess.run(
        [sys.executable, str(script), *(arguments or [])],
        cwd=ROOT,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    log.write(completed.stdout)
    return completed.returncode


with log_path.open("w", encoding="utf-8") as log:
    for script in preparation_scripts:
        exit_code = run_step(script, log)
        if exit_code:
            break
    if not exit_code and analysis_scripts:
        exit_code = run_step(
            readiness_helper,
            log,
            arguments=["--check"],
            label="data readiness gate",
        )
    if not exit_code:
        for script in analysis_scripts:
            exit_code = run_step(script, log)
            if exit_code:
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
