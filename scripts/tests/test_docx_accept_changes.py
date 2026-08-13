from __future__ import annotations

import importlib.util
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills" / "docx" / "scripts" / "accept_changes.py"


def load_module():
    spec = importlib.util.spec_from_file_location("epiagentkit_docx_accept", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def document_xml(tracked: bool) -> str:
    content = (
        '<w:ins w:id="1" w:author="Reviewer"><w:r><w:t>new</w:t></w:r></w:ins>'
        if tracked
        else "<w:r><w:t>clean</w:t></w:r>"
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body><w:p>{content}</w:p></w:body></w:document>"
    )


def write_docx(path: Path, tracked: bool) -> None:
    with zipfile.ZipFile(path, "w") as package:
        package.writestr("word/document.xml", document_xml(tracked))


class DocxAcceptChangesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()

    def test_no_tracked_changes_returns_without_libreoffice(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.docx"
            output = root / "output.docx"
            write_docx(source, tracked=False)
            with patch.object(self.module.shutil, "which") as which:
                result = self.module.accept_changes(source, output, root)
            self.assertEqual(result["status"], "not_needed")
            which.assert_not_called()
            self.assertFalse(output.exists())

    def test_missing_libreoffice_preserves_input_and_writes_no_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.docx"
            output = root / "output.docx"
            write_docx(source, tracked=True)
            before = source.read_bytes()
            with patch.object(self.module.shutil, "which", return_value=None):
                result = self.module.accept_changes(source, output, root)
            self.assertEqual(result["status"], "unavailable")
            self.assertEqual(source.read_bytes(), before)
            self.assertFalse(output.exists())

    def test_timeout_is_failure_and_does_not_write_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.docx"
            output = root / "output.docx"
            write_docx(source, tracked=True)
            with patch.object(self.module.shutil, "which", return_value="soffice"), patch.object(
                self.module, "initialize_profile", return_value=(True, "")
            ), patch.object(self.module, "install_macro"), patch.object(
                self.module.subprocess, "run", side_effect=subprocess.TimeoutExpired("soffice", 60)
            ):
                result = self.module.accept_changes(source, output, root)
            self.assertEqual(result["status"], "error")
            self.assertIn("超时", result["message"])
            self.assertFalse(output.exists())

    def test_residual_changes_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.docx"
            output = root / "output.docx"
            write_docx(source, tracked=True)
            completed = subprocess.CompletedProcess(["soffice"], 0, "", "")
            with patch.object(self.module.shutil, "which", return_value="soffice"), patch.object(
                self.module, "initialize_profile", return_value=(True, "")
            ), patch.object(self.module, "install_macro"), patch.object(
                self.module.subprocess, "run", return_value=completed
            ):
                result = self.module.accept_changes(source, output, root)
            self.assertEqual(result["status"], "error")
            self.assertIn("仍含修订标记", result["message"])
            self.assertFalse(output.exists())

    def test_success_writes_only_verified_clean_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.docx"
            output = root / "output.docx"
            write_docx(source, tracked=True)
            completed = subprocess.CompletedProcess(["soffice"], 0, "", "")

            def simulate_accept(command, **kwargs):
                candidate = Path(command[-1])
                write_docx(candidate, tracked=False)
                return completed

            with patch.object(self.module.shutil, "which", return_value="soffice"), patch.object(
                self.module, "initialize_profile", return_value=(True, "")
            ), patch.object(self.module, "install_macro"), patch.object(
                self.module.subprocess, "run", side_effect=simulate_accept
            ):
                result = self.module.accept_changes(source, output, root)
            self.assertEqual(result["status"], "success")
            self.assertEqual(self.module.tracked_change_locations(output), [])
            self.assertNotEqual(source.read_bytes(), output.read_bytes())

    def test_existing_output_is_preserved_without_replace(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.docx"
            output = root / "output.docx"
            write_docx(source, tracked=True)
            output.write_bytes(b"keep")
            result = self.module.accept_changes(source, output, root)
            self.assertEqual(result["status"], "error")
            self.assertEqual(output.read_bytes(), b"keep")

    def test_macro_module_is_registered_in_isolated_profile(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            profile = Path(directory) / "profile"
            self.module.install_macro(profile)
            standard = profile / "user" / "basic" / "Standard"
            self.assertIn(
                "AcceptAllTrackedChanges",
                (standard / "Module1.xba").read_text(encoding="utf-8"),
            )
            self.assertIn(
                'library:name="Module1"',
                (standard / "script.xlb").read_text(encoding="utf-8"),
            )

    def test_extended_revision_markers_are_detected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "extended.docx"
            xml = (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
                'xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml">'
                '<w:body><w:p><w:customXmlInsRangeStart w:id="1"/>'
                '<w14:conflictIns><w:r><w:t>x</w:t></w:r></w14:conflictIns>'
                '</w:p></w:body></w:document>'
            )
            with zipfile.ZipFile(source, "w") as package:
                package.writestr("word/document.xml", xml)
            locations = self.module.tracked_change_locations(source)
            self.assertEqual(
                locations,
                [
                    "word/document.xml:customXmlInsRangeStart",
                    "word/document.xml:conflictIns",
                ],
            )


if __name__ == "__main__":
    unittest.main()
