import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OFFICE_SCRIPTS = ROOT / "skills" / "docx" / "scripts" / "office"
sys.path.insert(0, str(OFFICE_SCRIPTS))

from validators import DOCXSchemaValidator  # noqa: E402


WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"


class DocxValidatorTests(unittest.TestCase):
    def _write_minimal_package(self, root: Path) -> Path:
        (root / "_rels").mkdir(parents=True)
        (root / "word").mkdir()
        (root / "_rels" / ".rels").write_text(
            (
                '<?xml version="1.0" encoding="UTF-8"?>'
                f'<Relationships xmlns="{REL_NS}">'
                '<Relationship Id="rId1" '
                'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
                'Target="word/document.xml"/>'
                "</Relationships>"
            ),
            encoding="utf-8",
        )
        document = root / "word" / "document.xml"
        document.write_text(
            (
                '<?xml version="1.0" encoding="UTF-8"?>'
                f'<w:document xmlns:w="{WORD_NS}"><w:body>'
                "<w:p><w:r><w:t>中文内容</w:t></w:r></w:p>"
                "<w:sectPr/></w:body></w:document>"
            ),
            encoding="utf-8",
        )
        return document

    def test_xsd_reader_uses_xml_encoding_not_windows_code_page(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            document = self._write_minimal_package(root)
            validator = DOCXSchemaValidator(root)

            valid, errors = validator._validate_single_file_xsd(document, root)

            self.assertTrue(valid, errors)
            self.assertFalse(errors)

    def test_empty_optional_word_parts_do_not_fail_relationship_validation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write_minimal_package(root)
            (root / "word" / "comments.xml").write_text(
                f'<w:comments xmlns:w="{WORD_NS}"/>',
                encoding="utf-8",
            )
            (root / "word" / "footnotes.xml").write_text(
                (
                    f'<w:footnotes xmlns:w="{WORD_NS}">'
                    '<w:footnote w:id="-1"><w:p/></w:footnote>'
                    '<w:footnote w:id="0"><w:p/></w:footnote>'
                    "</w:footnotes>"
                ),
                encoding="utf-8",
            )

            validator = DOCXSchemaValidator(root)

            self.assertTrue(validator.validate_file_references())

    def test_populated_or_unknown_unreferenced_parts_still_fail(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write_minimal_package(root)
            (root / "word" / "comments.xml").write_text(
                (
                    f'<w:comments xmlns:w="{WORD_NS}">'
                    '<w:comment w:id="0"><w:p><w:r><w:t>review</w:t></w:r></w:p></w:comment>'
                    "</w:comments>"
                ),
                encoding="utf-8",
            )
            (root / "word" / "orphan.xml").write_text(
                "<orphan/>",
                encoding="utf-8",
            )

            validator = DOCXSchemaValidator(root)
            output = io.StringIO()

            with contextlib.redirect_stdout(output):
                valid = validator.validate_file_references()

            self.assertFalse(valid)
            self.assertIn("comments.xml", output.getvalue())
            self.assertIn("orphan.xml", output.getvalue())


if __name__ == "__main__":
    unittest.main()
