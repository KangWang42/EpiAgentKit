from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from openpyxl import Workbook


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills" / "xlsx" / "scripts" / "recalc.py"


def load_recalc_module():
    spec = importlib.util.spec_from_file_location("epiagentkit_xlsx_recalc", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class XlsxRecalculationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_recalc_module()

    def workbook(self, path: Path, formula: bool = False, hyperlink: bool = False) -> None:
        workbook = Workbook()
        sheet = workbook.active
        sheet["A1"] = 2
        sheet["A2"] = 3
        sheet["A3"] = "=SUM(A1:A2)" if formula else 5
        if hyperlink:
            sheet["B1"] = "项目主页"
            sheet["B1"].hyperlink = "https://example.org/project"
        workbook.save(path)

    def test_no_formula_returns_without_libreoffice_or_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.xlsx"
            output = root / "output.xlsx"
            self.workbook(source)
            with patch.object(self.module.shutil, "which") as which:
                result = self.module.recalculate(source, output, root)
            self.assertEqual(result["status"], "not_needed")
            which.assert_not_called()
            self.assertFalse(output.exists())

    def test_missing_libreoffice_preserves_source_and_writes_no_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.xlsx"
            output = root / "output.xlsx"
            self.workbook(source, formula=True)
            before = source.read_bytes()
            with patch.object(self.module.shutil, "which", return_value=None):
                result = self.module.recalculate(source, output, root)
            self.assertEqual(result["status"], "unavailable")
            self.assertEqual(source.read_bytes(), before)
            self.assertFalse(output.exists())

    def test_web_hyperlink_is_not_an_external_data_connection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "hyperlink.xlsx"
            self.workbook(source, formula=True, hyperlink=True)
            self.assertFalse(self.module.external_links(source))

    def test_existing_output_is_not_overwritten_without_authorization(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "输入.xlsx"
            output = root / "输出.xlsx"
            self.workbook(source, formula=True)
            output.write_bytes(b"keep-existing-output")
            result = self.module.recalculate(source, output, root)
            self.assertEqual(result["status"], "error")
            self.assertEqual(output.read_bytes(), b"keep-existing-output")

    def test_macro_enabled_workbook_is_rejected_without_conversion(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.xlsm"
            output = root / "output.xlsx"
            source.write_bytes(b"not-opened-because-extension-is-rejected-first")
            result = self.module.recalculate(source, output, root)
            self.assertEqual(result["status"], "unsupported")
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
