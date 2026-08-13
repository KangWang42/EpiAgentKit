#!/usr/bin/env python3
"""Accept DOCX tracked changes through an isolated LibreOffice profile."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree


WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
WORD_2010_NS = "http://schemas.microsoft.com/office/word/2010/wordml"
TRACKED_LOCAL_NAMES = {
    "cellDel",
    "cellIns",
    "cellMerge",
    "customXmlDelRangeEnd",
    "customXmlDelRangeStart",
    "customXmlInsRangeEnd",
    "customXmlInsRangeStart",
    "customXmlMoveFromRangeEnd",
    "customXmlMoveFromRangeStart",
    "customXmlMoveToRangeEnd",
    "customXmlMoveToRangeStart",
    "customXmlPrChange",
    "del",
    "ins",
    "moveFrom",
    "moveFromRangeEnd",
    "moveFromRangeStart",
    "moveTo",
    "moveToRangeEnd",
    "moveToRangeStart",
    "numberingChange",
    "pPrChange",
    "rPrChange",
    "sectPrChange",
    "tblGridChange",
    "tblPrChange",
    "tblPrExChange",
    "trPrChange",
    "tcPrChange",
}
TRACKED_TAGS = {
    *(f"{{{WORD_NS}}}{name}" for name in TRACKED_LOCAL_NAMES),
    f"{{{WORD_2010_NS}}}conflictDel",
    f"{{{WORD_2010_NS}}}conflictIns",
}

ACCEPT_CHANGES_MACRO = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE script:module PUBLIC "-//OpenOffice.org//DTD OfficeDocument 1.0//EN" "module.dtd">
<script:module xmlns:script="http://openoffice.org/2000/script" script:name="Module1" script:language="StarBasic">
    Sub AcceptAllTrackedChanges()
        Dim frame As Object
        Dim dispatcher As Object
        frame = ThisComponent.CurrentController.Frame
        dispatcher = createUnoService("com.sun.star.frame.DispatchHelper")
        dispatcher.executeDispatch(frame, ".uno:AcceptAllTrackedChanges", "", 0, Array())
        ThisComponent.store()
        ThisComponent.close(True)
    End Sub
</script:module>"""
SCRIPT_LIBRARY = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE library:library PUBLIC "-//OpenOffice.org//DTD OfficeDocument 1.0//EN" "library.dtd">
<library:library xmlns:library="http://openoffice.org/2000/library" library:name="Standard" library:readonly="false" library:passwordprotected="false">
    <library:element library:name="Module1"/>
</library:library>"""


def tracked_change_locations(path: Path) -> list[str]:
    found: list[str] = []
    with zipfile.ZipFile(path) as package:
        for name in package.namelist():
            if not name.startswith("word/") or not name.endswith(".xml"):
                continue
            try:
                root = ElementTree.fromstring(package.read(name))
            except ElementTree.ParseError as exc:
                raise ValueError(f"无效 XML：{name}：{exc}") from exc
            for node in root.iter():
                if node.tag in TRACKED_TAGS:
                    local_name = node.tag.rsplit("}", 1)[1]
                    found.append(f"{name}:{local_name}")
    return found


def profile_uri(path: Path) -> str:
    return path.resolve().as_uri()


def soffice_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment["SAL_USE_VCLPLUGIN"] = "svp"
    return environment


def initialize_profile(executable: str, profile: Path, timeout: int) -> tuple[bool, str]:
    command = [
        executable,
        f"-env:UserInstallation={profile_uri(profile)}",
        "--headless",
        "--nologo",
        "--nodefault",
        "--nolockcheck",
        "--norestore",
        "--terminate_after_init",
    ]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            env=soffice_environment(),
        )
    except subprocess.TimeoutExpired:
        return False, "LibreOffice 隔离配置初始化超时"
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "未提供错误信息").strip()
        return False, f"LibreOffice 隔离配置初始化失败：{detail}"
    return True, ""


def install_macro(profile: Path) -> None:
    macro_dir = profile / "user" / "basic" / "Standard"
    macro_dir.mkdir(parents=True, exist_ok=True)
    (macro_dir / "Module1.xba").write_text(ACCEPT_CHANGES_MACRO, encoding="utf-8")
    (macro_dir / "script.xlb").write_text(SCRIPT_LIBRARY, encoding="utf-8")


def accept_changes(
    source: Path,
    output: Path,
    work_dir: Path,
    *,
    timeout: int = 60,
    replace: bool = False,
) -> dict[str, object]:
    source = source.resolve()
    output = output.resolve()
    work_dir = work_dir.resolve()

    if not source.is_file() or source.suffix.lower() != ".docx":
        return {"status": "error", "message": "输入必须是现有 DOCX 文件"}
    if source == output:
        return {"status": "error", "message": "输出必须与输入不同，以保留原文件"}
    if output.suffix.lower() != ".docx":
        return {"status": "error", "message": "输出必须使用 .docx 扩展名"}
    if output.exists() and not replace:
        return {"status": "error", "message": "输出已存在；确认后使用 --replace"}
    if not work_dir.is_dir():
        return {"status": "error", "message": "--work-dir 必须是已经建立的 workbench 目录"}
    try:
        before = tracked_change_locations(source)
    except (OSError, zipfile.BadZipFile, ValueError) as exc:
        return {"status": "error", "message": f"无法读取输入 DOCX：{exc}"}
    if not before:
        return {"status": "not_needed", "message": "输入文件没有可接受的修订标记"}

    executable = shutil.which("soffice")
    if not executable:
        return {"status": "unavailable", "message": "未发现兼容的 soffice；未写入输出文件"}

    with tempfile.TemporaryDirectory(prefix="docx-accept-", dir=work_dir) as temporary:
        temporary_path = Path(temporary)
        profile = temporary_path / "profile"
        candidate = temporary_path / source.name
        profile.mkdir()
        ok, message = initialize_profile(executable, profile, min(timeout, 20))
        if not ok:
            return {"status": "error", "message": message}
        install_macro(profile)
        shutil.copy2(source, candidate)
        command = [
            executable,
            f"-env:UserInstallation={profile_uri(profile)}",
            "--headless",
            "--nologo",
            "--nodefault",
            "--nolockcheck",
            "--norestore",
            "vnd.sun.star.script:Standard.Module1.AcceptAllTrackedChanges?language=Basic&location=application",
            str(candidate),
        ]
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
                env=soffice_environment(),
            )
        except subprocess.TimeoutExpired:
            return {"status": "error", "message": "接受修订超时；未写入输出文件"}
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "未提供错误信息").strip()
            return {"status": "error", "message": f"LibreOffice 接受修订失败：{detail}"}
        try:
            remaining = tracked_change_locations(candidate)
        except (OSError, zipfile.BadZipFile, ValueError) as exc:
            return {"status": "error", "message": f"无法核对候选净稿：{exc}"}
        if remaining:
            return {
                "status": "error",
                "message": "候选净稿仍含修订标记；未写入输出文件",
                "remaining": remaining[:20],
            }

        output.parent.mkdir(parents=True, exist_ok=True)
        staging = output.with_name(f".{output.name}.accept.tmp")
        try:
            shutil.copy2(candidate, staging)
            os.replace(staging, output)
        finally:
            staging.unlink(missing_ok=True)
        return {
            "status": "success",
            "input_changes": len(before),
            "remaining_changes": 0,
            "output": str(output),
        }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="使用隔离的 LibreOffice 配置接受 DOCX 修订，不覆盖输入文件"
    )
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--work-dir", required=True, type=Path)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    result = accept_changes(
        args.source,
        args.output,
        args.work_dir,
        timeout=args.timeout,
        replace=args.replace,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] in {"success", "not_needed"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
