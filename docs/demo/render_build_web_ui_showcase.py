#!/usr/bin/env python3
"""Render and optionally publish the build-web-ui showcase screenshots."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--publish", action="store_true")
    return parser.parse_args()


def wait_until_ready(url: str, process: subprocess.Popen[bytes]) -> None:
    for _ in range(30):
        if process.poll() is not None:
            raise RuntimeError("Local preview server exited before becoming ready")
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
        except (OSError, urllib.error.URLError):
            time.sleep(0.2)
    raise RuntimeError(f"Local preview server did not become ready: {url}")


def main() -> int:
    args = parse_args()
    repo = Path(__file__).resolve().parents[2]
    runtime = repo / "09_backup/workbench/2026-08-08_2348_slides_maker_ppt_maintenance/runtime"
    audit_script = repo / "skills/build-web-ui/scripts/audit_browser.py"
    output = args.output if args.output.is_absolute() else repo / args.output
    output = output.resolve()
    try:
        output.relative_to(repo)
    except ValueError as error:
        raise RuntimeError(f"Output must stay within the repository: {output}") from error
    if output.exists() and any(output.iterdir()):
        raise RuntimeError(f"Output directory must be absent or empty: {output}")
    output.mkdir(parents=True, exist_ok=True)

    url = f"http://127.0.0.1:{args.port}/docs/showcase/build-web-ui/index.html"
    env = os.environ.copy()
    for name in ("TEMP", "TMP", "TMPDIR"):
        env[name] = str(runtime)
    creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    server_out_path = runtime / "web-showcase-server.out.log"
    server_err_path = runtime / "web-showcase-server.err.log"

    with server_out_path.open("wb") as server_out, server_err_path.open("wb") as server_err:
        server = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "http.server",
                str(args.port),
                "--bind",
                "127.0.0.1",
                "--directory",
                str(repo),
            ],
            cwd=repo,
            env=env,
            stdout=server_out,
            stderr=server_err,
            creationflags=creation_flags,
        )
        try:
            wait_until_ready(url, server)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(audit_script),
                    url,
                    "--output",
                    str(output),
                    "--viewports",
                    "desktop=1440x960,mobile=390x844",
                ],
                cwd=repo,
                env=env,
                check=False,
            )
            if completed.returncode:
                return completed.returncode

            if args.publish:
                report = json.loads((output / "browser-audit.json").read_text(encoding="utf-8"))
                if not report.get("ok"):
                    raise RuntimeError("Browser audit did not pass; refusing to publish screenshots")
                screenshots = {
                    scenario["viewport"]["name"]: scenario["screenshot"]
                    for scenario in report["scenarios"]
                }
                if not {"desktop", "mobile"}.issubset(screenshots):
                    raise RuntimeError("Browser audit lacks desktop or mobile screenshots")
                showcase = repo / "docs/showcase/build-web-ui"
                shutil.copy2(output / screenshots["desktop"], showcase / "desktop.png")
                shutil.copy2(output / screenshots["mobile"], showcase / "mobile.png")
                print(f"published={showcase}")
        finally:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=5)
    return 0


if __name__ == "__main__":
    sys.exit(main())
