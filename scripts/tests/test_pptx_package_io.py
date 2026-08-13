from __future__ import annotations

import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import lxml.etree

ROOT = Path(__file__).resolve().parents[2]
OFFICE = ROOT / "skills" / "pptx" / "scripts" / "office"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from skills.pptx.scripts.office import pack as pptx_pack
from skills.pptx.scripts.office import package_io
from skills.pptx.scripts.office.validators import PPTXSchemaValidator
from skills.pptx.scripts.office.validators import base as pptx_validator_base


class PptxPackageIoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.package_io = package_io
        cls.pack_module = pptx_pack
        cls.validator_module = pptx_validator_base

    def test_unpack_rejects_path_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "unsafe.pptx"
            target = root / "unpacked"
            with zipfile.ZipFile(source, "w") as package:
                package.writestr("../escape.txt", "unsafe")
            with self.assertRaisesRegex(ValueError, "unsafe package member"):
                self.package_io.safe_extract_pptx(source, target)
            self.assertFalse((root / "escape.txt").exists())
            self.assertFalse(target.exists())

    def test_pack_rejects_non_pptx_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "unpacked"
            source.mkdir()
            with self.assertRaisesRegex(ValueError, r"\.pptx"):
                self.package_io.pack_pptx(source, root / "output.docx")

    def test_pack_preserves_existing_output_without_replace(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "unpacked"
            source.mkdir()
            (source / "part.xml").write_text("<part/>", encoding="utf-8")
            output = root / "output.pptx"
            output.write_bytes(b"keep")
            with self.assertRaises(FileExistsError):
                self.package_io.pack_pptx(source, output)
            self.assertEqual(output.read_bytes(), b"keep")

    def test_verified_pack_preserves_existing_output_when_candidate_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "unpacked"
            source.mkdir()
            (source / "part.xml").write_text("<part/>", encoding="utf-8")
            output = root / "output.pptx"
            output.write_bytes(b"keep")
            with patch.object(self.pack_module, "validate", return_value=False):
                with self.assertRaisesRegex(ValueError, "candidate failed validation"):
                    self.pack_module.pack_verified(source, output, replace=True)
            self.assertEqual(output.read_bytes(), b"keep")
            self.assertEqual(list(root.glob("*.candidate.pptx")), [])

    def test_pack_rejects_output_inside_input_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "unpacked"
            source.mkdir()
            with self.assertRaisesRegex(ValueError, "outside"):
                self.package_io.pack_pptx(source, source / "output.pptx")

    def test_pack_and_unpack_preserve_package_members(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "unpacked"
            (source / "ppt" / "slides").mkdir(parents=True)
            (source / "[Content_Types].xml").write_text("<Types/>", encoding="utf-8")
            (source / "ppt" / "slides" / "slide1.xml").write_text(
                "<p:sld xmlns:p='urn:p'/>", encoding="utf-8"
            )
            output = root / "output.pptx"
            restored = root / "restored"
            self.package_io.pack_pptx(source, output)
            self.package_io.safe_extract_pptx(output, restored)
            self.assertEqual(
                (restored / "ppt" / "slides" / "slide1.xml").read_text(encoding="utf-8"),
                "<p:sld xmlns:p='urn:p'/>",
            )

    def test_chart_extension_content_is_preserved_in_validation_copy(self) -> None:
        xml = lxml.etree.fromstring(
            b"""<c:extLst
              xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart"
              xmlns:c16="http://schemas.microsoft.com/office/drawing/2014/chart">
              <c:ext uri="{id}"><c16:uniqueId val="{value}"/></c:ext>
            </c:extLst>"""
        )
        validator = self.validator_module.BaseSchemaValidator.__new__(
            self.validator_module.BaseSchemaValidator
        )
        validator._remove_ignorable_elements(xml)
        children = xml.xpath("./c:ext/c16:uniqueId", namespaces={
            "c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
            "c16": "http://schemas.microsoft.com/office/drawing/2014/chart",
        })
        self.assertEqual(len(children), 1)

    def test_original_chart_error_is_allowed_but_added_copy_is_rejected(self) -> None:
        original = ROOT / "skills" / "sysu-ppt" / "assets" / "template.pptx"
        with tempfile.TemporaryDirectory() as directory:
            unpacked = Path(directory) / "unpacked"
            self.package_io.safe_extract_pptx(original, unpacked)
            chart = unpacked / "ppt" / "charts" / "chart5.xml"
            validator = PPTXSchemaValidator(unpacked, original)

            valid, new_errors, original_errors = validator.validate_file_against_xsd(chart)
            self.assertTrue(valid)
            self.assertFalse(new_errors)
            self.assertTrue(original_errors)

            tree = lxml.etree.parse(chart)
            empty_extensions = tree.xpath(
                ".//c:ext[not(*)]",
                namespaces={
                    "c": "http://schemas.openxmlformats.org/drawingml/2006/chart"
                },
            )
            self.assertTrue(empty_extensions)
            empty_extensions[0].addnext(
                lxml.etree.fromstring(lxml.etree.tostring(empty_extensions[0]))
            )
            tree.write(chart, encoding="UTF-8", xml_declaration=True)

            valid, new_errors, original_errors = validator.validate_file_against_xsd(chart)
            self.assertFalse(valid)
            self.assertEqual(sum(new_errors.values()), 1)
            self.assertTrue(original_errors)


if __name__ == "__main__":
    unittest.main()
